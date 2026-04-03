# Development Guide

## Goal

Use uv as the single project manager for dependency resolution, virtual environment management, and command execution across this workspace.

## One-Time Setup

```bash
# Install Python used by the workspace
uv python install 3.14

# Sync all workspace packages
uv sync --all-packages
```

## Daily Commands

```bash
# Refresh environment after dependency changes
make sync

# Run all agent tests
make test-all

# Run the full manimator pipeline
make test-pipeline

# Same pipeline, explicit uv package (from workspace root)
uv run --package manimator python -m manimator.main

# Run the interactive tester
uv run python test_agents.py --agent intent
```

Manimator-specific setup (TTS optional extra, `.env`, pytest): [manimator/README.md](manimator/README.md).

## Workspace Packages

This repository is a uv workspace with these members:

- manimator
- autolecture
- webapp
- amoeba

Use package-scoped dependency commands when needed:

```bash
uv add --package manimator <package>
uv add --package autolecture <package>
uv add --package webapp <package>
uv add --package amoeba <package>
```

## Lockfile Workflow

```bash
# Update lockfile after dependency changes
make lock

# Sync exactly from the lockfile (CI-like behavior)
make sync-frozen
```

## Command Conventions

- Always prefer `uv run python ...` over direct `python ...`.
- Run commands from the workspace root unless a package explicitly requires another working directory.
- Keep docs in sync whenever command conventions change.

## Related Documentation

- [manimator/README.md](manimator/README.md) — run Manimator with uv
- AGENT_TESTING.md
- VIDEO_CONFIG_GUIDE.md
- AGENTS.md
