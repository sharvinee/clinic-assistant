from langchain_core.tools import tool
from sqlalchemy import text
from src.approval import request_approval
from src.database import engine

@tool
def read_sql(query: str) -> str:
    """Run a read-only SELECT query against the Clinic database."""
    try:
        if not query.lstrip().upper().startswith("SELECT"):
            return "Error: only SELECT queries are permitted."
        with engine.connect() as connection:
            return str(connection.execute(text(query)).fetchall())
    except Exception as e:
        return f"Error: {e}"

@tool
def create_appointment(patient_id: int, slot_id: int) -> str:
    """
    Book an appointment for an identified patient in a specific available slot.

    Call only after:
    - confirming the patient ID with read_sql,
    - confirming the slot is available with read_sql, and
    - receiving the patient's explicit approval.

    This tool atomically marks the slot as booked and creates a confirmed
    appointment. Do not provide SQL; pass only integer IDs.
    """
    approval = request_approval(
        "this appointment booking",
        {"patient_id": patient_id, "slot_id": slot_id},
    )
    if not approval.approved:
        return "Booking was not approved."

    try:
        with engine.begin() as connection:  # commits on success & rolls back on failure
            reserve = connection.execute(
                text("""
                    UPDATE appointment_slots
                    SET status = 'booked'
                    WHERE slot_id = :slot_id AND status = 'available'
                """),
                {"slot_id": slot_id},
            )

            if reserve.rowcount != 1:
                return "Booking failed: that slot is no longer available."

            connection.execute(
                text("""
                    INSERT INTO appointments (patient_id, slot_id, status)
                    VALUES (:patient_id, :slot_id, 'confirmed')
                """),
                {"patient_id": patient_id, "slot_id": slot_id},
            )

        return "Appointment created successfully."
    except Exception as e:
        return f"Booking failed: {e}"

@tool
def verify_patient_identity(
    first_name: str,
    last_name: str,
    phone: str | None = None,
    email: str | None = None,
) -> str:
    """
    Verify a patient who claims an existing account.

    Require first name, last name, and at least one contact identifier (phone
    or email). Returns only a verified patient ID or a generic no-match result;
    it never reveals candidate patient records or contact details.
    """
    first_name = first_name.strip()
    last_name = last_name.strip()
    phone = phone.strip() if phone else None
    email = email.strip() if email else None

    if not first_name or not last_name:
        return "Identity verification failed: first name and last name are required."
    if not phone and not email:
        return "Identity verification failed: provide a phone number or email address."

    try:
        with engine.connect() as connection:
            matches = connection.execute(
                text("""
                    SELECT id
                    FROM patients
                    WHERE lower(first_name) = lower(:first_name)
                      AND lower(last_name) = lower(:last_name)
                      AND (:phone IS NULL OR phone = :phone)
                      AND (:email IS NULL OR lower(email) = lower(:email))
                    ORDER BY id
                """),
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "email": email,
                },
            ).mappings().all()

        if len(matches) == 1:
            return f"Patient identified successfully. patient_id={matches[0]['id']}"
        if not matches:
            return "No matching patient record found."
        return "Identity verification failed. Please contact the clinic."
    except Exception as e:
        return f"Identity verification failed: {e}"


@tool
def create_patient(
    first_name: str,
    last_name: str,
    phone: str | None = None,
    email: str | None = None,
) -> str:
    """
    Create a new patient record after explicit approval.

    Pass a first name, last name, and at least one contact identifier (phone or
    email). Do not provide SQL. This tool refuses to create an account if the
    phone number or email is already associated with an existing patient.
    """
    first_name = first_name.strip()
    last_name = last_name.strip()
    phone = phone.strip() if phone else None
    email = email.strip() if email else None

    if not first_name or not last_name:
        return "Patient creation failed: first name and last name are required."
    if not phone and not email:
        return "Patient creation failed: provide a phone number or email address."

    approval = request_approval(
        "creation of this patient record",
        {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "email": email,
        },
    )
    if not approval.approved:
        return "Patient creation was not approved."

    try:
        with engine.begin() as connection:
            existing = connection.execute(
                text("""
                    SELECT id
                    FROM patients
                    WHERE (:phone IS NOT NULL AND phone = :phone)
                       OR (:email IS NOT NULL AND lower(email) = lower(:email))
                    LIMIT 1
                """),
                {"phone": phone, "email": email},
            ).mappings().first()

            if existing:
                return (
                    "Patient creation not completed: an account already uses "
                    "the supplied phone number or email address."
                )

            result = connection.execute(
                text("""
                    INSERT INTO patients (first_name, last_name, phone, email)
                    VALUES (:first_name, :last_name, :phone, :email)
                """),
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "email": email,
                },
            )
            patient_id = result.lastrowid

        return f"Patient created successfully. patient_id={patient_id}"
    except Exception as e:
        return f"Patient creation failed: {e}"

