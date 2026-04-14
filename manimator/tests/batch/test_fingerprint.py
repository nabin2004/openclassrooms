"""Tests for pipeline fingerprint."""

from manimator.batch.fingerprint import compute_pipeline_fingerprint, prompt_versions_snapshot


def test_fingerprint_stable(monkeypatch) -> None:
    monkeypatch.setenv("INTENT_CLASSIFIER_PROMPT_VERSION", "v2")
    monkeypatch.setenv("MANIMATOR_VIDEO_CONFIG", "unlimited")
    a = compute_pipeline_fingerprint()
    b = compute_pipeline_fingerprint()
    assert a == b
    assert len(a) == 64
    snap = prompt_versions_snapshot()
    assert snap["INTENT_CLASSIFIER_PROMPT_VERSION"] == "v2"


def test_fingerprint_changes_with_prompt_version(monkeypatch) -> None:
    monkeypatch.setenv("INTENT_CLASSIFIER_PROMPT_VERSION", "v1")
    fp1 = compute_pipeline_fingerprint()
    monkeypatch.setenv("INTENT_CLASSIFIER_PROMPT_VERSION", "v2")
    fp2 = compute_pipeline_fingerprint()
    assert fp1 != fp2
