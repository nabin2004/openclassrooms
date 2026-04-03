import os
from typing import Optional

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
    ) -> str:
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return completion_message_text(response)