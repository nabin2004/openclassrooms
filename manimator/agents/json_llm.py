"""LiteLLM kwargs helpers for agents that require JSON in `message.content`."""

from __future__ import annotations

import os


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def response_format_json_object(*, disable_env_var: str) -> dict:
    """
    OpenAI-compatible JSON object mode for `think_and_parse` flows.

    Set ``disable_env_var`` to a truthy env name (e.g. ``INTENT_DISABLE_JSON_MODE``)
    to skip ``response_format`` when the provider rejects it.
    """
    if _truthy_env(disable_env_var):
        return {}
    return {"response_format": {"type": "json_object"}}
