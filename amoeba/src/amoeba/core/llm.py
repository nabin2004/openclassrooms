import os
from typing import Any, Optional

from amoeba.core.safe_acompletion import acompletion_safe


class LLMClient:
    def __init__(
        self,
        model_env_key: str = None,
        default_model: str = "gpt-4o",
        temperature: float = 0.7,
    ):
        self.model = (
            os.getenv(model_env_key, default_model)
            if model_env_key
            else default_model
        )
        self.temperature = temperature

    async def call(
        self,
        system: str,
        user: str,
        history: Optional[list] = None,
        *,
        max_tokens: Optional[int] = None,
        timeout: float | None = None,
        max_total_tokens: int | None = None,
        allow_empty: bool = False,
        **kwargs: Any,
    ) -> str:
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})

        params: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        _reserved = frozenset(
            {"timeout", "max_total_tokens", "allow_empty", "max_tokens"}
        )
        for key, val in kwargs.items():
            if key not in _reserved:
                params[key] = val
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        result = await acompletion_safe(
            timeout=timeout,
            max_total_tokens=max_total_tokens,
            require_non_empty_text=not allow_empty,
            **params,
        )
        return result.text