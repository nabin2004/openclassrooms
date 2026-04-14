"""Tests for querygen."""

import json
from pathlib import Path

from manimator.batch.querygen import generate_queries_jsonl


def test_querygen_writes_requested_count(tmp_path: Path) -> None:
    out = tmp_path / "q.jsonl"
    n = generate_queries_jsonl(
        output=out,
        count=50,
        topics_file=None,
        shuffle=False,
        seed=None,
    )
    assert n == 50
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 50
    first = json.loads(lines[0])
    assert "raw_query" in first and "row_id" in first


def test_querygen_custom_topics(tmp_path: Path) -> None:
    topics = tmp_path / "t.txt"
    topics.write_text("alpha\nbeta\n# skip\n\n", encoding="utf-8")
    out = tmp_path / "q.jsonl"
    generate_queries_jsonl(
        output=out,
        count=12,
        topics_file=topics,
        shuffle=False,
        seed=None,
    )
    # 2 topics * 20 templates = 40 unique; need 12
    rows = [json.loads(ln) for ln in out.read_text(encoding="utf-8").splitlines()]
    assert "alpha" in rows[0]["raw_query"] or "beta" in rows[0]["raw_query"]
