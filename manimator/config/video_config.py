"""Video configuration settings for flexible video length and scene count"""

from pydantic import BaseModel, Field
from typing import Optional


class VideoConfig(BaseModel):
    """Configuration for video generation parameters"""
    
    # Scene limits (set to None for unlimited)
    max_scenes: Optional[int] = Field(default=None, description="Maximum number of scenes (None = unlimited)")
    min_scenes: int = Field(default=1, description="Minimum number of scenes")
    
    # Duration limits (set to None for unlimited)
    max_duration_seconds: Optional[int] = Field(default=None, description="Maximum video duration in seconds (None = unlimited)")
    min_duration_seconds: int = Field(default=5, description="Minimum video duration in seconds")
    
    # Animation limits (set to None for unlimited)
    max_animations_per_scene: Optional[int] = Field(default=None, description="Maximum animations per scene (None = unlimited)")
    min_animations_per_scene: int = Field(default=1, description="Minimum animations per scene")
    
    # Title limits (set to None for unlimited)
    max_title_length: Optional[int] = Field(default=None, description="Maximum title length (None = unlimited)")
    
    # Retry limits
    max_retries: int = Field(default=10, description="Maximum repair attempts per scene")
    
    # Quality settings
    default_quality: str = Field(default="medium", description="Default video quality (low, medium, high)")
    
    # Output settings
    output_format: str = Field(default="mp4", description="Output video format")
    
    @classmethod
    def unlimited(cls) -> "VideoConfig":
        """Create config with no limitations"""
        return cls(
            max_scenes=None,
            max_duration_seconds=None,
            max_animations_per_scene=None,
            max_title_length=None
        )
    
    @classmethod
    def conservative(cls) -> "VideoConfig":
        """Create config with conservative limitations"""
        return cls(
            max_scenes=10,
            max_duration_seconds=300,  # 5 minutes
            max_animations_per_scene=15,
            max_title_length=100,
            max_retries=5
        )
    
    @classmethod
    def educational(cls) -> "VideoConfig":
        """Create config optimized for educational content"""
        return cls(
            max_scenes=20,
            max_duration_seconds=600,  # 10 minutes
            max_animations_per_scene=25,
            max_title_length=150,
            max_retries=8
        )


# Default configuration - can be overridden by environment or user input
DEFAULT_CONFIG = VideoConfig.unlimited()


def get_video_config() -> VideoConfig:
    """Get current video configuration"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check for environment variable override
    config_type = os.getenv("MANIMATOR_VIDEO_CONFIG", "unlimited").lower()
    
    if config_type == "unlimited":
        return VideoConfig.unlimited()
    elif config_type == "conservative":
        return VideoConfig.conservative()
    elif config_type == "educational":
        return VideoConfig.educational()
    else:
        return DEFAULT_CONFIG


def apply_config_limits(prompt: str, config: VideoConfig = None) -> str:
    """Apply configuration limits to a prompt"""
    if config is None:
        config = get_video_config()
    
    limit_text = []
    
    if config.max_scenes:
        limit_text.append(f"scene_count: integer (1-{config.max_scenes})")
    else:
        limit_text.append("scene_count: integer (no limit)")
    
    if config.max_title_length:
        limit_text.append(f"title: string (max {config.max_title_length} characters)")
    else:
        limit_text.append("title: string (no character limit)")
    
    if config.max_duration_seconds:
        limit_text.append(f"total_duration_target: integer (max {config.max_duration_seconds} seconds)")
    else:
        limit_text.append("total_duration_target: integer (no limit - seconds)")
    
    if config.max_animations_per_scene:
        limit_text.append(f"animations: create up to {config.max_animations_per_scene} animations per scene")
    else:
        limit_text.append("animations: create as many animations as needed")
    
    return "\n".join(limit_text)
