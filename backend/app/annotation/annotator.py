"""Writes an annotated copy of a source PDF: a sticky note on each page cited for
a question, plus an appended summary page with the question, answer, confidence,
and the full citation list (including citations from other documents). Never
modifies the original file in backend/uploads/."""

from pathlib import Path

import fitz  # PyMuPDF

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
ANNOTATED_DIR = Path(__file__).resolve().parent.parent.parent / "annotated"

STICKY_NOTE_POINT = fitz.Point(36, 36)  # inside the top-left page margin

# The summary page uses a fixed, generously-sized page (A4) regardless of the
# source PDF's own page size — source pages can be small (e.g. slide decks),
# and PyMuPDF's insert_textbox silently drops ALL text if it overflows the box,
# rather than truncating, so an undersized page can end up with a blank summary.
SUMMARY_PAGE_SIZE = (595, 842) #A4 in points
SUMMARY_MARGIN = 36
MIN_FONT_SIZE = 6


class DocumentNotFoundError(FileNotFoundError):
    """Raised when the requested document isn't in backend/uploads/."""


def _safe_filename(document_name: str) -> str:
    # Strip any directory components so a crafted document_name can't escape
    # UPLOADS_DIR / ANNOTATED_DIR.
    return Path(document_name).name


# PyMuPDF's built-in "helv" font only supports WinAnsi encoding, not the Unicode
# punctuation Claude tends to output (em/en dashes, minus signs, curly quotes) —
# unsupported characters render as garbage rather than raising an error, so text
# drawn on the page (not annotation popups, which support Unicode fine) needs
# to be down-converted first.
_ASCII_REPLACEMENTS = {
    "—": "-",  # em dash
    "–": "-",  # en dash
    "−": "-",  # minus sign
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "…": "...",
}


def _ascii_safe(text: str) -> str:
    for unicode_char, replacement in _ASCII_REPLACEMENTS.items():
        text = text.replace(unicode_char, replacement)
    return text


def _build_summary_text(question: str, ask_response: dict) -> str:
    lines = [
        "Study Assistant — Answer Record",
        "",
        "Question:",
        question,
        "",
        "Answer:",
        ask_response["answer"],
        "",
        f"Confidence: {ask_response['confidence']}%",
        "Confidence breakdown:",
    ]
    lines.extend(f"- {item}" for item in ask_response["confidence_breakdown"])

    lines.append("")
    lines.append("Citations:")
    citations = ask_response["citations"]
    if not citations:
        lines.append("- (none)")
    else:
        for c in citations:
            heading = f" — {c['heading']}" if c.get("heading") else ""
            lines.append(f"- {c['document_name']}, p.{c['page_number']}{heading}")

    return "\n".join(lines)


def _write_lines(doc: fitz.Document, lines: list[str], page: fitz.Page | None = None) -> None:
    """Write `lines` starting on `page` (a fresh page if not given), splitting
    across as many additional pages as needed. Tries progressively smaller font
    sizes before splitting, since insert_textbox drops all text on overflow
    rather than truncating it."""
    if not lines:
        return

    if page is None:
        page = doc.new_page(width=SUMMARY_PAGE_SIZE[0], height=SUMMARY_PAGE_SIZE[1])
    rect = fitz.Rect(
        SUMMARY_MARGIN,
        SUMMARY_MARGIN,
        SUMMARY_PAGE_SIZE[0] - SUMMARY_MARGIN,
        SUMMARY_PAGE_SIZE[1] - SUMMARY_MARGIN,
    )
    text = "\n".join(lines)

    for fontsize in (10, 9, 8, 7, MIN_FONT_SIZE):
        if page.insert_textbox(rect, text, fontsize=fontsize, fontname="helv") >= 0:
            return

    if len(lines) == 1:
        # A single line still doesn't fit even at the smallest font — insert it
        # anyway (it'll be visually clipped) rather than recursing forever.
        page.insert_textbox(rect, lines[0], fontsize=MIN_FONT_SIZE, fontname="helv")
        return

    mid = len(lines) // 2
    _write_lines(doc, lines[:mid], page=page)
    _write_lines(doc, lines[mid:])  # spills onto a new page


def _write_summary_pages(doc: fitz.Document, summary_text: str) -> None:
    _write_lines(doc, _ascii_safe(summary_text).split("\n"))


def annotate_pdf(document_name: str, question: str, ask_response: dict) -> Path:
    """Annotate the cited pages of `document_name` and append a summary page.

    `ask_response` is expected to be the actual result of a real /ask call
    (answer, confidence, confidence_breakdown, citations as plain dicts) — this
    function doesn't validate that, it just renders whatever it's given.

    Saves the result to backend/annotated/{document_name}_annotated.pdf and
    returns that path. Raises DocumentNotFoundError if the document isn't in
    backend/uploads/.
    """
    safe_name = _safe_filename(document_name)
    source_path = UPLOADS_DIR / safe_name
    if not source_path.exists():
        raise DocumentNotFoundError(
            f"'{document_name}' is not currently uploaded — it may have never "
            "been uploaded this session, or the uploads were cleared. Upload it "
            "again before exporting."
        )

    doc = fitz.open(source_path)

    for citation in ask_response["citations"]:
        if citation["document_name"] != document_name:
            continue
        page_index = citation["page_number"] - 1
        if not (0 <= page_index < doc.page_count):
            continue
        doc[page_index].add_text_annot(
            STICKY_NOTE_POINT, f"Cited for: {question}", icon="Note"
        )

    _write_summary_pages(doc, _build_summary_text(question, ask_response))

    ANNOTATED_DIR.mkdir(exist_ok=True)
    output_path = ANNOTATED_DIR / f"{safe_name}_annotated.pdf"
    doc.save(output_path)
    doc.close()

    return output_path
