#!/usr/bin/env python3
"""Test the critic agent individually"""

import asyncio
from manimator.agents.critic import critique_render

async def test_critic():
    scene_ids = [0, 1, 2]
    keyframe_paths = ['test_outputs/scene_0.mp4', 'test_outputs/scene_1.mp4', 'test_outputs/scene_2.mp4']
    print(f'Input scenes: {scene_ids}')
    print(f'Input paths: {keyframe_paths}')
    result = await critique_render(scene_ids, keyframe_paths)
    print(f'Critic result: {result.model_dump()}')
    return result

if __name__ == "__main__":
    asyncio.run(test_critic())
