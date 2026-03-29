# Video Configuration Guide

This guide explains how to configure video length, scene count, and animation limits in the Manimator system.

## Overview

The Manimator system now supports flexible configuration of:
- **Scene count limits** (or unlimited)
- **Video duration limits** (or unlimited) 
- **Animation limits per scene** (or unlimited)
- **Title length limits** (or unlimited)

## Configuration Types

### 1. Unlimited (Default)
```bash
python set_video_config.py unlimited
```
- **Max scenes**: Unlimited
- **Max duration**: Unlimited
- **Max animations per scene**: Unlimited
- **Max title length**: Unlimited
- **Use case**: Maximum creative freedom, no constraints

### 2. Conservative
```bash
python set_video_config.py conservative
```
- **Max scenes**: 10
- **Max duration**: 300 seconds (5 minutes)
- **Max animations per scene**: 15
- **Max title length**: 100 characters
- **Use case**: Quick, focused animations

### 3. Educational
```bash
python set_video_config.py educational
```
- **Max scenes**: 20
- **Max duration**: 600 seconds (10 minutes)
- **Max animations per scene**: 25
- **Max title length**: 150 characters
- **Use case**: Comprehensive educational content

## Usage

### Setting Configuration
```bash
# Set to unlimited (no limits)
python set_video_config.py unlimited

# Set to conservative (moderate limits)
python set_video_config.py conservative

# Set to educational (generous limits for teaching)
python set_video_config.py educational
```

### Checking Current Configuration
```bash
python set_video_config.py [type]
# Shows current settings after setting
```

### Environment Variable
You can also set the configuration directly in your `.env` file:
```bash
MANIMATOR_VIDEO_CONFIG=unlimited
MANIMATOR_VIDEO_CONFIG=conservative
MANIMATOR_VIDEO_CONFIG=educational
```

## How It Works

### Dynamic Prompt Generation
The system automatically adjusts LLM prompts based on your configuration:

**Unlimited Example:**
```
scene_count: integer (no limit)
title: string (no character limit)
total_duration_target: integer (no limit - seconds)
animations: create as many animations as needed
```

**Conservative Example:**
```
scene_count: integer (1-10)
title: string (max 100 characters)
total_duration_target: integer (max 300 seconds)
animations: create up to 15 animations per scene
```

### Validation Updates
- **Scene contracts**: Removed hard limits
- **Budget caps**: Set to 999 (effectively unlimited)
- **Planner prompts**: Updated to respect configuration
- **Title validation**: Now configurable

## Examples

### Example 1: Unlimited Mode
```bash
python set_video_config.py unlimited
python manimator/agents/scene_decomposer.py
```
Output: 7 scenes, 300-second duration, long descriptive titles

### Example 2: Conservative Mode
```bash
python set_video_config.py conservative
python manimator/agents/scene_decomposer.py
```
Output: 6 scenes, 240-second duration, concise titles

### Example 3: Educational Mode
```bash
python set_video_config.py educational
python manimator/agents/scene_decomposer.py
```
Output: More scenes, longer duration, detailed titles

## Advanced Configuration

### Custom Configuration
You can create custom configurations by modifying `manimator/config/video_config.py`:

```python
@classmethod
def custom(cls) -> "VideoConfig":
    return cls(
        max_scenes=15,
        max_duration_seconds=450,  # 7.5 minutes
        max_animations_per_scene=20,
        max_title_length=120
    )
```

### Programmatic Access
```python
from manimator.config.video_config import get_video_config

config = get_video_config()
print(f"Max scenes: {config.max_scenes}")
print(f"Max duration: {config.max_duration_seconds}")
```

## Testing Different Configurations

### Quick Testing
```bash
# Test with unlimited config
make test-decomposer

# Change to conservative
python set_video_config.py conservative
make test-decomposer

# Change to educational  
python set_video_config.py educational
make test-decomposer
```

### Pipeline Testing
```bash
# Test full pipeline with different configs
python set_video_config.py unlimited
make test-pipeline

python set_video_config.py conservative
make test-pipeline
```

## Best Practices

1. **Start with Unlimited**: For initial development and testing
2. **Use Conservative**: For quick prototypes and demos
3. **Choose Educational**: For comprehensive teaching content
4. **Monitor Performance**: Longer videos take more time to render
5. **Consider Audience**: Shorter videos for social media, longer for deep learning

## Troubleshooting

### Configuration Not Applying
1. Check `.env` file for correct setting
2. Restart your Python process
3. Verify no duplicate entries in `.env`

### Scenes Still Limited
1. Ensure contracts are updated (check `scene_plan.py`)
2. Verify budget caps in `scene_spec.py`
3. Check planner prompts are updated

### Titles Still Truncated
1. Verify `SceneEntry` model in `scene_plan.py`
2. Check decomposer prompt limits
3. Ensure configuration is loading correctly

## File Locations

- **Configuration**: `manimator/config/video_config.py`
- **Contracts**: `manimator/contracts/scene_plan.py`
- **Scene Limits**: `manimator/contracts/scene_spec.py`
- **Planner**: `manimator/agents/planner.py`
- **Decomposer**: `manimator/agents/scene_decomposer.py`
- **CLI Tool**: `set_video_config.py`

This configuration system gives you complete control over video length and complexity while maintaining the ability to create comprehensive, educational content.
