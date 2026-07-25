"""Splits parsed PDF pages into ~300-600 word chunks, preferring sentence
boundaries where convenient, and attaching page/heading metadata.

Chunk boundaries are driven purely by word count. Headings are metadata
attached to whichever chunk they fall in — they never force a chunk break,
so multiple consecutive chunks commonly share the same heading."""

import re

from app.ingestion.parser import ParsedPage
from app.models import Chunk

MIN_CHUNK_WORDS = 300
MAX_CHUNK_WORDS = 600

_WORD_RE = re.compile(r"\S+")
_SENTENCE_END_RE = re.compile(r"[.!?]$")


class _Token:
    def __init__(self, word: str, page_number: int, heading: str | None):
        self.word = word
        self.page_number = page_number
        self.heading = heading


def _tokens_for_page(page: ParsedPage, carried_heading: str | None) -> tuple[list[_Token], str | None]:
    """Split one page's text into word tokens, tagging each with the heading
    active at that point (falling back to the heading carried over from
    earlier pages if this page has none yet)."""
    tokens: list[_Token] = []
    active_heading = carried_heading
    heading_idx = 0
    headings = page.headings

    for match in _WORD_RE.finditer(page.text):
        start = match.start()
        while heading_idx < len(headings) and headings[heading_idx][1] <= start:
            active_heading = headings[heading_idx][0]
            heading_idx += 1
        tokens.append(_Token(match.group(), page.page_number, active_heading))

    return tokens, active_heading


def chunk_pages(pages: list[ParsedPage], document_name: str) -> list[Chunk]:
    """Group word tokens from parsed pages into word-bounded chunks."""
    all_tokens: list[_Token] = []
    carried_heading: str | None = None
    for page in pages:
        page_tokens, carried_heading = _tokens_for_page(page, carried_heading)
        all_tokens.extend(page_tokens)

    chunks: list[Chunk] = []
    current: list[_Token] = []

    def flush():
        if not current:
            return
        chunks.append(
            Chunk(
                chunk_id=f"{document_name}_{len(chunks)}",
                document_name=document_name,
                page_number=current[0].page_number,
                heading=current[0].heading,
                text=" ".join(t.word for t in current),
            )
        )
        current.clear()

    for token in all_tokens:
        current.append(token)

        if len(current) >= MAX_CHUNK_WORDS:
            # Hard cap: split here even mid-sentence, so a section with
            # little/no punctuation can't grow into one giant chunk.
            flush()
        elif len(current) >= MIN_CHUNK_WORDS and _SENTENCE_END_RE.search(token.word):
            # Within the target range and sitting on a sentence boundary —
            # a good, avoidable-mid-sentence-split point.
            flush()

    flush()
    return chunks
