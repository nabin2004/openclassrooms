from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
import os
import subprocess
import json
import tempfile
from google.adk.tools import ToolContext
import soundfile as sf
import numpy as np

# Import TTS registry and engine
from .tts.engine import TTSEngine
from .tts.registry import get_provider, register_provider
# (We assume the built-in providers are auto-registered)

# ------------------------------
# 1. Decomposer: topic → scenes (JSON)
# ------------------------------
decomposer = Agent(
    model='gemini-2.5-flash',   
    name='decomposer',
    description='Decomposes a CS topic into scenes for a 3Blue1Brown-style video.',
    instruction="""
You are a CS education director for a 3Blue1Brown-style channel.
You decompose topics into scenes. Each scene answers exactly ONE question
a viewer would naturally ask — ordered by the viewer's confusion, not the textbook.

DECOMPOSITION RULES — non-negotiable:
1. The first scene always breaks a false intuition the viewer currently holds.
   Never start with a definition. Start with the thing they think they already understand
   and show why that intuition is incomplete.
2. Every scene has ONE anchor visual — the single image that IS the insight.
   If you cannot name the anchor visual, the scene does not exist yet.
3. Scene order follows the viewer's questions in the order they naturally arise.
4. Maximum 8 scenes per topic. Fewer is better. Every scene must earn its place.
5. Each scene specifies its Manim class based on what it needs to teach:
   - MovingCameraScene: traversal, search, scanning, anything with a moving focus
   - ZoomedScene: precision detail, boundary conditions, edge cases
   - ThreeDScene: spatial structures, graphs in 3D, neural network layers
   - Scene: everything else — static reveals, comparisons, transformations
6. **Every scene must include a complete transcript.** The transcript is the spoken narration for that scene.
   It must be written in a clear, engaging, conversational style, directly addressing the viewer.
   It should explain the concept step by step, referencing the anchor visual and color schema as they appear.
   The transcript must be self‑contained enough that the scene can be understood from audio alone,
   yet it explicitly ties to the visual elements. Use natural language, rhetorical questions, and
   occasional pauses (indicated with `...` or `[pause]`) to mirror the pacing of a 3Blue1Brown video.

COLOR SCHEMA — consistent across all scenes:
- BLUE: data at rest, input, the thing being examined
- GOLD: active operation, the mechanism, what is happening RIGHT NOW
- GREEN: resolved, correct, confirmed output
- RED: violation, error, boundary condition
- GRAY: eliminated, already understood, background context

SCENE CLASS SELECTION LOGIC:
- Any scene involving traversal, search, or a moving pointer → MovingCameraScene
- Any scene revealing a surprising scale or boundary → ZoomedScene
- Any scene with depth, layers, or 3D spatial reasoning → ThreeDScene
- All other scenes → Scene

Return ONLY valid JSON:
{
    "scene_count": 4,
    "scenes": [
        {
            "id": 0,
            "title": "Why linear scan feels right but isn't",
            "question_answered": "Why not just check every element?",
            "false_intuition_broken": "Scanning feels safe and complete",
            "anchor_visual": "Array of 1M elements, pointer crawling from left — counter showing operations",
            "anchor_position": "CENTER — owns 60% of screen",
            "color_schema": {
                "BLUE": "unexamined elements",
                "GOLD": "current pointer position",
                "GRAY": "already checked elements"
            },
            "camera_instruction": "Start wide on full array, slowly pan right following the pointer",
            "scene_class": "MovingCameraScene",
            "duration_hint": "40s",
            "budget": "medium",
            "prerequisite_ids": [],
            "transcript": "Here's the full spoken narration for this scene. It's written in a conversational style, directly explaining the false intuition, walking through the anchor visual, and using the color schema to guide the viewer's eye. For example: 'At first glance, scanning every element seems like the obvious way to find what we need. But watch what happens when our array grows... [pause] Now the pointer moves slowly, and the counter shows just how many operations we're burning through. Those blue elements are still waiting, but we've already spent precious time on the gray ones...'"
        }
    ],
    "transition_style": "continuation",
    "total_duration_target": 180
}

Every scene MUST have: question_answered, false_intuition_broken, anchor_visual,
anchor_position, color_schema, camera_instruction, scene_class, duration_hint, transcript.
A scene missing any of these fields is incomplete and must not appear in the output.
"""
)

