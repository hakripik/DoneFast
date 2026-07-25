"""Verifier agent: checks whether a solver's answer is actually grounded in the
retrieved chunks. Never re-answers the question or introduces outside knowledge —
it only judges the answer against the given evidence."""

import anthropic
from pydantic import BaseModel

from app.agents.errors import ensure_api_key
from app.models import Chunk

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are a strict fact-checker. You will be given a question, an \
answer someone produced, and the source excerpts that answer was supposed to be \
based on. Your only job is to judge whether the answer is actually supported by \
those excerpts — you are not answering the question yourself, and you must not use \
any outside knowledge of your own.

Check for things like:
- Claims in the answer that are not stated anywhere in the excerpts.
- Assumptions the answer relies on that the excerpts don't state.
- Citations or details that don't match what the cited excerpt actually says.
- The answer being confidently wrong given what the excerpts say.

If the answer sticks to what the excerpts actually support (including cases where \
the answer correctly says it doesn't know), mark it as supported. Be specific in \
`issues` — name the exact unsupported claim or assumption, don't just say \
"partially supported"."""


class _StructuredVerification(BaseModel):
    supported: bool
    issues: list[str]
    notes: str


def _build_context(chunks: list[Chunk]) -> str:
    blocks = [
        f"[chunk_id: {c.chunk_id} | document: {c.document_name} | page: {c.page_number} "
        f"| heading: {c.heading or 'n/a'}]\n{c.text}"
        for c in chunks
    ]
    return "\n\n---\n\n".join(blocks)


def verify_answer(question: str, answer: str, chunks: list[Chunk]) -> dict:
    """Check `answer` against `chunks`.

    Returns {"supported": bool, "issues": list[str], "notes": str}.
    Raises MissingAPIKeyError if ANTHROPIC_API_KEY is not set.
    """
    ensure_api_key()

    client = anthropic.Anthropic()
    context = _build_context(chunks)

    response = client.messages.parse(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Source excerpts:\n\n{context}\n\n"
                    f"Question: {question}\n\n"
                    f"Answer to check: {answer}"
                ),
            }
        ],
        output_format=_StructuredVerification,
    )

    structured = response.parsed_output
    return {
        "supported": structured.supported,
        "issues": structured.issues,
        "notes": structured.notes,
    }
