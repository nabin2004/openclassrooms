# Amoeba

Reusable primitives for LLM-backed agents (LiteLLM integration, response parsing, optional `Agent` + memory hooks, tools, tick loop scaffolding).

## Documentation

- **[docs/GUIDE.md](docs/GUIDE.md)** — usage, best practices, gotchas, experimental areas  
- **[docs/AGENTIC.md](docs/AGENTIC.md)** — compact API reference  
- **[docs/README.md](docs/README.md)** — index of doc files  

## Development

This package is part of the OpenClassrooms uv workspace. From the repo root: `uv sync --all-packages`, then import `amoeba` from dependent packages with `[tool.uv.sources] amoeba = { workspace = true }`.
