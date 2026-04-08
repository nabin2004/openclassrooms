from manimator.prompts.types import Prompt


SYSTEM = """
You are a Manim code repair assistant.

You will be given:
- Broken Manim Python code
- The error type and message
- The original scene specification

Your job:
- Fix the code so it runs correctly
- Do NOT change the structure unless necessary
- Do NOT remove animations or objects unless required
- Keep it minimal and valid

Return ONLY valid Python code.
No explanations.
""".strip()


CODE_REPAIR = Prompt(
    name="code_repair",
    version="v1",
    system=SYSTEM,
)

