#!/usr/bin/env python3
"""
CLI tool to set video configuration preferences
Usage: python set_video_config.py [config_type]
"""

import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python set_video_config.py [unlimited|conservative|educational]")
        print("\nConfiguration types:")
        print("  unlimited    - No limits on scenes, duration, animations")
        print("  conservative - Moderate limits (10 scenes, 5 min, 15 anims/scene)")
        print("  educational  - Educational content limits (20 scenes, 10 min, 25 anims/scene)")
        return
    
    config_type = sys.argv[1].lower()
    
    if config_type not in ["unlimited", "conservative", "educational"]:
        print("Error: Invalid configuration type")
        return
    
    # Set environment variable in .env file
    env_file = Path(".env")
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add the config line
    config_line = f"MANIMATOR_VIDEO_CONFIG={config_type}\n"
    found = False
    
    # Remove any existing MANIMATOR_VIDEO_CONFIG lines
    lines = [line for line in lines if not line.startswith("MANIMATOR_VIDEO_CONFIG=")]
    
    # Add the new config line
    lines.append(config_line)
    
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Video configuration set to: {config_type}")
    print(f"Updated {env_file}")
    
    # Show current settings
    from manimator.config.video_config import get_video_config
    config = get_video_config()
    
    print(f"\nCurrent settings:")
    print(f"  Max scenes: {config.max_scenes or 'unlimited'}")
    print(f"  Max duration: {config.max_duration_seconds or 'unlimited'} seconds")
    print(f"  Max animations per scene: {config.max_animations_per_scene or 'unlimited'}")
    print(f"  Max title length: {config.max_title_length or 'unlimited'} characters")

if __name__ == "__main__":
    main()
