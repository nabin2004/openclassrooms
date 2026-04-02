from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext
from pathlib import Path
from typing import Any
import importlib
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

try:
    _skills_module = importlib.import_module("google.adk.skills")
    load_skill_from_dir = getattr(_skills_module, "load_skill_from_dir")
    models = getattr(_skills_module, "models")
    skill_toolset = importlib.import_module("google.adk.tools.skill_toolset")
    SKILLS_API_AVAILABLE = True
except ImportError:
    load_skill_from_dir = None
    models = None
    skill_toolset = None
    SKILLS_API_AVAILABLE = False


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = re.sub(r"^```(?:json|python|manim-code)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _decode_json_like_string(value: str) -> str:
    """Decode common escaped sequences produced inside JSON-like code fields."""
    if not value:
        return value
    return (
        value
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
    )


def _extract_quoted_field(raw: str, key: str) -> str | None:
    """Extract a quoted string field from JSON-like text even if invalid JSON."""
    key_match = re.search(rf'"{re.escape(key)}"\s*:\s*"', raw)
    if not key_match:
        return None

    i = key_match.end()
    chunks: list[str] = []
    escaped = False
    while i < len(raw):
        ch = raw[i]
        if escaped:
            chunks.append("\\" + ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            return _decode_json_like_string("".join(chunks))
        else:
            chunks.append(ch)
        i += 1
    return None


def _extract_manim_payload(payload: str | dict) -> tuple[str, list[str]]:
    """Extract code and class list from structured payload or fenced code output."""
    if isinstance(payload, dict):
        code = str(payload.get("code", "")).strip()
        class_names = payload.get("class_names") or []
    else:
        raw = str(payload).strip()
        if not raw:
            raise ValueError("Received empty payload for Manim compilation.")

        raw = re.sub(r"^\s*\[[^\]]+\]\s*:\s*", "", raw, count=1)
        candidate = _strip_code_fences(raw)

        code = ""
        class_names: list[str] = []

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                code = str(parsed.get("code", "")).strip()
                class_names = [str(x) for x in parsed.get("class_names", []) if str(x).strip()]
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(candidate)
                if isinstance(parsed, dict):
                    code = str(parsed.get("code", "")).strip()
                    class_names = [str(x) for x in parsed.get("class_names", []) if str(x).strip()]
            except (SyntaxError, ValueError):
                code_from_field = _extract_quoted_field(raw, "code")
                if code_from_field is not None:
                    code = code_from_field.strip()
                else:
                    code_block = re.search(r"```(?:python)?\s*(.*?)\s*```", raw, flags=re.IGNORECASE | re.DOTALL)
                    code = code_block.group(1).strip() if code_block else raw

    if not code:
        raise ValueError("Payload must include non-empty Manim Python code.")

    code = _strip_code_fences(_decode_json_like_string(code))

    # Guardrail: if the extracted text still looks like a payload wrapper, fail fast.
    if re.match(r"^\s*\{\s*\"?(file_name|class_names|primary_class|code)\"?\s*:", code):
        raise ValueError("Extraction error: expected raw Python code, got a serialized payload wrapper.")

    if not class_names:
        class_names = re.findall(r"class\s+(\w+)\s*\(", code)

    if not class_names:
        raise ValueError("Could not infer any scene class names from payload code.")

    return code, class_names


def compile_manim_payload(payload: str, context: ToolContext | None = None) -> str:
    """Compile generated Manim code and return rendered video artifact paths."""
    code, class_names = _extract_manim_payload(payload)

    artifacts_dir = Path(".adk") / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Validate syntax before invoking Manim for clearer boundary-failure diagnostics.
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise SyntaxError(f"Generated code failed Python syntax validation: {exc}") from exc

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    debug_source_path = artifacts_dir / f"generated_scene_{timestamp}.py"
    debug_source_path.write_text(code, encoding="utf-8")

    rendered: list[str] = []
    with tempfile.TemporaryDirectory(prefix="manimator_compile_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        source_path = tmp_path / "generated_scene.py"
        source_path.write_text(code, encoding="utf-8")

        media_dir = tmp_path / "media"
        for class_name in class_names:
            cmd = [
                sys.executable,
                "-m",
                "manim",
                "-pql",
                str(source_path),
                class_name,
                "--media_dir",
                str(media_dir),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Compilation failed for {class_name}. Source: {debug_source_path}.\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )

            matches = list(media_dir.rglob(f"{class_name}.mp4"))
            if not matches:
                raise FileNotFoundError(f"Compiled video not found for scene class: {class_name}")

            video_src = max(matches, key=lambda p: p.stat().st_mtime)
            dest = artifacts_dir / f"{class_name}.mp4"
            shutil.copy2(video_src, dest)
            rendered.append(str(dest.resolve()))

    return json.dumps(
        {
            "video_paths": rendered,
            "compiled_classes": class_names,
            "source_path": str(debug_source_path.resolve()),
        },
        ensure_ascii=True,
    )


def _markdown_file_to_skill(md_file: Path) -> Any | None:
    """Build an inline Skill object from a markdown file."""
    if not SKILLS_API_AVAILABLE or models is None:
        return None

    content = md_file.read_text(encoding="utf-8").strip()
    if not content:
        return None

    first_line = next((line.strip("# ").strip() for line in content.splitlines() if line.strip()), "")
    description = first_line or f"Skill loaded from {md_file.name}"
    skill_name = md_file.stem.lower().replace("_", "-").replace(" ", "-")

    return models.Skill(
        frontmatter=models.Frontmatter(
            name=skill_name,
            description=description,
        ),
        instructions=content,
    )


def _load_skills(skills_dir: Path) -> list[Any]:
    """Load skills from directory-based specs and markdown files."""
    loaded: list[Any] = []
    if not skills_dir.exists() or not SKILLS_API_AVAILABLE or load_skill_from_dir is None:
        return loaded

    # Preferred format: one directory per skill with SKILL.md
    for child in sorted(skills_dir.iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            loaded.append(load_skill_from_dir(child))

    # Backward-compatible format: plain markdown skill files.
    for md_file in sorted(skills_dir.glob("*.md")):
        if md_file.name.lower() in {"skills.md", "readme.md", "skill.md"}:
            continue
        inline_skill = _markdown_file_to_skill(md_file)
        if inline_skill is not None:
            loaded.append(inline_skill)

    return loaded


def _load_skill_guidance(skills_dir: Path) -> str:
    """Fallback guidance text for runtimes without experimental skills APIs."""
    if not skills_dir.exists():
        return ""

    orchestrator_file = skills_dir / "skills.md"
    if orchestrator_file.exists():
        return orchestrator_file.read_text(encoding="utf-8").strip()

    snippets: list[str] = []
    for md_file in sorted(skills_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        headline = next((line.strip("# ").strip() for line in text.splitlines() if line.strip()), md_file.stem)
        snippets.append(f"- {md_file.name}: {headline}")

    return "\n".join(snippets)


SKILLS_DIR = Path(__file__).parent / "skills"
LOADED_SKILLS = _load_skills(SKILLS_DIR)
FALLBACK_SKILL_GUIDANCE = _load_skill_guidance(SKILLS_DIR)

agent_tools = []
has_skill_toolset = bool(SKILLS_API_AVAILABLE and LOADED_SKILLS and skill_toolset is not None)
if has_skill_toolset:
    agent_tools.append(skill_toolset.SkillToolset(skills=LOADED_SKILLS))
agent_tools.append(compile_manim_payload)

agent_instruction = (
    "Answer user questions to the best of your knowledge and use loaded skills when relevant. "
    "When Stage 3 produces Manim code, call compile_manim_payload to render videos."
)

if not has_skill_toolset and FALLBACK_SKILL_GUIDANCE:
    agent_instruction = (
        "Answer user questions to the best of your knowledge. "
        "This runtime does not expose the experimental ADK Skills APIs, so follow the local skills guidance below as procedural instructions.\n\n"
        f"{FALLBACK_SKILL_GUIDANCE}"
    )


root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions using loaded ADK skills.',
    instruction=agent_instruction,
    tools=agent_tools,
)
