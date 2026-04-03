from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Prompt:
    """Versioned system prompt for an agent or pipeline stage."""

    name: str
    version: str
    system: str
