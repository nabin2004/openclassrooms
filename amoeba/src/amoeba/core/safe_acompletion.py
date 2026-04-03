"""Centralized LiteLLM ``acompletion`` with timeouts, errors, and metrics."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import litellm

from amoeba.core.responses import completion_message_text
from amoeba.exceptions import (
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from amoeba.observability import get_trace_id, log_llm_event


@dataclass(frozen=True)
class LLMCallResult:
    text: str
    latency_ms: float
    model: str | None
    usage: dict[str, Any]
    raw_response: Any


def _redact_llm_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in kwargs.items() if k != "messages"}
    msgs = kwargs.get("messages")
    if isinstance(msgs, list):
        out["message_count"] = len(msgs)
        out["roles"] = [
            m.get("role") for m in msgs if isinstance(m, dict)
        ]
    return out


def _usage_dict(response: Any) -> dict[str, Any]:
    u = getattr(response, "usage", None)
    if u is None:
        return {}
    if isinstance(u, dict):
        return dict(u)
    out: dict[str, Any] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        val = getattr(u, key, None)
        if val is not None:
            out[key] = val
    return out


def _total_tokens(usage: dict[str, Any]) -> int | None:
    t = usage.get("total_tokens")
    if t is not None:
        return int(t)
    p = usage.get("prompt_tokens")
    c = usage.get("completion_tokens")
    if p is not None and c is not None:
        return int(p) + int(c)
    return None


def _map_llm_exception(exc: BaseException, base_context: dict[str, Any]) -> LLMError:
    if isinstance(exc, LLMError):
        return exc
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return LLMTimeoutError(context=base_context)
    msg = str(exc).lower()
    name = type(exc).__name__.lower()
    blob = f"{name} {msg}"
    if "429" in msg or "rate limit" in msg or "ratelimit" in blob:
        return LLMRateLimitError(context={**base_context, "provider_error": str(exc)})
    if "timeout" in msg or "timed out" in msg:
        return LLMTimeoutError(
            context={**base_context, "provider_error": str(exc)},
        )
    return LLMError(
        f"LLM call failed: {exc}",
        context={**base_context, "provider_error": str(exc), "exc_type": type(exc).__name__},
    )


async def acompletion_safe(
    *,
    timeout: float | None = None,
    max_total_tokens: int | None = None,
    require_non_empty_text: bool = True,
    **litellm_kwargs: Any,
) -> LLMCallResult:
    """
    Run ``litellm.acompletion`` with uniform errors, timing, and optional guards.

    Raises subclasses of :class:`~amoeba.exceptions.LLMError` on failure.
    """
    trace_id = get_trace_id()
    redacted = _redact_llm_kwargs(litellm_kwargs)
    if trace_id is not None:
        redacted["trace_id"] = trace_id
    log_llm_event(
        "llm.request",
        model=litellm_kwargs.get("model"),
        **{k: v for k, v in redacted.items() if k != "model"},
    )

    start = time.perf_counter()
    try:
        coro = litellm.acompletion(**litellm_kwargs)
        if timeout is not None:
            response = await asyncio.wait_for(coro, timeout=timeout)
        else:
            response = await coro
    except (asyncio.TimeoutError, TimeoutError) as e:
        latency_ms = (time.perf_counter() - start) * 1000
        raise LLMTimeoutError(
            context={
                **redacted,
                "latency_ms": latency_ms,
                "timeout_s": timeout,
            },
        ) from e
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        err = _map_llm_exception(
            e,
            {**redacted, "latency_ms": latency_ms},
        )
        raise err from e

    latency_ms = (time.perf_counter() - start) * 1000
    usage = _usage_dict(response)

    if max_total_tokens is not None:
        total = _total_tokens(usage)
        if total is not None and total > max_total_tokens:
            raise LLMError(
                f"Response exceeded token budget ({total} > {max_total_tokens})",
                context={
                    **redacted,
                    "usage": usage,
                    "latency_ms": latency_ms,
                },
                user_message="The model used more tokens than allowed for this call.",
            )

    try:
        text = completion_message_text(response)
    except Exception as e:
        raise LLMResponseError(
            "Could not extract text from LLM response",
            context={
                **redacted,
                "latency_ms": latency_ms,
                "response_repr": repr(response)[:2000],
            },
        ) from e

    if require_non_empty_text and not text:
        raise LLMResponseError(
            "Model returned no usable text content",
            context={
                **redacted,
                "usage": usage,
                "latency_ms": latency_ms,
                "model": getattr(response, "model", None),
            },
            user_message="The model returned an empty reply. Check the model and API keys.",
        )

    model = getattr(response, "model", None)
    log_llm_event(
        "llm.response",
        model=model,
        latency_ms=latency_ms,
        usage=usage,
        text_chars=len(text),
    )

    return LLMCallResult(
        text=text,
        latency_ms=latency_ms,
        model=model,
        usage=usage,
        raw_response=response,
    )
