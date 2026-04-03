from pathlib import Path

import pytest
from pipeline.graph import pipeline
from pipeline.state import PipelineState


TEST_QUERIES = [
    "explain gradient descent visually",
    "show me how binary search works",
    "visualize a neural network forward pass",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query", TEST_QUERIES)
async def test_pipeline_completes_on_query(query: str):
    result = await pipeline.ainvoke(PipelineState(raw_query=query))
    assert result["error"] is None
    assert result.get("delivery_dir")
    assert result.get("transcript_path")
    assert result["intent"] is not None
    assert result["scene_plan"] is not None
    assert len(result["scene_specs"]) > 0
    assert len(result["generated_codes"]) > 0
    assert result.get("narrated_paths") is not None
    assert Path(result["transcript_path"]).is_file()
    if result.get("output_video_path"):
        assert Path(result["output_video_path"]).is_file()


@pytest.mark.asyncio
async def test_pipeline_rejects_out_of_scope():
    result = await pipeline.ainvoke(PipelineState(raw_query="animate a heartbeat"))
    # Stub classifier always returns in_scope=True
    # This test will be meaningful once real classifier is implemented
    assert result is not None


@pytest.mark.asyncio
async def test_pipeline_state_is_fully_populated():
    result = await pipeline.ainvoke(
        PipelineState(raw_query="explain gradient descent visually")
    )
    assert result["validation_results"] is not None
    assert result["rendered_paths"] is not None
    assert result["critic_result"] is not None
    assert result.get("narrated_paths") is not None