"""Process-level setup helpers for agent runtimes (env files, etc.)."""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv

_loaded = False


def load_agent_env(*, dotenv_paths: list[str | Path] | None = None) -> None:
    """
    Load ``.env`` into the process once. Safe to call from multiple agents.

    Idempotent: subsequent calls are no-ops.
    """
    global _loaded
    if _loaded:
        return
    if dotenv_paths is None:
        load_dotenv()
    else:
        # Load in order; later files may override earlier values.
        for i, p in enumerate(dotenv_paths):
            path = Path(p)
            if i == 0:
                load_dotenv(path)
            else:
                load_dotenv(path, override=True)
    _loaded = True
