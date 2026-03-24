# Project Rules

## Git Workflow
- Never merge code directly to master. Always create a feature branch and open a PR.
- Pull the latest master before starting new work.

## Testing
- Always run `poetry run pytest -v` before creating a PR to ensure tests pass.
- When writing new code, always create tests alongside it. No code without tests.

## Documentation
- When writing a new feature, create a plan document in `/docs` for review before implementation.

## Tech Stack
- Python 3.11, FastAPI, Poetry
- Project layout: `src/app/`
- Tests in `tests/` using pytest + httpx
