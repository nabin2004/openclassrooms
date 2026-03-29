#!/usr/bin/env python3
"""Test the scene planner agent individually"""

import asyncio
from manimator.agents.planner import plan_scene
from manimator.contracts.scene_plan import SceneEntry, SceneClass, Budget

async def test_planner():
    scene = SceneEntry(
        id=0,
        title='Introduction to Scatter Plot',
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        prerequisite_ids=[]
    )
    print(f'Input scene: {scene.model_dump()}')
    result = await plan_scene(scene)
    print(f'Scene spec: {result.model_dump()}')
    return result

if __name__ == "__main__":
    asyncio.run(test_planner())
