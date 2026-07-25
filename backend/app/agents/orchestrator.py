"""Ties the solver, verifier, and reflection agents into a single pipeline:
retrieve -> solve -> verify -> (optionally retry once with a revised query) ->
score confidence."""

from app.agents.confidence import compute_confidence
from app.agents.reflection import reflect
from app.agents.solver import answer_question
from app.agents.verifier import verify_answer
from app.models import Chunk
from app.retrieval.store import search as search_chunks

MAX_RETRIES = 1


def _retrieve(query: str, top_k: int) -> tuple[list[Chunk], list[float]]:
    results = search_chunks(query, top_k=top_k)
    chunks = [
        Chunk(
            chunk_id=r["chunk_id"],
            document_name=r["document_name"],
            page_number=r["page_number"],
            heading=r["heading"],
            text=r["text"],
        )
        for r in results
    ]
    scores = [r["similarity"] for r in results]
    return chunks, scores


def run_pipeline(question: str, top_k: int = 5) -> dict:
    """Run the solver -> verifier -> reflection -> confidence pipeline for `question`.

    Returns {"answer": str, "citations": list[Citation], "verification": dict,
    "retried": bool, "confidence": int, "confidence_breakdown": list[str]}.
    Solves at most twice total (initial attempt + one retry).
    """
    chunks, scores = _retrieve(question, top_k)
    result = answer_question(question, chunks)
    verification = verify_answer(question, result["answer"], chunks)

    retried = False
    for _ in range(MAX_RETRIES):
        reflection = reflect(question, result["answer"], verification)
        if not reflection["retry"] or not reflection["revised_query"]:
            break

        retried = True
        chunks, scores = _retrieve(reflection["revised_query"], top_k)
        result = answer_question(question, chunks)
        verification = verify_answer(question, result["answer"], chunks)

    confidence = compute_confidence(
        scores, verification, retried, has_citations=bool(result["citations"])
    )

    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "verification": verification,
        "retried": retried,
        "confidence": confidence["confidence"],
        "confidence_breakdown": confidence["breakdown"],
    }
