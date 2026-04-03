"""Optional Result type for pipelines that should not always raise."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    ok: bool
    value: T | None = None
    error: BaseException | None = None

    @staticmethod
    def success(value: T) -> "Result[T]":
        return Result(ok=True, value=value, error=None)

    @staticmethod
    def failure(error: BaseException) -> "Result[T]":
        return Result(ok=False, value=None, error=error)
