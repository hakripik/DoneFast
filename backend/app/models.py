"""Pydantic request/response schemas."""

from pydantic import BaseModel #lib for data validation, parsing and serailisation through inheritance


class Chunk(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int
    heading: str | None
    text: str


class UploadResponse(BaseModel):
    document_name: str
    total_pages: int
    total_chunks: int
    chunks: list[Chunk]


class SearchResult(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int
    heading: str | None
    text: str
    similarity: float


class Citation(BaseModel):
    document_name: str
    page_number: int
    heading: str | None


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class Verification(BaseModel):
    supported: bool
    issues: list[str]
    notes: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    verification: Verification
    retried: bool
    confidence: int
    confidence_breakdown: list[str]


class DocumentInfo(BaseModel):
    document_name: str
    total_pages: int
    total_chunks: int


class ClearResponse(BaseModel):
    documents_deleted: int


class ExportRequest(BaseModel):
    document_name: str
    question: str
    answer: str
    confidence: int
    confidence_breakdown: list[str]
    citations: list[Citation]
