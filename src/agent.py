from deepagents import create_deep_agent
from src.tools import (
    read_sql,
    verify_patient_identity,
    create_patient,
    create_appointment,
    reschedule_appointment,
    cancel_appointment,
)
from src.model import model
from src.prompts import SYSTEM_PROMPT

agent = create_deep_agent(
    model=model,
    name="AI_clinic_assistant",
    system_prompt=SYSTEM_PROMPT,
    tools=[
    read_sql,
    verify_patient_identity,
    create_patient,
    create_appointment,
    reschedule_appointment,
    cancel_appointment,
    ],
)