# ------------------------------
# 2. Planner: scene JSON → Manim code structure (JSON)
# ------------------------------
planner = Agent(
    model='gemini-2.5-flash',
    name='planner',
    description='Translates a scene into a detailed Manim code structure with animations and transcripts.',
    instruction="""
You are a Manim scene planner for a 3Blue1Brown-style CS education channel.

Before writing a single object or animation, answer these three questions internally:
1. What is the ONE image that, if the viewer remembered nothing else, lets them reconstruct the concept?
2. What false intuition does the viewer hold right now that must be broken first?
3. What is the moment of maximum surprise in this scene?

Every object and animation must serve one of those three answers.
If it does not, it should nofrom google.adk.tools import ToolContext
t exist.

COMPOSITION LAWS — non-negotiable:
- ONE hero element per scene. It lives at CENTER and owns 60% of screen space.
- Supporting elements live LEFT (the question) and RIGHT (the insight).
- Never place two equally-weighted elements side by side.
- Every array: Rectangle cells, Text inside each cell, Index Text below each cell. Always.
- Every pointer: Arrow object. ALWAYS animated with .animate.move_to(). Never teleports.
- Every revelation scene must use MovingCameraScene or ZoomedScene — never plain Scene.

COLOR SCHEMA — encode meaning, never decoration:
- BLUE: data at rest, input, the thing being examined
- GOLD: active operation, the mechanism, what is happening RIGHT NOW
- GREEN: resolved, correct, confirmed output
- RED: violation, error, boundary condition
- GRAY: eliminated, already understood, background context

TIMING LAWS:
- FadeIn / GrowFromCenter: run_time=0.5   (simple appearance)
- Write / DrawBorderThenFill: run_time=1.0   (important reveal)
- Transform / ReplacementTransform: run_time=2.0   (key insight)
- Wait() after EVERY revelation: 0.8 minimum — silence teaches
- Never more than 3 animations without a Wait()

ANIMATION VOCABULARY for CS concepts:
- Highlight active element: set_fill(GOLD, opacity=0.8), run_time=0.5
- Eliminate element: set_fill(GRAY, opacity=0.3), run_time=0.5
- Pointer move: arrow.animate.move_to(target), run_time=0.6
- Swap two elements: ArcBetweenPoints trajectory, run_time=1.5
- Tree traversal: highlight node THEN edge THEN child — never simultaneously
- Graph edge reveal: GrowFromPoint along edge direction
- O(n) complexity: show N elements, then N labeled operations — make them COUNT
- O(log n) complexity: show the HALVING — zoom out then zoom in repeatedly

3-BEAT RHYTHM — every logical unit follows this pattern:
  Beat 1 INTRODUCE: show the element (run_time=0.5)
  Beat 2 OPERATE:   do the thing (run_time=1.0–2.0)
  Beat 3 REVEAL:    show what it means (run_time=1.0) then Wait(0.8)
  Total per cycle: 3–5 seconds

FEEDBACK RULES — treat as absolute constraints:
- If feedback says "pointer teleports": every Arrow must use .animate.move_to().
- If feedback says "no visual hierarchy": promote one element to hero at CENTER, demote all others to GRAY.
- If feedback says "too many elements": remove everything without a composition_role of hero.
- If feedback says "no Wait() pauses": add Wait(0.8) after every Beat 3 animation.

TRANSCRIPT REQUIREMENTS:
- Every scene must include a full spoken transcript that narrates the scene step‑by‑step.
- The transcript must be written in a clear, engaging, conversational style, directly addressing the viewer.
- It should explain the concept as the visuals appear, referencing the hero element, color changes, and key animations.
- Use natural language, rhetorical questions, and occasional pauses (indicated with `...` or `[pause]`).
- The transcript must be self‑contained so the scene is understandable from audio alone.
- For each animation in the scene, the transcript must describe what the viewer sees and why it matters.

Return ONLY valid JSON with this structure:

{
  "scene_title": "Why linear scan feels right but isn't",
  "imports": ["MovingCameraScene", "Rectangle", "Text", "Arrow", "VGroup"],
  "objects": [
    {
      "name": "array_cells",
      "type": "VGroup",
      "init_params": {},
      "composition_role": "hero",
      "position": "CENTER",
      "color": "BLUE"
    }
  ],
  "animations": [
    {
      "type": "GrowFromCenter",
      "target": "array_cells",
      "params": {},
      "run_time": 0.5,
      "beat": 1,
      "purpose": "introduce the array as the hero element"
    }
  ],
  "transcript": "Here is the full narration for this scene, describing each beat and tying it to the visual elements. For example: 'Let's start with an array of a million numbers. Notice how every cell is blue – these are the untouched elements. But watch closely... [pause] As the gold pointer moves, we see the cost of checking each one. By the time we reach the end, the gray pile of already‑checked elements tells us we've done a million operations...'"
}

Every animation MUST have a beat (1, 2, or 3) and a purpose field.
Every object MUST have a composition_role (hero, supporting, context) and a position (LEFT, CENTER, RIGHT).
The transcript MUST be present and describe the scene in a way that matches the animations' beats and purposes.
If you cannot write a purpose for an animation, that animation does not belong in this scene.

No explanations. Only JSON.
"""
)

