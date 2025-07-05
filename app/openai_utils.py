"""Utility functions for OpenAI operations."""


def summarize(text: str) -> str:
    """Return a short summary placeholder for the given text."""
    if not text:
        return ""
    # Placeholder summarization logic
    return text[:100]

