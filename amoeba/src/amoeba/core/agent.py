from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from amoeba.core.llm import LLMClient
from amoeba.core.safe_acompletion import LLMResponse
from amoeba.core.memory import DagestanAdapter, StatelessMemoryAdapter
from amoeba.exceptions import ConfigurationError, StructuredOutputError
from amoeba.utils import safe_parse_json

T = TypeVar("T", bound=BaseModel)


class Agent:
    def __init__(
        self,
        name: str,
        role: str,
        model_env_key: str | None = None,
        default_model: str = "gpt-4o",
        memory: Optional[DagestanAdapter | StatelessMemoryAdapter] = None,
        temperature: float = 0.7,
        output_schema: Optional[Type[BaseModel]] = None,
    ):
        self.name = name
        self.role = role
        self.output_schema = output_schema
        self.memory = memory or DagestanAdapter()
        self._llm = LLMClient(
            model_env_key=model_env_key,
            default_model=default_model,
            temperature=temperature,
        )
        self._history: list[dict[str, str]] = []

    @property
    def last_llm_response(self) -> LLMResponse | None:
        return self._llm.last_response

    async def think(
        self,
        user_input: str,
        context: dict | None = None,
        *,
        max_tokens: int | None = None,
        model: str | None = None,
        **llm_kwargs: Any,
    ) -> str:
        if context is None:
            context = {}
        past = self.memory.recall(self.name, user_input)
        system = self.role
        if past:
            system += f"\n\nRelevant context from memory:\n{past}"

        raw = await self._llm.call(
            system=system,
            user=user_input,
            history=self._history,
            max_tokens=max_tokens,
            model=model,
            **llm_kwargs,
        )

        self.memory.snapshot(
            self.name,
            {
                "input": user_input,
                "output": raw,
                "context": context,
            },
        )
        self._history.append({"role": "user", "content": user_input})
        self._history.append({"role": "assistant", "content": raw})
        return raw

    async def think_and_parse(
        self,
        user_input: str,
        schema: Optional[Type[T]] = None,
        context: dict | None = None,
        *,
        max_tokens: int | None = None,
        model: str | None = None,
        **llm_kwargs: Any,
    ) -> T:
        raw = await self.think(
            user_input,
            context=context,
            max_tokens=max_tokens,
            model=model,
            **llm_kwargs,
        )
        target_schema = schema or self.output_schema
        if not target_schema:
            raise ConfigurationError(
                "No output schema provided for think_and_parse",
                context={"agent": self.name},
            )

        data = safe_parse_json(raw)
        if not isinstance(data, dict):
            raise StructuredOutputError(
                f"Model output for {target_schema.__name__} must be a JSON object, got {type(data).__name__}",
                context={
                    "agent": self.name,
                    "raw_preview": raw[:2000],
                },
                user_message="The model returned JSON that was not an object (for example a bare array).",
            )
        try:
            return target_schema(**data)
        except ValidationError as e:
            raise StructuredOutputError(
                f"Model output failed validation for {target_schema.__name__}",
                context={
                    "agent": self.name,
                    "pydantic_errors": e.errors(),
                    "raw_preview": raw[:2000],
                },
                user_message="The model returned JSON that did not match the expected shape.",
            ) from e

    async def run(self, state: dict) -> dict:
        raise NotImplementedError("Subclasses must implement run()")

    def as_node(self):
        import asyncio
        def node(state: dict) -> dict:
            return asyncio.get_event_loop().run_until_complete(self.run(state))
        return node

    def reset_history(self):
        self._history = []

    def __repr__(self):
        return f"Agent(name={self.name}, model={self._llm.model})"