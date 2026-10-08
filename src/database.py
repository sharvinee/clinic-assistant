from pathlib import Path
import sqlite3
from sqlalchemy import create_engine, text

DATABASE_PATH = Path(__file__).resolve().parents[1] / "database" / "clinic.db"

if not DATABASE_PATH.exists():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executescript(
            (DATABASE_PATH.parent / "schema.sql").read_text()
        )

engine = create_engine(f"sqlite:///{DATABASE_PATH}")

# `schema.sql` is only run when the database is first created. Apply these non-destructive indexes here too so an existing local database receives the same patient-identity safeguards.
with engine.begin() as connection:
    connection.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_patients_phone
        ON patients(phone)
        WHERE phone IS NOT NULL
    """))
    connection.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_patients_email
        ON patients(email)
        WHERE email IS NOT NULL
    """))
