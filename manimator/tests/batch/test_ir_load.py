"""Tests for manimator.batch.ir_load."""

from pathlib import Path

import pytest

from manimator.batch.ir_load import load_pipeline_state

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_load_minimal_ir() -> None:
    ir_dir = FIXTURES / "ir_minimal"
    state = load_pipeline_state(ir_dir)
    assert state.raw_query.startswith("Explain unit circles")
    assert state.run_id == "fixture_run_minimal"
    assert state.intent is not None
    assert state.intent.in_scope is True
    assert state.scene_plan is None


def test_load_full_ir() -> None:
    ir_dir = FIXTURES / "ir_full"
    state = load_pipeline_state(ir_dir)
    assert state.run_id == "fixture_run_full"
    assert state.intent is not None
    assert state.scene_plan is not None
    assert len(state.scene_plan.scenes) == 1
    assert len(state.scene_specs) == 1
    assert state.scene_specs[0].class_name == "TestScene"
    assert 0 in state.generated_codes
    assert 0 in state.validation_results
    assert state.validation_results[0].passed is True
    assert state.rendered_paths.get(0, "").endswith(".mp4")
    assert state.critic_result is not None
    assert state.critic_result.replan_required is False


def test_load_missing_summary_raises() -> None:
    with pytest.raises(FileNotFoundError, match="run_summary"):
        load_pipeline_state(FIXTURES / "nonexistent_ir_dir")
