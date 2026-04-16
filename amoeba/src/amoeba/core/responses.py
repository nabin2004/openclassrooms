"""Extract assistant text from LiteLLM / OpenAI-style chat completion objects."""


def _text_from_thinking_blocks(msg, _get) -> str:
    """LiteLLM/providers may attach text in `thinking_blocks` instead of `content`."""
    tb = _get(msg, "thinking_blocks")
    if not tb:
        return ""
    parts: list[str] = []
    if isinstance(tb, list):
        for item in tb:
            if isinstance(item, dict):
                t = item.get("text")
                if t is None and isinstance(item.get("content"), str):
                    t = item.get("content")
                if t is not None:
                    parts.append(str(t))
            elif isinstance(item, str):
                parts.append(item)
    elif isinstance(tb, str) and tb.strip():
        return tb.strip()
    return "".join(parts).strip()


def completion_message_text(response) -> str:
    """
    Return the assistant text from a chat completion. Handles None content
    (some providers or tool-style replies) and simple multimodal text blocks.
    """
    try:
        choices0 = response.choices[0]
    except (AttributeError, IndexError, TypeError):
        return ""
    msg = getattr(choices0, "message", None)
    if msg is None and isinstance(choices0, dict):
        msg = choices0.get("message")

    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    content = _get(msg, "content", None)
    out = ""
    if content is None:
        # Tool / function call replies can have content=None; the payload lives
        # under tool_calls/function_call arguments.
        tool_calls = _get(msg, "tool_calls", None)
        if isinstance(tool_calls, list) and tool_calls:
            parts: list[str] = []
            for tc in tool_calls:
                fn = None
                if isinstance(tc, dict):
                    fn = tc.get("function")
                else:
                    fn = getattr(tc, "function", None)
                if fn is None:
                    continue
                args = fn.get("arguments") if isinstance(fn, dict) else getattr(fn, "arguments", None)
                if args:
                    parts.append(str(args))
            if parts:
                out = "\n".join(parts).strip()

        if not out:
            fn_call = _get(msg, "function_call", None)
            if fn_call:
                args = fn_call.get("arguments") if isinstance(fn_call, dict) else getattr(fn_call, "arguments", None)
                if args:
                    out = str(args).strip()
    elif isinstance(content, str):
        out = content.strip()
    elif isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                t = block.get("text")
                if t is None and isinstance(block.get("content"), str):
                    t = block.get("content")
                if t is not None:
                    parts.append(str(t))
            elif isinstance(block, str):
                parts.append(block)
        out = "".join(parts).strip()
    else:
        out = str(content).strip()

    if not out and msg is not None:
        out = _text_from_thinking_blocks(msg, _get)

    # Some providers put chain-of-thought in `reasoning_content` and the final answer in
    # `content`. Only use reasoning when it plausibly contains JSON (avoid prose-only CoT).
    if not out and msg is not None:
        from amoeba.utils import _extract_first_json as _extract_json_blob

        for key in ("reasoning_content", "reasoning", "thinking"):
            v = _get(msg, key)
            if not isinstance(v, str) or not v.strip():
                continue
            s = v.strip()
            usable = s.lstrip().startswith(("{", "[")) or _extract_json_blob(s) is not None
            if not usable:
                continue
            out = s
            break

    # Legacy completions / alternate shapes
    if not out:
        if isinstance(choices0, dict):
            lt = choices0.get("text")
        else:
            lt = getattr(choices0, "text", None)
        if isinstance(lt, str) and lt.strip():
            out = lt.strip()

    # Rare: provider puts assistant string on the response object
    if not out:
        rt = getattr(response, "content", None)
        if isinstance(rt, str) and rt.strip():
            out = rt.strip()

    return out
