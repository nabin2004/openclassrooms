"""Regression-style checks for intent classification (prompt + model quality)."""

import os

import pytest

from manimator.agents.intent_classifier import classify_intent

# Expected in_scope only — keeps tests stable across prompt wording tweaks.
INTENT_IN_SCOPE_CASES: list[tuple[str, bool]] = [
    ("What is a circle?", True),
    ("Explain transformers", True),
    ("How does the heart work?", False),
    ("Cook pasta", False),
]

requires_groq = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set",
)


@pytest.mark.asyncio
@requires_groq
@pytest.mark.parametrize("query,expected_in_scope", INTENT_IN_SCOPE_CASES)
async def test_intent_in_scope_matches_expected(query: str, expected_in_scope: bool) -> None:
    result = await classify_intent(query)
    assert result.in_scope is expected_in_scope


@pytest.mark.asyncio
async def test_dry_run_no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MANIMATOR_DRY_RUN", "1")
    r = await classify_intent("What is a circle?")
    assert r.in_scope is True
    r2 = await classify_intent("How does the heart work?")
    assert r2.in_scope is False
