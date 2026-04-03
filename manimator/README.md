# Manimator

Agentic pipeline: intent → scene plan → Manim specs → code → validate → render → optional narration → transcript.

Run it from the **workspace root** (`OpenClassrooms/`) so relative paths like `outputs/` match the pipeline and `manim` media layout.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (0.10+)
- Python **3.14** (see repo `.python-version`)
- **`manim`** on your PATH when you want real renders (not just codegen)
- **`ffmpeg` and `ffprobe`** on your PATH when narration (TTS mux) is enabled
- API keys for your LLM providers (via LiteLLM), usually in a **`.env`** file at the workspace root

## Install (uv only)

From the **repository root** (parent of this `manimator/` folder):

```bash
uv python install 3.14
uv sync --all-packages
```

Editable install with pip (optional, from repo root): `uv pip install -e ./manimator` — requires valid `[tool.setuptools]` in this `pyproject.toml` (never put `packages` under `[project]`).

Optional **text-to-speech** (KittenTTS; large dependency set):

```bash
uv sync --package manimator --extra tts
# or from the root Makefile:
make sync-tts
```

## Environment

- Place **`.env`** next to the workspace `pyproject.toml` (not inside `manimator/`). `manimator.main` loads `PROJECT_ROOT / ".env"`.
- Set models and keys as needed for LiteLLM (for example `GROQ_API_KEY`, `OPENAI_API_KEY`, or provider-specific vars). Planner/decomposer defaults use env vars such as `SCENE_PLANNER_MODEL` / `SCENE_DECOMPOSER_MODEL` where applicable.
- **Narration** (after `make sync-tts` or `uv sync --package manimator --extra tts`):
  - `MANIMATOR_ENABLE_TTS` — unset = auto (on if `kittentts` is installed); `1`/`true` = force on; `0`/`false` = off
  - `KITTEN_TTS_MODEL` — default `KittenML/kitten-tts-nano-0.8`
  - `KITTEN_TTS_VOICE` — default `Jasper`
  - `KITTEN_TTS_SPEED` — default `1.0`
  - `KITTEN_TTS_BACKEND=cuda` — optional GPU backend for KittenTTS

## Run the pipeline (uv)

Always **`cd` to the workspace root** first.

**Recommended** (explicit package context):

```bash
uv run --package manimator python -m manimator.main
```

Use a custom topic (short prompt):

```bash
uv run --package manimator python -m manimator.main -q "Teach me RNNs with visuals"
```

Or a long brief from a file (example: `manimator/query_rnn.txt`):

```bash
uv run --package manimator python -m manimator.main --query-file manimator/query_rnn.txt
```

Equivalent after `uv sync --all-packages` (shared `.venv` already includes manimator):

```bash
uv run python -m manimator.main
```

**Makefile** (also uses uv via `UV_RUN`):

```bash
make test-pipeline
```

Outputs (typical):

- `outputs/delivery/<timestamp>/final.mp4` — **all scenes in order** (normalized + concatenated with ffmpeg)
- `outputs/delivery/<timestamp>/transcript.txt` — same transcript text, **in the same folder** as `final.mp4`
- `outputs/transcript.txt` — copy of the transcript (backward compatibility)
- `outputs/scene_*.mp4` — per-scene renders (when Manim succeeds)
- `outputs/scene_*_narrated.mp4` — per-scene video + TTS (when TTS is enabled and ffmpeg is available)
- `outputs/scene_*_narration.wav` — per-scene WAV intermediates (when TTS runs)

## Tests (uv)

From the workspace root:

```bash
uv run --package manimator -m pytest manimator/tests/audio/test_voiceover.py -q
uv run --package manimator -m pytest manimator/tests/contracts -q
```

Use `-m pytest` so the `manimator` package resolves correctly (avoid shadowing the stdlib `logging` package by running with a bad `PYTHONPATH`).

## Dependency changes

From the workspace root:

```bash
uv add --package manimator <package>
make lock
```

## See also

- Workspace overview: `../README.md`
- Agent testing: `../AGENT_TESTING.md`
- Video limits/config: `../VIDEO_CONFIG_GUIDE.md`
