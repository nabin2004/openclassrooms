

def strip_markdown_code_blocks(text: str) -> str:
    """
    Removes markdown code block wrappers like ``` or ```json from a string.
    """
    text = text.strip()

    if not text.startswith("```"):
        return text

    parts = text.split("```")

    # Typical case: ["", "json\n{...}", ""]
    if len(parts) >= 2:
        content = parts[1].strip()

        # Remove optional language tag (e.g., "json")
        first_newline = content.find("\n")
        if first_newline != -1:
            maybe_lang = content[:first_newline].strip().lower()
            if maybe_lang in {"json", "python", "js"}:
                content = content[first_newline + 1 :]

        return content.strip()

    return text