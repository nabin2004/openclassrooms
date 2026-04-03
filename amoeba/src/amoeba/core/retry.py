"""Selective async retries for transient LLM failures."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from amoeba.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError

T = TypeVar("T")

logger = logging.getLogger("amoeba.retry")


async def async_retry_llm(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_s: float = 1.0,
    retry_exceptions: tuple[type[LLMError], ...] = (
        LLMRateLimitError,
        LLMTimeoutError,
    ),
) -> T:
    """
    Retry only **retryable** LLM errors (rate limit, timeout by default).

    Other :class:`~amoeba.exceptions.LLMError` subclasses are re-raised immediately.
    """
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except retry_exceptions as e:
            last_exc = e
            if attempt >= max_attempts:
                raise
            delay = base_delay_s * (2 ** (attempt - 1))
            logger.warning(
                "amoeba.retry backing off attempt=%s/%s delay_s=%s exc=%s",
                attempt,
                max_attempts,
                delay,
                type(e).__name__,
            )
            await asyncio.sleep(delay)
        except LLMError:
            raise
    assert last_exc is not None
    raise last_exc
