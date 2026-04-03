"""Normalize LiteLLM / OpenAI-style chat completion bodies."""


def completion_message_text(response) -> str:
    """
    Return the assistant text from a chat completion. Handles None content
    (some providers or tool-style replies) and simple multimodal text blocks.
    """
    try:
        msg = response.choices[0].message
    except (AttributeError, IndexError, TypeError):
        return ""
    content = getattr(msg, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                t = block.get("text")
                if t is not None:
                    parts.append(str(t))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts).strip()
    return str(content).strip()
