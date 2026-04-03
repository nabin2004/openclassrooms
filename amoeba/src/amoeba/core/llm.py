import os
from typing import Any, Optional

import litellm

from amoeba.core.responses import completion_message_text


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
            **kwargs,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        response = await litellm.acompletion(**params)
        return completion_message_text(response)