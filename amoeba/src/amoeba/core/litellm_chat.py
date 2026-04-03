"""Thin async helpers around LiteLLM for common agent call patterns."""

from __future__ import annotations

from typing import Any

import litellm

from amoeba.core.responses import completion_message_text


async def acompletion_system_user(
    *,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    error_context: str = "Agent",
    **kwargs: Any,
) -> str:
    """
    Single system + user turn via ``litellm.acompletion``, returning trimmed text.

    Raises ``RuntimeError`` if the model returns no usable string content
    (after :func:`completion_message_text`).
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
    params.update(kwargs)

    response = await litellm.acompletion(**params)
    raw = completion_message_text(response)
    if not raw:
        raise RuntimeError(
            f"{error_context} received empty model content. "
            "Check model env var, API keys, and provider status."
        )
    return raw
