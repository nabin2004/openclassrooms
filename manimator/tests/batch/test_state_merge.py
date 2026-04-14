"""Tests for state_merge."""

from manimator.contracts.intent import ConceptType, IntentResult, Modality
from manimator.batch.state_merge import merge_updates
from manimator.pipeline.state import PipelineState


def test_merge_intent_and_run_dir() -> None:
    state = PipelineState(raw_query="q", run_id="rid")
    intent = IntentResult(
        in_scope=True,
        raw_query="q",
        concept_type=ConceptType.MATH,
        modality=Modality.TWO_D,
        complexity=2,
    )
    merge_updates(state, {"intent": intent, "run_dir": "/tmp/run"})
    assert state.intent is intent
    assert state.run_dir == "/tmp/run"
