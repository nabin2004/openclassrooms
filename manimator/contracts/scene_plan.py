from enum import Enum
from pydantic import BaseModel, Field, model_validator


class SceneClass(str, Enum):
    SCENE = "Scene"
    THREE_D = "ThreeDScene"
    MOVING_CAMERA = "MovingCameraScene"
    ZOOMED = "ZoomedScene"
    GRAPH = "GraphScene"


class Budget(str, Enum):
    LOW = "low"      # max 3 animations
    MEDIUM = "medium"  # max 6 animations
    HIGH = "high"    # max 10 animations


class TransitionStyle(str, Enum):
    CUT = "cut"
    FADE = "fade"
    CONTINUATION = "continuation"
    WIPE = "wipe"


class SceneEntry(BaseModel):
    id: int = Field(ge=0)
    title: str = Field(max_length=40)
    scene_class: SceneClass
    budget: Budget
    prerequisite_ids: list[int] = Field(default_factory=list)


class ScenePlan(BaseModel):
    scene_count: int = Field(ge=1, le=6)
    scenes: list[SceneEntry]
    transition_style: TransitionStyle
    total_duration_target: int | None = Field(default=None, ge=10, le=300)

    @model_validator(mode="after")
    def scene_count_matches_scenes(self) -> "ScenePlan":
        if len(self.scenes) != self.scene_count:
            raise ValueError(
                f"scene_count={self.scene_count} but got {len(self.scenes)} scenes"
            )
        return self

    @model_validator(mode="after")
    def no_self_referencing_prerequisites(self) -> "ScenePlan":
        ids = {s.id for s in self.scenes}
        for scene in self.scenes:
            for prereq in scene.prerequisite_ids:
                if prereq not in ids:
                    raise ValueError(
                        f"Scene {scene.id} references unknown prerequisite {prereq}"
                    )
                if prereq == scene.id:
                    raise ValueError(f"Scene {scene.id} cannot be its own prerequisite")
        return self

    @model_validator(mode="after")
    def no_cycles_in_prerequisites(self) -> "ScenePlan":
        # Kahn's algorithm: if topo sort doesn't consume all nodes, there's a cycle
        from collections import deque
        graph: dict[int, list[int]] = {s.id: list(s.prerequisite_ids) for s in self.scenes}
        in_degree: dict[int, int] = {s.id: 0 for s in self.scenes}
        for scene in self.scenes:
            for prereq in scene.prerequisite_ids:
                in_degree[scene.id] += 1
        queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for scene in self.scenes:
                if node in scene.prerequisite_ids:
                    in_degree[scene.id] -= 1
                    if in_degree[scene.id] == 0:
                        queue.append(scene.id)
        if visited != len(self.scenes):
            raise ValueError("Cycle detected in scene prerequisites")
        return self