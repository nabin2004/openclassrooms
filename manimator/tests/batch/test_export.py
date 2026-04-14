"""Tests for dataset export."""

import shutil
from pathlib import Path

from manimator.batch.export import export_batch
from manimator.batch.manifest import BatchSampleRef, write_batch_manifest
from manimator.batch.stages import LogicalStage

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "ir_full"


def test_export_writes_jsonl(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    run_id = "export_test_run"
    ir_dst = root / "runs" / run_id / "ir"
    shutil.copytree(FIXTURES, ir_dst)

    write_batch_manifest(
        outputs_root=root,
        batch_id="exp1",
        pipeline_fingerprint="testfp",
        prompt_versions={"INTENT_CLASSIFIER_PROMPT_VERSION": "v1"},
        samples=[BatchSampleRef(row_id="0", run_id=run_id, raw_query_hash="x")],
    )

    written = export_batch(
        outputs_root=root,
        batch_id="exp1",
        stages=(LogicalStage.intent, LogicalStage.scene_plan),
    )
    assert "intent" in written
    lines = written["intent"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    import json

    row = json.loads(lines[0])
    assert row["metadata"]["run_id"] == run_id
    assert row["metadata"]["stage"] == "intent"
    assert row["input"]["raw_query"] == "Batch fixture full IR."
    assert row["output"]["concept_type"] == "cs"
