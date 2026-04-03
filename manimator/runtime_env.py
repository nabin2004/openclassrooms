"""Load environment variables from the repo root and this package directory."""

from pathlib import Path

from dotenv import load_dotenv

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
    load_dotenv(repo_root / ".env")
    load_dotenv(pkg_root / ".env", override=True)
    _done = True
