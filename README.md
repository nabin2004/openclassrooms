# OpenClassrooms Monorepo

This repository is a uv-managed Python workspace with multiple projects:

- `manimator`: agentic animation pipeline
- `autolecture`: lecture generation experiments
- `webapp`: FastHTML web application
- `amoeba`: agent framework package

## Requirements

- `uv` 0.10+
- Python `3.14` (from `.python-version`)

## Quick Start

```bash
# 1) Install and select Python 3.14 for uv
uv python install 3.14

# 2) Sync all workspace packages into .venv
uv sync --all-packages

# 3) Run repository tests/workflows
make test-all
```

## Developer guide (how to run things)

Work from the **repository root** (`OpenClassrooms/`, where this `README.md` lives).

### Environment

```bash
uv sync --all-packages          # recommended: all workspace members in .venv
# optional TTS for manimator:
uv sync --package manimator --extra tts
```

### Run Manimator (correct patterns)

The `manimator` package includes a top-level folder named `logging/`. If Python puts the `manimator` project directory on `sys.path` **before** the stdlib is consulted, `import logging` can wrongly load `manimator/logging/` and crash. **Always fix the path or use `-m`.**

| Do this | Why |
|--------|-----|
| `uv run --package manimator python -m manimator.main` | **Preferred** from repo root |
| `uv run python -m manimator.main` | OK after `uv sync --all-packages` |
| `uv run python manimator/main.py` | OK **after** `main.py` path fix (still prefer `-m`) |
| `cd manimator && uv run python main.py` | **Avoid** — same `logging` shadow risk unless path is fixed |

### Editable installs (`pip`)

- **Workspace metapackage only** (root deps, not manimator code):  
  `uv pip install -e .`
- **Manimator package** (so `import manimator` works from any cwd):  
  `uv pip install -e ./manimator`

Do not put `packages = [...]` under `[project]` in `pyproject.toml` — that is invalid for PEP 621. Package discovery belongs under `[tool.setuptools]` (root) or `manimator/pyproject.toml`.

### Builds

- `uv build` at the root produces **only** the `openclassrooms` metapackage wheel/sdist (not manimator).
- To ship manimator, build from `manimator/` (or use the workspace lock + sync).

More detail: [manimator/README.md](manimator/README.md), [DEVELOPMENT.md](DEVELOPMENT.md).

## Daily Workflow (uv-first)

```bash
# Sync dependencies after pulling
make sync

# Run full pipeline
make test-pipeline

# Run one test script directly
uv run python test_agents.py --agent planner

# Fast pass/fail check
make quick-test
```

## Dependency Management

Use uv at the workspace root:

```bash
# Add dependency to root project
uv add <package>

# Add dependency to a specific workspace package
uv add --package manimator <package>
uv add --package autolecture <package>
uv add --package webapp <package>
uv add --package amoeba <package>

# Remove dependency
uv remove --package manimator <package>

# Re-lock dependencies
make lock

# Recreate env exactly from lockfile
make sync-frozen
```

## Useful Entry Points

```bash
# Root hello script
uv run python main.py

# Manimator pipeline (run from this directory; see manimator/README.md)
uv run --package manimator python -m manimator.main

# Interactive agent test harness
uv run python test_agents.py --agent intent

# Video config helper
uv run python set_video_config.py conservative
```

**Manimator** (sync, TTS extra, env vars, pytest): [manimator/README.md](manimator/README.md).

## Developer Docs

- `DEVELOPMENT.md`: uv workflow and team conventions
- `AGENT_TESTING.md`: agent-level testing workflow
- `VIDEO_CONFIG_GUIDE.md`: configuration profiles for scene/decomposition limits
- `AGENTS.md`: coding-agent instructions for this repository
