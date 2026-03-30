from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional


#  Reversibility 
class Reversibility(str, Enum):
    REVERSIBLE   = "reversible"    # can be undone — move file, update state
    IRREVERSIBLE = "irreversible"  # cannot be undone — render video, send API call
    UNKNOWN      = "unknown"       # default — treat with caution


#  Tool result 
@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __repr__(self):
        status = "ok" if self.success else f"err={self.error}"
        return f"ToolResult({self.tool_name}, {status}, {self.duration_ms:.1f}ms)"


#  Tool base class 
class Tool:
    """
    Base class for all Amoeba tools.

    Subclass this for structured tools with state, or use
    the @action decorator for simple function-based tools.

    Usage:
        class RenderScene(Tool):
            name = "render_scene"
            description = "Renders a Manim scene to video"
            reversibility = Reversibility.IRREVERSIBLE
            confidence_threshold = 0.9

            async def run(self, scene_spec: dict) -> dict:
                # render logic
                return {"path": "/output/scene.mp4"}
    """

    name: str = "unnamed_tool"
    description: str = ""
    reversibility: Reversibility = Reversibility.UNKNOWN
    confidence_threshold: float = 0.0   # 0.0 = always run, 1.0 = never run

    async def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    async def execute(self, *args, confidence: float = 1.0, **kwargs) -> ToolResult:
        """
        Safe execution wrapper.
        Checks confidence threshold before running irreversible actions.
        """
        if (
            self.reversibility == Reversibility.IRREVERSIBLE
            and confidence < self.confidence_threshold
        ):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=(
                    f"Confidence {confidence:.2f} below threshold "
                    f"{self.confidence_threshold:.2f} for irreversible action"
                ),
            )

        start = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(self.run):
                output = await self.run(*args, **kwargs)
            else:
                output = self.run(*args, **kwargs)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def to_llm_schema(self) -> dict:
        """
        Describes this tool for the LLM's tool-use context.
        Matches the shape LiteLLM / OpenAI function calling expects.
        """
        return {
            "name": self.name,
            "description": self.description,
            "reversibility": self.reversibility.value,
        }

    def __repr__(self):
        return f"Tool(name={self.name}, reversibility={self.reversibility.value})"


#  @action decorator --> for function-based tools 
#
#  Use this when you don't need state or subclassing.
#  Wraps any sync or async function into a full Tool instance.
#
#  Usage:
#      @action(reversible=False, confidence_threshold=0.85)
#      async def render_scene(scene_spec: dict) -> dict:
#          ...
#
#      @action(reversible=True)
#      def update_state(key: str, value: Any) -> None:
#          ...

def action(
    reversible: bool = True,
    confidence_threshold: float = 0.0,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Decorator that turns any function into a Tool instance.

    Args:
        reversible:            Whether the action can be undone.
        confidence_threshold:  Min confidence required to execute if irreversible.
        name:                  Override tool name (defaults to function name).
        description:           Override description (defaults to docstring).
    """
    def decorator(fn: Callable) -> Tool:
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip()
        tool_rev  = (
            Reversibility.REVERSIBLE
            if reversible
            else Reversibility.IRREVERSIBLE
        )

        # Build a Tool subclass dynamically from the function
        is_async = asyncio.iscoroutinefunction(fn)

        class FunctionTool(Tool):
            pass

        FunctionTool.name                 = tool_name
        FunctionTool.description          = tool_desc
        FunctionTool.reversibility        = tool_rev
        FunctionTool.confidence_threshold = confidence_threshold

        if is_async:
            async def _run(self, *args, **kwargs):
                return await fn(*args, **kwargs)
        else:
            async def _run(self, *args, **kwargs):
                return fn(*args, **kwargs)

        FunctionTool.run = _run

        # Return an instance, not the class
        # so @action tools are used directly: render_scene.execute(...)
        instance = FunctionTool()
        instance.__wrapped__ = fn   # preserve original for testing
        return instance

    return decorator


#  ToolRegistry — agent's tool belt ─

class ToolRegistry:
    """
    Holds all tools available to an agent.
    Agents call registry.execute(name, ...) rather than tools directly —
    this gives a single place for logging, retries, and confidence gating.
    """

    def __init__(self, tools: list[Tool] = []):
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    async def execute(
        self,
        name: str,
        *args,
        confidence: float = 1.0,
        **kwargs,
    ) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Tool '{name}' not found in registry",
            )
        return await tool.execute(*args, confidence=confidence, **kwargs)

    def schemas(self) -> list[dict]:
        """All tool schemas — pass to LLM for tool-use context."""
        return [t.to_llm_schema() for t in self._tools.values()]

    def __len__(self):
        return len(self._tools)

    def __repr__(self):
        names = list(self._tools.keys())
        return f"ToolRegistry(tools={names})"   