"""Process-level setup helpers for agent runtimes (env files, etc.)."""

from dotenv import load_dotenv

_loaded = False


def load_agent_env() -> None:
    """
    Load ``.env`` into the process once. Safe to call from multiple agents.

    Idempotent: subsequent calls are no-ops.
    """
    global _loaded
    if _loaded:
        return
    load_dotenv()
    _loaded = True
