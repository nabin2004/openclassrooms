"""Thin async helpers around LiteLLM for common agent call patterns."""

from __future__ import annotations

from typing import Any

from amoeba.core.safe_acompletion import acompletion_safe
from amoeba.exceptions import LLMResponseError


async def acompletion_system_user(
    *,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    error_context: str = "Agent",
    timeout: float | None = None,
    max_total_tokens: int | None = None,
    allow_empty: bool = False,
    **kwargs: Any,
) -> str:
    """
    Single system + user turn via centralized :func:`~amoeba.core.safe_acompletion.acompletion_safe`.

    Raises :class:`~amoeba.exceptions.LLMError` subclasses on provider failures;
    empty content raises :class:`~amoeba.exceptions.LLMResponseError` with
    ``error_context`` in the message unless ``allow_empty=True``.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    params: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    _reserved = frozenset({"timeout", "max_total_tokens", "allow_empty"})
    for key, val in kwargs.items():
        if key not in _reserved:
            params[key] = val

    try:
        result = await acompletion_safe(
            timeout=timeout,
            max_total_tokens=max_total_tokens,
            require_non_empty_text=not allow_empty,
            **params,
        )
    except LLMResponseError as e:
        raise LLMResponseError(
            f"{error_context}: {e.message}",
            context={**e.context, "error_context": error_context},
            user_message=e.user_message,
        ) from e
    return result.text
