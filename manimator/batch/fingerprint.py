"""Stable pipeline fingerprint for batch resume and manifest (env + config)."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from manimator.config.video_config import get_video_config


def prompt_versions_snapshot() -> dict[str, str]:
    """Resolved prompt versions from environment (matches manimator.prompts.registry)."""
    return {
        "INTENT_CLASSIFIER_PROMPT_VERSION": os.getenv("INTENT_CLASSIFIER_PROMPT_VERSION", "v1").strip(),
        "SCENE_DECOMPOSER_PROMPT_VERSION": os.getenv("SCENE_DECOMPOSER_PROMPT_VERSION", "v1").strip(),
        "SCENE_PLANNER_PROMPT_VERSION": os.getenv("SCENE_PLANNER_PROMPT_VERSION", "v1").strip(),
        "CODE_REPAIR_PROMPT_VERSION": os.getenv("CODE_REPAIR_PROMPT_VERSION", "v1").strip(),
    }


def _video_config_fingerprint_payload() -> dict[str, Any]:
    vc = get_video_config()
    return json.loads(vc.model_dump_json())


def compute_pipeline_fingerprint(
    *,
    extra: dict[str, Any] | None = None,
) -> str:
    """
    SHA256 hex digest of prompt versions + video config + optional extra keys.

    Used in batch manifest; resume skips only when this matches the manifest.
    """
    payload: dict[str, Any] = {
        "prompt_versions": prompt_versions_snapshot(),
        "video_config": _video_config_fingerprint_payload(),
        "manimator_video_config_env": os.getenv("MANIMATOR_VIDEO_CONFIG", "unlimited").strip().lower(),
    }
    if extra:
        payload["extra"] = extra
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
