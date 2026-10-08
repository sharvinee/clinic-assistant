PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patients (
    id         INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    phone      TEXT,
    email      TEXT
);

CREATE TABLE IF NOT EXISTS appointment_slots (
    slot_id        INTEGER PRIMARY KEY,
    start_datetime TEXT NOT NULL,
    end_datetime   TEXT NOT NULL,
    status         TEXT NOT NULL
        CHECK (status IN ('available', 'blocked', 'booked'))
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INTEGER PRIMARY KEY,
    patient_id     INTEGER NOT NULL REFERENCES patients(id),
    slot_id        INTEGER NOT NULL REFERENCES appointment_slots(slot_id),
    status         TEXT NOT NULL
        CHECK (status IN ('confirmed', 'cancelled'))
);

-- Names are not unique: different people may share the same name. Contact
-- identifiers, when supplied, must belong to only one patient record.
CREATE UNIQUE INDEX IF NOT EXISTS uq_patients_phone
    ON patients(phone)
    WHERE phone IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_patients_email
    ON patients(email)
    WHERE email IS NOT NULL;

DELETE FROM appointments;
DELETE FROM appointment_slots;
DELETE FROM patients;

INSERT INTO patients (id, first_name, last_name, phone, email) VALUES
    (1, 'Alice',    'Johnson',   '5550101', 'alice.johnson@example.com'),
    (2, 'Benjamin', 'Lee',       '5550102', 'benjamin.lee@example.com'),
    (3, 'Carla',    'Martinez',  '5550103', 'carla.martinez@example.com'),
    (4, 'Daniel',   'Kim',       '5550104', 'daniel.kim@example.com'),
    (5, 'Elena',    'Rossi',     '5550105', 'elena.rossi@example.com'),
    (6, 'Farah',    'Ahmed',     '5550106', 'farah.ahmed@example.com'),
    (7, 'George',   'Wilson',    '5550107', 'george.wilson@example.com'),
    (8, 'Hana',     'Nakamura',  '5550108', 'hana.nakamura@example.com'),
    (9, 'Isaac',    'Brown',     '5550109', 'isaac.brown@example.com'),
    (10, 'Julia',   'Santos',    '5550110', 'julia.santos@example.com');

INSERT INTO appointment_slots
    (slot_id, start_datetime, end_datetime, status)
VALUES
    (1,  '2027-09-03 09:00:00', '2027-09-03 10:00:00', 'booked'),
    (2,  '2027-09-03 10:00:00', '2027-09-03 11:00:00', 'available'),
    (3,  '2027-09-05 09:00:00', '2027-09-05 10:00:00', 'blocked'),
    (4,  '2027-09-05 10:00:00', '2027-09-05 11:00:00', 'booked'),
    (5,  '2027-09-10 09:00:00', '2027-09-10 10:00:00', 'available'),
    (6,  '2027-09-12 11:00:00', '2027-09-12 12:00:00', 'booked'),
    (7,  '2027-10-24 09:00:00', '2027-10-24 10:00:00', 'booked'),
    (8,  '2027-10-27 09:00:00', '2027-10-27 10:00:00', 'available'),
    (9,  '2027-10-29 10:00:00', '2027-10-29 11:00:00', 'booked'),
    (10, '2027-10-31 11:00:00', '2027-10-31 12:00:00', 'blocked'),
    (11, '2027-11-05 09:00:00', '2027-11-05 10:00:00', 'available'),
    (12, '2027-11-07 10:00:00', '2027-11-07 11:00:00', 'booked'),
    (13, '2027-11-12 11:00:00', '2027-11-12 12:00:00', 'available'),
    (14, '2027-11-14 09:00:00', '2027-11-14 10:00:00', 'booked'),
    (15, '2027-11-21 10:00:00', '2027-11-21 11:00:00', 'available'),
    (16, '2027-11-28 11:00:00', '2027-11-28 12:00:00', 'booked'),
    (17, '2027-11-19 09:00:00', '2027-11-19 10:00:00', 'booked'),
    (18, '2027-11-26 10:00:00', '2027-11-26 11:00:00', 'booked');

INSERT INTO appointments
    (appointment_id, patient_id, slot_id, status)
VALUES
    (1,  1, 1,  'confirmed'),
    (2,  2, 4,  'confirmed'),
    (3,  3, 6,  'confirmed'),
    (4,  4, 7,  'confirmed'),
    (5,  5, 9,  'confirmed'),
    (6,  6, 12, 'confirmed'),
    (7,  7, 14, 'confirmed'),
    (8,  8, 16, 'confirmed'),
    (9,  3, 11, 'cancelled'),
    (10, 8, 15, 'cancelled'),
    (11, 9, 17, 'confirmed'),
    (12, 10, 18, 'confirmed');
