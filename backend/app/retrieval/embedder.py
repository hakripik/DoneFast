"""Text embedding, local via sentence-transformers.

Kept behind a single `embed()` function so the rest of the app never
imports sentence-transformers directly — swapping to an API-based embedding
model later only means changing this file.
"""

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returning one vector per text."""
    if not texts:
        return []
    vectors = _get_model().encode(texts, convert_to_numpy=True)
    return vectors.tolist()
