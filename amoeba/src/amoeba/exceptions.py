"""Structured errors for Amoeba. Prefer these over raw Exception / ValueError."""


class AmoebaError(Exception):
    """
    Base for Amoeba failures. Carries optional context for logs and UI.

    ``user_message`` is a stable, end-user-oriented string; ``str(exc)``
    remains the developer-oriented message.
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict | None = None,
        retryable: bool = False,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = dict(context or {})
        self.retryable = retryable
        self.user_message = user_message if user_message is not None else message

    def format_detail(self) -> str:
        lines = [f"{type(self).__name__}: {self.message}"]
        if self.context:
            lines.append("Context:")
            for key, val in list(self.context.items())[:30]:
                text = str(val)
                if len(text) > 600:
                    text = text[:600] + "..."
                lines.append(f"  - {key}: {text}")
        return "\n".join(lines)


class ConfigurationError(AmoebaError):
    """Invalid setup (missing schema, bad config)."""


class LLMError(AmoebaError):
    """LiteLLM / provider call failed or produced an unusable result."""


class LLMTimeoutError(LLMError):
    def __init__(
        self,
        message: str = "LLM request timed out",
        *,
        context: dict | None = None,
        user_message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            context=context,
            retryable=True,
            user_message=user_message,
        )


class LLMRateLimitError(LLMError):
    def __init__(
        self,
        message: str = "LLM rate limit hit",
        *,
        context: dict | None = None,
        user_message: str | None = "The model provider rate limit was reached. Try again shortly.",
    ) -> None:
        super().__init__(
            message,
            context=context,
            retryable=True,
            user_message=user_message,
        )


class LLMResponseError(LLMError):
    """Response missing text, malformed envelope, or empty when content was required."""


class JSONParseError(AmoebaError):
    """Fence-stripped text is not valid JSON."""


class StructuredOutputError(AmoebaError):
    """JSON parsed but does not match the expected Pydantic schema."""


class SubprocessError(AmoebaError):
    """External command failed (non-zero exit, timeout, or OS error)."""
