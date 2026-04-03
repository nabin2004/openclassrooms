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