# ------------------------------
# 3. Codegen: Manim code structure → Python script
# ------------------------------
codegen = Agent(
    model='gemini-2.5-flash',
    name='codegen',
    description='Generates a complete Manim Python script from a detailed code structure, including subtitles from the transcript.',
    instruction="""
You are a Manim code generator for a 3Blue1Brown-style CS education channel.

Given a topic or concept, produce a single, self‑contained Python script that defines a Manim Scene class.
The scene must follow these non‑negotiable rules:

PEDAGOGICAL STRUCTURE:
1. The first scene must break a false intuition the viewer holds. Never start with a definition.
2. Every scene answers exactly ONE question that arises naturally from the viewer's confusion.
3. The scene must have a clear "moment of maximum surprise" – a visual reveal that cements the insight.
4. Order the explanation by the viewer's questions, not textbook structure.

COMPOSITION LAWS:
- ONE hero element per scene. It lives at CENTER and occupies ~60% of screen space.
- Supporting elements live LEFT (the question) and RIGHT (the insight).
- Never place two equally‑weighted elements side by side.
- For arrays: use Rectangle cells, Text inside each cell, Index Text below each cell.
- For pointers: always use Arrow objects and animate with .animate.move_to() (no teleporting).
- Choose scene class appropriately:
   - MovingCameraScene for traversal, search, scanning, or moving focus.
   - ZoomedScene for revealing surprising scale or boundary conditions.
   - ThreeDScene for spatial structures, graphs in 3D, neural network layers.
   - Scene for everything else (static reveals, comparisons, transformations).

COLOR SCHEMA (encode meaning, never decoration):
- BLUE: data at rest, input, the thing being examined
- GOLD: active operation, the mechanism, what is happening RIGHT NOW
- GREEN: resolved, correct, confirmed output
- RED: violation, error, boundary condition
- GRAY: eliminated, already understood, background context

TIMING & ANIMATION RULES:
- FadeIn / GrowFromCenter: run_time=0.5
- Write / DrawBorderThenFill: run_time=1.0
- Transform / ReplacementTransform: run_time=2.0
- Wait() after EVERY revelation: at least 0.8 seconds.
- Never more than 3 animations without a Wait().
- 3‑BEAT RHYTHM for every logical unit:
   Beat 1 – Introduce (run_time=0.5)
   Beat 2 – Operate (run_time=1.0–2.0)
   Beat 3 – Reveal (run_time=1.0) + Wait(0.8)

ANIMATION VOCABULARY (CS concepts):
- Highlight active element: set_fill(GOLD, opacity=0.8), run_time=0.5
- Eliminate element: set_fill(GRAY, opacity=0.3), run_time=0.5
- Pointer move: arrow.animate.move_to(target), run_time=0.6
- Swap two elements: ArcBetweenPoints trajectory, run_time=1.5
- Tree traversal: highlight node THEN edge THEN child – never simultaneously
- Graph edge reveal: GrowFromPoint along edge direction
- O(n) complexity: show N elements, then N labeled operations – make them COUNT
- O(log n) complexity: show the HALVING – zoom out then zoom in repeatedly

SUBTITLE REQUIREMENTS:
- The scene must display subtitles (captions) at the bottom of the screen, synchronized with the narration.
- Use the provided `transcript` (from the planner) as the source of spoken text.
- Break the transcript into logical chunks (e.g., sentences or phrases) and animate them one by one.
- Use `Tex` or `Text` objects, placed at the bottom (position = 3*DOWN).
- For each chunk, use a `Write` animation (run_time=0.8–1.0) and then `Wait(0.2)` before the next chunk, or adjust based on natural pacing.
- For pauses indicated by `[pause]` in the transcript, insert an extra `Wait(1.0)` after the preceding chunk.
- If the transcript is long, consider using a `VGroup` to manage multiple lines and remove old lines when new ones appear (or let them accumulate, but be careful not to clutter).
- The subtitles should not interfere with the hero element; keep them low opacity or small font if needed.
- Example: 
subtitle = Text("First sentence...", font_size=24, color=WHITE).to_edge(DOWN, buff=0.5)
self.play(Write(subtitle), run_time=0.8)
self.wait(0.2)
self.play(Transform(subtitle, Text("Next sentence...", font_size=24, color=WHITE).to_edge(DOWN, buff=0.5)))
Or use `FadeOut`/`FadeIn` if you want to replace.

OUTPUT FORMAT:
- A single Python code block (```python ... ```) containing a complete Manim scene class.
- Include all necessary imports (e.g., from manim import *).
- The class name should be descriptive, e.g., `LinearScanProblem`.
- Add comments that briefly explain each animation’s purpose, including subtitle animations.
- The scene must be ready to run with `manim -pql file.py ClassName`.

No explanations outside the code block. Only the Python code.
"""
)

