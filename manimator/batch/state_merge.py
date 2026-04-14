"""Merge LangGraph-style node return dicts into PipelineState."""

from __future__ import annotations

from manimator.pipeline.state import PipelineState


def merge_updates(state: PipelineState, updates: dict) -> None:
    """Apply keys returned by ``node_*`` functions (same contract as LangGraph reducers)."""
    for key, value in updates.items():
        if not hasattr(state, key):
            continue
        setattr(state, key, value)
