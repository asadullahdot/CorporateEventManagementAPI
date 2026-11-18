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
TODO (author to complete): confirm in your own words that you reviewed each file and can explain it, for example how `services.py` enforces the duplicate and capacity rules, why the event row is locked, and how `main.py` maps `NotFoundError` and `ConflictError` to 404 and 409.
