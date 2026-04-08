from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ManimatorError(Exception):
    """Base exception for Manimator errors that should be user-visible."""

    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


class PipelineError(ManimatorError):
    """Pipeline orchestration failed (node crash, invalid state, etc.)."""


class ExternalToolError(ManimatorError):
    """External tool invocation failed (e.g., manim subprocess)."""


class RenderError(ExternalToolError):
    """Manim render failed."""


class ContractValidationError(ManimatorError):
    """A pydantic contract validation failed."""

