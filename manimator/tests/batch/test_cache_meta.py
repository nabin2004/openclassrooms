"""Tests for batch_cache.json sidecar."""

from pathlib import Path

from manimator.batch.cache_meta import read_batch_cache_fingerprint, write_batch_cache


def test_write_read_cache_fingerprint(tmp_path: Path) -> None:
    ir = tmp_path / "ir"
    write_batch_cache(ir, pipeline_fingerprint="abc")
    assert read_batch_cache_fingerprint(ir) == "abc"
