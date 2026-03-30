from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from amoeba.core.llm import LLMClient
from amoeba.core.memory import DagestanAdapter
from amoeba.src.amoeba.utils import safe_parse_json

T = TypeVar("T", bound=BaseModel)

class Agent:
    def __init__(
        self,
        name: str,
        role: str,
        model_env_key: str = None,
        default_model: str = "gpt-4o",
        memory: Optional[DagestanAdapter] = None,
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
        self._history: list = []

    async def think(self, user_input: str, context: dict = {}) -> str:
        past = self.memory.recall(self.name, user_input)
        system = self.role
        if past:
            system += f"\n\nRelevant context from memory:\n{past}"

        raw = await self._llm.call(
            system=system,
            user=user_input,
            history=self._history,
        )

        self.memory.snapshot(self.name, {
            "input": user_input,
            "output": raw,
            "context": context,
        })
        self._history.append({"role": "user", "content": user_input})
        self._history.append({"role": "assistant", "content": raw})
        return raw

    async def think_and_parse(
        self,
        user_input: str,
        schema: Optional[Type[T]] = None,
        context: dict = {},
    ) -> T:
        raw = await self.think(user_input, context=context)
        target_schema = schema or self.output_schema
        if not target_schema:
            raise ValueError("No output schema provided")

        data = safe_parse_json(raw)
        try:
            return target_schema(**data)
        except Exception as e:
            raise ValueError(
                f"Failed to parse {target_schema.__name__}: {e}\nRaw:\n{raw}"
            )

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