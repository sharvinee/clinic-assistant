# Clinic Assistant

A Deep Agents clinic scheduling assistant, built with LangChain and running on
the LangGraph runtime. It helps patients register, view available appointment
slots, review their own appointments, and book, reschedule, or cancel visits.

The application uses a local SQLite database seeded with fictional patient and
appointment data. It is intended as a demonstration project, not a production
clinical system.

## Features

- Patient verification using name plus a phone number or email address
- Privacy-preserving identity lookup that does not reveal candidate records
- Appointment availability lookup
- Atomic create, reschedule, and cancellation operations
- Human approval interrupts before any clinic-data change
- A LangGraph graph that can be run with LangGraph Studio

## Requirements

- Python 3.11–3.14
- An OpenAI API key
- `uv` (recommended for dependency management)

## Setup

1. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

2. Add your credentials to `.env`:

   ```dotenv
   OPENAI_API_KEY=your_openai_api_key
   ```

   LangSmith variables are optional, but enable tracing when configured.

3. Install dependencies:

   ```bash
   uv sync --all-groups
   ```

4. Start the LangGraph development server:

   ```bash
   uv run langgraph dev
   ```

   The graph is registered as `clinic_assistant` in `langgraph.json`.

## Local data

`database/schema.sql` defines and seeds the demonstration database. The local
`database/clinic.db` file is created automatically on first use and is ignored
by Git, so local changes to appointment state are never committed.

To reset the demonstration data, delete only `database/clinic.db`; the next
run recreates it from the schema.

## Safety and privacy

- Do not commit `.env`; it contains API credentials.
- The included `.env.example` contains placeholders only.
- Appointment mutations pause for an approval response before making database
  changes.
- The assistant verifies a person before showing their appointment details.

## Evaluation data

Local evaluation fixtures live in `datasets/` and are intentionally ignored by
Git. `clinic_assistant_langsmith.json` uses LangSmith-style examples with
`inputs`, `outputs`, and `metadata` fields.

## Project layout

```text
src/agent.py         LangGraph agent definition
src/tools.py         Database and appointment tools
src/approval.py      Human-approval interrupt schema
src/database.py      SQLite initialization and SQLAlchemy engine
src/prompts.py       Assistant behavior and privacy instructions
database/schema.sql  Demonstration database schema and seed data
langgraph.json       LangGraph deployment configuration
```
