# AGENTS

## Purpose

This file defines repository-specific expectations for coding agents working in this workspace.

## Environment and Tooling

- Use uv as the default Python project manager.
- Use `uv run python ...` for Python execution.
- Use `uv sync --all-packages` to prepare environments.
- Use `uv lock` when dependencies are changed.

## Preferred Commands

- `make sync`
- `make test-all`
- `make quick-test`
- `make test-pipeline`
- Manimator run (from workspace root): `uv run --package manimator python -m manimator.main`
- Manimator pytest: `uv run --package manimator -m pytest manimator/tests/...` (use `-m pytest` so imports resolve)

## Editing Rules

- Keep changes focused; avoid unrelated formatting edits.
- Do not edit generated output directories unless explicitly requested.
- Update markdown documentation when command or workflow behavior changes.

## Dependency Changes

- Add dependencies using uv, preferably package-scoped:
  - `uv add --package manimator <package>`
  - `uv add --package autolecture <package>`
  - `uv add --package webapp <package>`
  - `uv add --package amoeba <package>`
- Re-lock after dependency changes with `make lock`.

## Validation Expectations

- Run relevant make targets before finishing substantial changes.
- If full validation is too expensive, run the most focused target and report what was not run.
