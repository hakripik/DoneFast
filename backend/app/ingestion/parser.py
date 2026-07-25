"""PDF text extraction with best-effort heading detection using PyMuPDF."""

from dataclasses import dataclass, field

import fitz  # PyMuPDF

# A line is treated as a heading if its font size is at least this many
# points larger than the page's most common (body) font size.
HEADING_SIZE_DELTA = 2.0


@dataclass
class ParsedPage:
    page_number: int  # 1-indexed
    text: str
    # (heading_text, char_offset_into_text) for each heading found on the page,
    # in the order they appear.
    headings: list[tuple[str, int]] = field(default_factory=list)


def parse_pdf(pdf_bytes: bytes) -> list[ParsedPage]:
    """Extract per-page text and best-effort headings from a PDF's bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[ParsedPage] = []

    for page_index, page in enumerate(doc):
        page_dict = page.get_text("dict")
        body_size = _most_common_font_size(page_dict)

        text_parts: list[str] = []
        headings: list[tuple[str, int]] = []
        char_offset = 0

        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                line_text, max_size = _line_text_and_max_size(line)
                if not line_text.strip():
                    continue

                if max_size >= body_size + HEADING_SIZE_DELTA:
                    headings.append((line_text.strip(), char_offset))

                text_parts.append(line_text)
                char_offset += len(line_text)

        pages.append(
            ParsedPage(
                page_number=page_index + 1,
                text="".join(text_parts),
                headings=headings,
            )
        )

    doc.close()
    return pages


def _line_text_and_max_size(line: dict) -> tuple[str, float]:
    spans = line.get("spans", [])
    text = "".join(span.get("text", "") for span in spans) + "\n"
    max_size = max((span.get("size", 0.0) for span in spans), default=0.0)
    return text, max_size


def _most_common_font_size(page_dict: dict) -> float:
    """Approximate the body text size as the size covering the most characters."""
    size_counts: dict[float, int] = {}
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = round(span.get("size", 0.0), 1)
                size_counts[size] = size_counts.get(size, 0) + len(span.get("text", ""))

    if not size_counts:
        return 0.0
    return max(size_counts, key=size_counts.get)
