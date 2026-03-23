from dataclasses import dataclass, field
from manimator.contracts.intent import IntentResult
from manimator.contracts.scene_plan import ScenePlan, SceneEntry
from manimator.contracts.scene_spec import SceneSpec
from manimator.contracts.validation import ValidationResult
from manimator.contracts.critic import CriticResult

@dataclass
class PipelineState:
    # Input
    raw_query: str = ""

    # Agent outputs — populated as pipeline progresses
    intent: IntentResult | None = None
    scene_plan: ScenePlan | None = None
    scene_specs: list[SceneSpec] = field(default_factory=list)
    generated_codes: dict[int, str] = field(default_factory=dict)  # scene_id → code
    validation_results: dict[int, ValidationResult] = field(default_factory=dict)
    rendered_paths: dict[int, str] = field(default_factory=dict)   # scene_id → video path
    critic_result: CriticResult | None = None

    # Control flow
    current_scene_index: int = 0
    replan_count: int = 0
    retry_counts: dict[int, int] = field(default_factory=dict)     # scene_id → retry count
    failed_scene_ids: list[int] = field(default_factory=list)

    # Final output
    output_video_path: str | None = None
    error: str | None = None