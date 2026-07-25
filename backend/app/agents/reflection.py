"""Reflection agent: decides what to do with a verifier's judgment. If the answer
looks unsupported, it proposes a broadened/rephrased search query aimed at pulling
in better evidence on a retry — it does not itself re-answer the question."""

import anthropic
from pydantic import BaseModel

from app.agents.errors import ensure_api_key

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are a retrieval-strategy assistant. You will be given a \
question, an answer that was produced for it, and a verifier's judgment of whether \
that answer is actually supported by the retrieved evidence.

Decide whether it's worth retrying retrieval with a different search query:
- If the verifier says the answer is supported, or the issues are minor/cosmetic, \
recommend no retry.
- If the verifier flagged real problems (unsupported claims, mismatched citations, \
missing evidence), recommend a retry and write a revised search query that is more \
likely to retrieve the right evidence — e.g. rephrase using terminology the source \
material would likely use, broaden overly narrow wording, or pull in adjacent terms \
implied by the verifier's issues. The revised query is used for vector similarity \
search, not shown to a person, so keep it a plain, keyword-rich query rather than a \
full sentence."""


class _StructuredReflection(BaseModel):
    retry: bool
    revised_query: str | None
    reason: str


def reflect(question: str, answer: str, verification: dict) -> dict:
    """Decide whether to retry retrieval given the verifier's judgment.

    Returns {"retry": bool, "revised_query": str | None, "reason": str}.
    Raises MissingAPIKeyError if ANTHROPIC_API_KEY is not set.
    """
    ensure_api_key()

    if verification.get("supported"):
        return {
            "retry": False,
            "revised_query": None,
            "reason": "Verifier marked the answer as supported.",
        }

    client = anthropic.Anthropic()

    response = client.messages.parse(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Answer: {answer}\n\n"
                    f"Verifier supported: {verification.get('supported')}\n"
                    f"Verifier issues: {verification.get('issues')}\n"
                    f"Verifier notes: {verification.get('notes')}"
                ),
            }
        ],
        output_format=_StructuredReflection,
    )

    structured = response.parsed_output
    return {
        "retry": structured.retry,
        "revised_query": structured.revised_query,
        "reason": structured.reason,
    }
