"""Shared error types and helpers for the agent pipeline."""

import os


class MissingAPIKeyError(RuntimeError):
    """Raised when ANTHROPIC_API_KEY is not configured."""


def ensure_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise MissingAPIKeyError(
            "ANTHROPIC_API_KEY is not set. Get a key from console.anthropic.com "
            "and add it to backend/.env as ANTHROPIC_API_KEY=sk-ant-... "
            "(copy backend/.env.example to backend/.env if you haven't already)."
        )
