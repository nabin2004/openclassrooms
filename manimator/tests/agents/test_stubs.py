import pytest
from manimator.contracts.intent import ConceptType, Modality, IntentResult
from manimator.contracts.scene_plan import Budget, SceneClass, SceneEntry
from manimator.agents.scene_decomposer import decompose_scenes
from manimator.agents.planner import plan_scene
from manimator.agents.codegen import generate_code
from manimator.agents.validator import validate_code
from manimator.agents.critic import critique_render


@pytest.mark.asyncio
async def test_intent_stub_returns_valid_contract():
    # Tests the contract shape only no LLM call
    intent = IntentResult(
        in_scope=True,
        raw_query="explain gradient descent",
        concept_type=ConceptType.MATH,
        modality=Modality.THREE_D,
        complexity=3,
    )
    assert intent.in_scope is True
    assert 1 <= intent.complexity <= 5


@pytest.mark.asyncio
async def test_decomposer_returns_valid_plan():
    intent = IntentResult(
        in_scope=True,
        raw_query="explain gradient descent",
        concept_type=ConceptType.MATH,
        modality=Modality.THREE_D,
        complexity=3,
    )
    plan = await decompose_scenes(intent)
    assert plan.scene_count == len(plan.scenes)


@pytest.mark.asyncio
async def test_planner_returns_valid_spec():
    scene = SceneEntry(
        id=0, title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.MEDIUM,
        prerequisite_ids=[],
    )
    spec = await plan_scene(scene)
    assert spec.scene_id == 0


@pytest.mark.asyncio
async def test_codegen_returns_string():
    scene = SceneEntry(
        id=0, title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        prerequisite_ids=[],
    )
    spec = await plan_scene(scene)
    code = await generate_code(spec)
    assert "def construct" in code


@pytest.mark.asyncio
async def test_validator_passes_valid_code():
    scene = SceneEntry(
        id=0, title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        prerequisite_ids=[],
    )
    spec = await plan_scene(scene)
    code = await generate_code(spec)
    result = await validate_code(code, spec, retry_count=0)
    assert result.passed is True


@pytest.mark.asyncio
async def test_validator_catches_syntax_error():
    scene = SceneEntry(
        id=0, title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        prerequisite_ids=[],
    )
    spec = await plan_scene(scene)
    result = await validate_code("def broken(: pass", spec, retry_count=0)
    assert result.passed is False


@pytest.mark.asyncio
async def test_critic_stub_always_passes():
    result = await critique_render(scene_ids=[0, 1], keyframe_paths=[], replan_count=0)
    assert result.replan_required is False