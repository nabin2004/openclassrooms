import pytest
from manimator.contracts.intent import ConceptType, Modality
from manimator.contracts.scene_plan import Budget, SceneClass, SceneEntry, TransitionStyle
from manimator.contracts.validation import MAX_RETRIES
from manimator.agents.intent_classifier import classify_intent
from manimator.agents.scene_decomposer import decompose_scenes
from manimator.agents.planner import plan_scene
from manimator.agents.codegen import generate_code
from manimator.agents.validator import validate_code
from manimator.agents.critic import critique_render


@pytest.mark.asyncio
async def test_intent_classifier_returns_valid_contract():
    result = await classify_intent("explain gradient descent")
    assert result.in_scope is True
    assert result.concept_type in ConceptType
    assert result.modality in Modality
    assert 1 <= result.complexity <= 5


@pytest.mark.asyncio
async def test_decomposer_returns_valid_plan():
    from contracts.intent import IntentResult
    intent = IntentResult(
        in_scope=True,
        raw_query="explain gradient descent",
        concept_type=ConceptType.MATH,
        modality=Modality.THREE_D,
        complexity=3,
    )
    plan = await decompose_scenes(intent)
    assert plan.scene_count == len(plan.scenes)
    assert plan.scene_count >= 1


@pytest.mark.asyncio
async def test_planner_returns_valid_spec():
    scene = SceneEntry(
        id=0,
        title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.MEDIUM,
        prerequisite_ids=[],
    )
    spec = await plan_scene(scene)
    assert spec.scene_id == 0
    assert len(spec.animations) > 0


@pytest.mark.asyncio
async def test_codegen_returns_string():
    scene = SceneEntry(
        id=0, title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        prerequisite_ids=[],
    )
    from agents.planner import plan_scene
    spec = await plan_scene(scene)
    code = await generate_code(spec)
    assert "def construct" in code
    assert "class " in code


@pytest.mark.asyncio
async def test_validator_passes_valid_code():
    scene = SceneEntry(
        id=0, title="TestScene",
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        prerequisite_ids=[],
    )
    from agents.planner import plan_scene
    from agents.codegen import generate_code
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
    from agents.planner import plan_scene
    spec = await plan_scene(scene)
    result = await validate_code("def broken(: pass", spec, retry_count=0)
    assert result.passed is False
    assert result.error_type is not None


@pytest.mark.asyncio
async def test_critic_stub_always_passes():
    result = await critique_render(
        scene_ids=[0, 1],
        keyframe_paths=[],
        replan_count=0,
    )
    assert result.replan_required is False
    assert result.combined_score > 0.6