import pytest
from pydantic import ValidationError
from manimator.contracts.critic import CriticResult, MAX_REPLANS


def test_valid_no_replan():
    result = CriticResult(
        replan_required=False,
        r_visual=0.85, r_semantic=0.90,
        combined_score=0.875,
        replan_count=0,
    )
    assert result.replan_required is False


def test_replan_requires_feedback():
    with pytest.raises(ValidationError, match="critic_feedback"):
        CriticResult(
            replan_required=True,
            failed_scene_ids=[2],
            r_visual=0.71, r_semantic=0.38,
            combined_score=0.545,
            critic_feedback=[],  # empty — should fail
            replan_count=0,
        )


def test_replan_requires_failed_scene_ids():
    with pytest.raises(ValidationError, match="failed_scene_ids"):
        CriticResult(
            replan_required=True,
            failed_scene_ids=[],  # empty: should fail
            r_visual=0.4, r_semantic=0.4,
            combined_score=0.4,
            critic_feedback=["Scene was wrong"],
            replan_count=0,
        )


def test_combined_score_mismatch():
    with pytest.raises(ValidationError, match="combined_score"):
        CriticResult(
            replan_required=False,
            r_visual=0.8, r_semantic=0.6,
            combined_score=0.99,  # wrong: should be 0.7
            replan_count=0,
        )


def test_replan_count_at_max_raises():
    with pytest.raises(ValidationError, match="MAX_REPLANS"):
        CriticResult(
            replan_required=False,
            r_visual=0.8, r_semantic=0.8,
            combined_score=0.8,
            replan_count=MAX_REPLANS,
        )