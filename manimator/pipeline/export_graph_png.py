"""
Regenerate LangGraph pipeline PNGs at the repo root.

Uses LangChain's mermaid.ink renderer (needs network). Run from repo root::

    uv run --package manimator python -m manimator.pipeline.export_graph_png
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    from manimator.pipeline.graph import build_pipeline

    png = build_pipeline().get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)
    for name in ("pipeline_graph.png", "manimator_pipeline.png"):
        path = repo_root / name
        path.write_bytes(png)
        print(f"Wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