@tool
def reschedule_appointment(
    appointment_id: int,
    patient_id: int,
    new_slot_id: int,
) -> str:
    """Atomically move a patient's confirmed appointment to an available new slot."""
    approval = request_approval(
        "this appointment rescheduling",
        {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "new_slot_id": new_slot_id,
        },
    )
    if not approval.approved:
        return "Rescheduling was not approved."

    try:
        with engine.begin() as connection:
            appointment = connection.execute(
                text("""
                    SELECT slot_id
                    FROM appointments
                    WHERE appointment_id = :appointment_id
                      AND patient_id = :patient_id
                      AND status = 'confirmed'
                """),
                {
                    "appointment_id": appointment_id,
                    "patient_id": patient_id,
                },
            ).mappings().one_or_none()

            if appointment is None:
                return "Reschedule failed: no matching confirmed appointment was found."

            old_slot_id = appointment["slot_id"]

            # Reserve the new slot only if it is still available.
            reserve_new_slot = connection.execute(
                text("""
                    UPDATE appointment_slots
                    SET status = 'booked'
                    WHERE slot_id = :new_slot_id
                      AND status = 'available'
                """),
                {"new_slot_id": new_slot_id},
            )

            if reserve_new_slot.rowcount != 1:
                return "Reschedule failed: the requested new slot is unavailable."

            # Move the confirmed appointment.
            move_appointment = connection.execute(
                text("""
                    UPDATE appointments
                    SET slot_id = :new_slot_id
                    WHERE appointment_id = :appointment_id
                      AND patient_id = :patient_id
                      AND status = 'confirmed'
                """),
                {
                    "new_slot_id": new_slot_id,
                    "appointment_id": appointment_id,
                    "patient_id": patient_id,
                },
            )

            if move_appointment.rowcount != 1:
                raise ValueError("Appointment could not be moved.")

            # Release the previous slot.
            connection.execute(
                text("""
                    UPDATE appointment_slots
                    SET status = 'available'
                    WHERE slot_id = :old_slot_id
                """),
                {"old_slot_id": old_slot_id},
            )

        return "Appointment rescheduled successfully."
    except Exception as e:
        return f"Reschedule failed: {e}"


@tool
def cancel_appointment(appointment_id: int, patient_id: int) -> str:
    """Atomically cancel a patient's confirmed appointment and release its slot."""
    approval = request_approval(
        "this appointment cancellation",
        {"appointment_id": appointment_id, "patient_id": patient_id},
    )
    if not approval.approved:
        return "Cancellation was not approved."

    try:
        with engine.begin() as connection:
            appointment = connection.execute(
                text("""
                    SELECT slot_id
                    FROM appointments
                    WHERE appointment_id = :appointment_id
                      AND patient_id = :patient_id
                      AND status = 'confirmed'
                """),
                {
                    "appointment_id": appointment_id,
                    "patient_id": patient_id,
                },
            ).mappings().one_or_none()

            if appointment is None:
                return "Cancellation failed: no matching confirmed appointment was found."

            old_slot_id = appointment["slot_id"]

            cancel = connection.execute(
                text("""
                    UPDATE appointments
                    SET status = 'cancelled'
                    WHERE appointment_id = :appointment_id
                      AND patient_id = :patient_id
                      AND status = 'confirmed'
                """),
                {
                    "appointment_id": appointment_id,
                    "patient_id": patient_id,
                },
            )

            if cancel.rowcount != 1:
                raise ValueError("Appointment could not be cancelled.")

            connection.execute(
                text("""
                    UPDATE appointment_slots
                    SET status = 'available'
                    WHERE slot_id = :old_slot_id
                """),
                {"old_slot_id": old_slot_id},
            )

        return "Appointment cancelled successfully."
    except Exception as e:
        return f"Cancellation failed: {e}"