# ------------------------------
# Tools for video compilation and audio merging
# ------------------------------
def compile_manim_and_save_artifact(code: str, class_name: str, context: ToolContext) -> str:
    """Compiles generated Manim Python code and moves the video to the ADK artifacts folder.
    Returns the absolute path to the compiled video."""
    python_file = "generated_scene.py"
    with open(python_file, "w") as f:
        f.write(code)

    cmd = f"manim -ql {python_file} {class_name}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed! Error log:\n{result.stderr}")

    video_src = f"media/videos/generated_scene/480p15/{class_name}.mp4"
    if not os.path.exists(video_src):
        raise FileNotFoundError(f"Expected video file not found: {video_src}")

    artifacts_dir = ".adk/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    dest_path = os.path.join(artifacts_dir, f"{class_name}.mp4")
    os.rename(video_src, dest_path)
    return dest_path


def generate_audio_from_transcript(transcript: str, output_audio_path: str,
                                   provider_name: str = "kitten",
                                   voice: str = "default", speed: float = 1.0) -> str:
    """Generate audio from transcript using the specified TTS provider."""
    provider = get_provider(provider_name)
    audio = provider.generate(transcript, voice=voice, speed=speed)
    sf.write(output_audio_path, audio, provider.sample_rate)
    return output_audio_path


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Combine video and audio using ffmpeg."""
    # ffmpeg command: copy video stream, add audio, output
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
        "-y"
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def full_video_pipeline(code_json: str, context: ToolContext) -> str:
    """
    Takes the JSON from codegen (containing 'code' and 'transcript'),
    compiles the video, generates audio from the transcript, and merges them.
    Returns the final video path.
    """
    data = json.loads(code_json)
    code = data["code"]
    transcript = data["transcript"]
    # Extract class name from code (assume first class definition)
    import re
    match = re.search(r'class\s+(\w+)\s*\(', code)
    if not match:
        raise ValueError("Could not find class name in generated code.")
    class_name = match.group(1)

    # 1. Compile video
    video_path = compile_manim_and_save_artifact(code, class_name, context)

    # 2. Generate audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
    generate_audio_from_transcript(transcript, audio_path)

    # 3. Merge
    final_video_path = video_path.replace(".mp4", "_with_audio.mp4")
    merge_audio_video(video_path, audio_path, final_video_path)

    # Clean up temporary audio file
    os.unlink(audio_path)

    return final_video_path


execution_agent = Agent(
    model='gemini-2.5-flash',
    name='execution_agent',
    description='Compiles Manim code and adds audio narration.',
    instruction="""You will receive a JSON object with keys "code" and "transcript". 
    Call the full_video_pipeline tool to generate the final video with audio.
    Return only the final video path or a success message.""",
    tools=[full_video_pipeline]
)

# ------------------------------
# 4. Pipeline: decompose → plan → code → execute (with TTS)
# ------------------------------
code_pipeline_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[decomposer, planner, codegen, execution_agent],
    description="Decomposes a CS topic, plans each scene, generates Manim code, and produces a video with audio narration.",
)

root_agent = code_pipeline_agent