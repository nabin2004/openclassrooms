from pydantic import BaseModel, Field, model_validator
from enum import Enum


class ConceptType(str, Enum):
    MATH = "math"
    CS = "cs"
    AI = "ai"
    MIXED = "mixed"

class Modality(str, Enum):
    TWO_D = "2d"
    THREE_D = "3d"
    GRAPH = "graph"
    MIXED = "mixed"
    
class IntentResult(BaseModel):
    in_scope: bool 
    raw_query: str = Field(max_length=1024)
    concept_type: ConceptType 
    modality: Modality 
    complexity: int = Field(ge=1, le=5)
    reject_reason: str | None = None 
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def reject_reason_required_when_out_of_scope(self) -> "IntentResult":
        if not self.in_scope and self.reject_reason is None:
            raise ValueError("reject_reason is required when in_scope is False")
        return self