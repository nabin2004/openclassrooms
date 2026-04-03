# Copilot Instructions for OpenClassrooms

## Project Manager

Use uv for all Python dependency and execution workflows.

## Run Commands

- Prefer `uv run python <script.py>`.
- Prefer existing Makefile targets for test/pipeline workflows.

## Dependencies

- Add dependencies with uv (`uv add ...`).
- Use package-scoped add/remove commands for workspace members.
- Update lockfile after dependency updates.

## Documentation

When workflow commands or setup steps change, update:

- README.md
- DEVELOPMENT.md
- AGENT_TESTING.md
- VIDEO_CONFIG_GUIDE.md
- AGENTS.md
