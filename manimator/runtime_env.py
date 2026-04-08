"""Backward-compatible env loader for Manimator.

Prefer calling `amoeba.runtime.load_agent_env(...)` directly.
"""

from pathlib import Path

from amoeba.runtime import load_agent_env

_done = False


def ensure_manimator_env() -> None:
    """
    Load, in order:
      1) `<repo>/.env`
      2) `<repo>/manimator/.env` (overrides — common place for local API keys)

    Previously only the repo root was loaded from main.py, so keys kept only in
    manimator/.env were invisible and LiteLLM could return empty completions.
    """
    global _done
    if _done:
        return
    pkg_root = Path(__file__).resolve().parent
    repo_root = pkg_root.parent
    load_agent_env(dotenv_paths=[repo_root / ".env", pkg_root / ".env"])
    _done = True
