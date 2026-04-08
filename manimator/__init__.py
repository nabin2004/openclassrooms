"""Manimator: agentic Manim animation pipeline."""

from pathlib import Path

from amoeba.runtime import load_agent_env

_pkg_root = Path(__file__).resolve().parent
_repo_root = _pkg_root.parent

# Load repo .env then allow manimator/.env to override.
load_agent_env(dotenv_paths=[_repo_root / ".env", _pkg_root / ".env"])
