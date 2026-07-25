"""Solver agent: answers a question using only retrieved chunks, via the Claude API."""

import anthropic
from pydantic import BaseModel

from app.agents.errors import ensure_api_key
from app.models import Chunk, Citation

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """You are a study assistant answering questions using only the provided \
course material excerpts. Rules:
- Answer only using the information in the provided context. Do not use outside knowledge.
- If the context does not contain enough information to answer, say so explicitly \
instead of guessing.
- In `used_chunk_ids`, list the ids of exactly the chunks you actually relied on to \
write the answer. Leave it empty if you couldn't answer from the context."""


class _StructuredAnswer(BaseModel):
    answer: str
    used_chunk_ids: list[str]


def _build_context(chunks: list[Chunk]) -> str:
    blocks = [
        f"[chunk_id: {c.chunk_id} | document: {c.document_name} | page: {c.page_number} "
        f"| heading: {c.heading or 'n/a'}]\n{c.text}"
        for c in chunks
    ]
    return "\n\n---\n\n".join(blocks)


def answer_question(question: str, chunks: list[Chunk]) -> dict:
    """Answer `question` using only `chunks` as context.

    Returns {"answer": str, "citations": list[Citation]}.
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
                "content": f"Context:\n\n{context}\n\nQuestion: {question}",
            }
        ],
        output_format=_StructuredAnswer,
    )

    structured = response.parsed_output
    chunks_by_id = {c.chunk_id: c for c in chunks}
    citations = [
        Citation(
            document_name=chunks_by_id[cid].document_name,
            page_number=chunks_by_id[cid].page_number,
            heading=chunks_by_id[cid].heading,
        )
        for cid in structured.used_chunk_ids
        if cid in chunks_by_id
    ]

    return {"answer": structured.answer, "citations": citations}
