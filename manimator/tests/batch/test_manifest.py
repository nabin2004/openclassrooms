"""Tests for batch manifest I/O."""

import json
from pathlib import Path

from manimator.batch.manifest import (
    BatchSampleRef,
    load_samples_from_manifest,
    manifest_path,
    read_batch_manifest,
    write_batch_manifest,
)


def test_write_read_manifest(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    samples = [
        BatchSampleRef(row_id="0", run_id="abc123", raw_query_hash="deadbeef"),
    ]
    path = write_batch_manifest(
        outputs_root=root,
        batch_id="batch1",
        pipeline_fingerprint="fp1",
        prompt_versions={"INTENT_CLASSIFIER_PROMPT_VERSION": "v1"},
        samples=samples,
    )
    assert path == manifest_path(root, "batch1")
    data = read_batch_manifest(path)
    assert data["pipeline_fingerprint"] == "fp1"
    assert data["batch_id"] == "batch1"
    loaded = load_samples_from_manifest(data)
    assert len(loaded) == 1
    assert loaded[0].run_id == "abc123"
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == "1.0.0"
