import pytest 
from pydantic import ValidationError
from manimator.contracts.intent import ConceptType, IntentResult, Modality

def test_valida_in_scope_intent():
    intent = IntentResult(
        in_scope=True,
        raw_query="Explain gradient descent visually",
        concept_type=ConceptType.MATH,
        modality=Modality.THREE_D,
        complexity=3,
        confidence=0.91,
    )
    assert intent.in_scope is True 
    assert intent.reject_reason is None

def test_out_of_scope_requires_reject_reason():
    with pytest.raises(ValidationError):
        IntentResult(
            in_scope=False,
            raw_query="Animate a heartbeat",
            concept_type=ConceptType.MIXED,
            modality=Modality.TWO_D,
            complexity=1,
            reject_reason=None,
        )

def test_out_of_scope_with_reason_passes():
    intent = IntentResult(
        in_scope=False,
        raw_query="Animate a heartbeat",
        concept_type=ConceptType.MIXED,
        modality=Modality.TWO_D,
        complexity=1,
        reject_reason="Topic not in scope: biological processes cannot be represented in Manim",    
    )

    assert intent.in_scope is False
    assert intent.reject_reason is not None

def test_complexity_bounds():
    with pytest.raises(ValidationError):
        IntentResult(
            in_scope=True,
            raw_query="test",
            concept_type=ConceptType.CS,
            modality=Modality.TWO_D,
            complexity=6,  # max is 5
        )

def test_query_max_length():
    with pytest.raises(ValidationError):
        IntentResult(
            in_scope=True,
            raw_query="x" * 1025,  # max is 1024
            concept_type=ConceptType.CS,
            modality=Modality.TWO_D,
            complexity=1,
        )