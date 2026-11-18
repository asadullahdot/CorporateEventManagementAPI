# AI Usage Documentation

## Tools & models
| Tool | Model | Used for |
|---|---|---|
| Claude Code (VS Code extension) | Claude Sonnet 5.5 (`claude-sonnet-5-5`) | Reading the brief and rubric, planning, writing the code, code review, fixes, running tests, git operations, documentation |
| Docker + `postgres:16` image | n/a | Throwaway PostgreSQL instance for testing (not AI) |

## What AI was used for
- Reading the assignment brief (PDF) and grading rubric (XLSX) and summarising the requirements.
- Planning the scaffold (plan mode) and generating `db.py`, `models.py`, `schemas.py`, `services.py`, `main.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md` and this file.
- Running a code review (`/code-review`) and fixing the findings that relate to the assignment requirements.
- Running a scripted end-to-end test against PostgreSQL, and creating `.env` and starting the server.
- Git operations: creating feature branches, merging, pushing to GitHub, and rewriting commit messages to remove a co-author trailer.

The scope was limited to the **mandatory** features only. No bonus features (JWT, async, pagination, filtering, pytest) and no frontend were built.

## Prompts
Prompts sent to the AI, in order:

1. `Explore the requirements in 'requirements' folder`
2. `Yes, scaffold it with only Mandatory features`
3. `/code-review` (built-in review command), followed by: `review all the findings and fix them which matches with the requirements`
4. `First commit it on locally Git then The github repository is: https://github.com/asadullahdot/CorporateEventManagementAPI`
5. `Help me test it with postgres`
6. `Create the .env file and start the server`
7. `I have manually tested all the endpoints from swagger page`
8. `Remove Co-Authored-By from all commits and force push`
9. `Fill in AI_USAGE.md`

## Outcome of the AI-assisted steps
- **Review (prompt 3):** 9 findings were reported. 6 were fixed: row locking on capacity checks (race conditions), correct 404 vs 409 on concurrent delete, a standalone `EventResponse` schema, a case-insensitive unique index on registration emails, and `passive_deletes` for cascading deletes. 3 were deliberately skipped as outside the brief: the default `DATABASE_URL`, extra validation such as past dates and description length, and database migrations.
- **Testing (prompt 5):** a scripted run of 26 checks against PostgreSQL 16 passed. It covered every endpoint, the 404, 409 and 422 cases, and a concurrency test (6 simultaneous registrations for 1 seat gave exactly 1 success).
- **Manual testing (prompt 7):** I tested all endpoints myself through Swagger UI. Screenshots are in `docs/screenshots/`.

## Chat history
The complete Claude Code conversation is exported at [docs/chat-history/2026-11-18-205308-explore-the-requirements-in-requirements-folder.txt](docs/chat-history/2026-11-18-205308-explore-the-requirements-in-requirements-folder.txt).

## Configuration
- Claude Code in the VS Code extension, with plan mode used before the scaffold was written.
- Database: PostgreSQL 16 in Docker, mapped to host port 5433, database `event_management`. Connection string is set through `DATABASE_URL` in a local, untracked `.env` file (template in `.env.example`).
- Python 3.14 virtual environment (`.venv`); dependencies pinned loosely in `requirements.txt`.
- Git: `main` as the stable branch, feature branches `feature/db-setup`, `feature/event-crud`, `feature/docs-readme` and `fix/review-findings`, merged into `main` with `--no-ff`.

## Understanding the code
I reviewed every file. This is how the project works, file by file.

**`db.py`: connection.** Reads `DATABASE_URL` from `.env` and builds the SQLAlchemy engine and a `SessionLocal` factory. `get_db()` is a FastAPI dependency that opens one session per request and always closes it in a `finally` block, so connections are never leaked.

**`models.py`: tables.** `Event` has id, title, description, date, location and max_capacity. `Registration` has id, event_id, attendee name and email, and created_at. The foreign key uses `ondelete="CASCADE"` together with `passive_deletes=True`, so deleting an event lets PostgreSQL remove its registrations in one statement. A unique index on `(event_id, lower(attendee_email))` makes "one registration per employee per event" a database guarantee, not only an application check.

**`schemas.py`: validation.** Separate schemas for create, update and response:
- `EventCreate` / `EventUpdate`: title and location must be non-blank (`min_length` plus a validator that strips whitespace), `max_capacity` must be `> 0` (`Field(gt=0)`), `date` is a `datetime.date` so invalid dates fail, and required fields have no default. FastAPI turns any failure into a 422.
- `RegistrationCreate`: name must be non-blank and the email must be a valid `EmailStr`.
- `EventResponse` is deliberately *not* built on the input schema, so a stored row that breaks an input rule can never turn a GET into a 500.

**`services.py`: business logic.** All rules live here, and routes never touch the database directly. It raises two domain exceptions, `NotFoundError` and `ConflictError`, which know nothing about HTTP.
- `get_event` returns the event or raises `NotFoundError`. With `lock=True` it uses `SELECT ... FOR UPDATE`.
- `create_registration` runs the rules in order: (1) event must exist, otherwise 404; (2) the same email, compared case-insensitively, must not already be registered, otherwise 409; (3) the registration count must be below `max_capacity`, otherwise 409; then it inserts. The event row is locked first, so two simultaneous requests for the last seat are serialised and only one succeeds. I verified this with 6 parallel requests for 1 seat: exactly 1 got 201 and 5 got 409.
- If the insert still fails with an `IntegrityError` (the unique index acting as a backstop), the code rolls back and re-checks the event. It returns 404 if the event was deleted in the meantime and 409 for a real duplicate.
- `update_event` refuses (409) to lower capacity below the number of existing registrations.
- `delete_event` and `delete_registration` raise 404 when the target is missing.

**`main.py`: routes.** Each route is a thin wrapper that receives the validated schema and a session, calls one service function and returns the result. Two exception handlers translate `NotFoundError` to 404 and `ConflictError` to 409 with a `{"detail": ...}` body, so error messages are consistent everywhere. Create endpoints return 201 and delete endpoints return 204 with no body. Routes declare `response_model`, tags, summaries and documented error responses, which is what makes `/docs` complete. A `lifespan` hook calls `create_all` at startup to create the tables.

**Key decisions**
- Business logic is separated from routes, so the rules can be read and changed in one place.
- Duplicate and capacity rules are checked in the application *and* backed by the database (unique index, row lock), because checks in code alone are not safe under concurrent requests.
- Domain exceptions plus central handlers keep status codes consistent and keep HTTP concerns out of `services.py`.
- Only the mandatory features were built. Pagination, filtering, JWT, async and pytest were left out on purpose, as were migrations; `create_all` will not alter tables that already exist.
