import os
import pytest
from manimator.agents.intent_classifier import classify_intent
from manimator.contracts.intent import ConceptType, Modality


# Skip entire file if no Groq key present
pytestmark = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set"
)

@pytest.mark.asyncio
async def test_math_query_classified_correctly():
    result = await classify_intent("explain gradient descent visually")
    assert result.in_scope is True
    assert result.concept_type == ConceptType.MATH
    assert result.complexity >= 2


@pytest.mark.asyncio
async def test_cs_query_classified_correctly():
    result = await classify_intent("show me how binary search works")
    assert result.in_scope is True
    assert result.concept_type in {ConceptType.CS, ConceptType.MATH}


@pytest.mark.asyncio
async def test_ai_query_classified_correctly():
    result = await classify_intent("visualize transformer attention mechanism")
    assert result.in_scope is True
    assert result.concept_type in {ConceptType.AI, ConceptType.MIXED}
    assert result.complexity >= 3


@pytest.mark.asyncio
async def test_out_of_scope_query_rejected():
    result = await classify_intent("animate how the heart pumps blood")
    assert result.in_scope is False
    assert result.reject_reason is not None


@pytest.mark.asyncio
async def test_3d_modality_detected():
    result = await classify_intent("show a 3D loss surface for gradient descent")
    assert result.modality in {Modality.THREE_D, Modality.MIXED}


@pytest.mark.asyncio
async def test_graph_modality_detected():
    result = await classify_intent("visualize a binary search tree")
    assert result.modality in {Modality.GRAPH, Modality.TWO_D}