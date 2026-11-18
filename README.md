# Corporate Event Management API

Backend API for Acme Corp's internal event system: manage events and register employees.
Built with FastAPI, SQLAlchemy 2.0 and PostgreSQL.

## Project structure

| File | Responsibility |
|---|---|
| `db.py` | Engine, session factory, `get_db` dependency |
| `models.py` | SQLAlchemy models (`Event`, `Registration`) |
| `schemas.py` | Pydantic request/response schemas and validation |
| `services.py` | Business logic and database operations |
| `main.py` | Thin API routes, error handlers, app entry point |

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## PostgreSQL configuration

1. Install PostgreSQL and create a database:
   ```sql
   CREATE DATABASE event_management;
   ```
2. Copy `.env.example` to `.env` and set your credentials:
   ```
   DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/event_management
   ```
Tables are created automatically on first startup.

## Run

```bash
uvicorn main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Endpoints

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/events` | 201 | 422 |
| GET | `/events` | 200 | |
| GET | `/events/{id}` | 200 | 404 |
| PUT | `/events/{id}` | 200 | 404, 409 (capacity below current registrations), 422 |
| DELETE | `/events/{id}` | 204 | 404 |
| POST | `/events/{id}/registrations` | 201 | 404, 409 (duplicate or full), 422 |
| GET | `/events/{id}/registrations` | 200 | 404 |
| DELETE | `/registrations/{id}` | 204 | 404 |

## Validation rules

Title and location must be non-blank, date must be a valid `YYYY-MM-DD`, `max_capacity` must be > 0,
and registrations need a name and valid email.

## Submission extras

Swagger screenshots go in `docs/screenshots/`; AI usage is documented in [AI_USAGE.md](AI_USAGE.md).
