from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.agents.errors import MissingAPIKeyError
from app.agents.orchestrator import run_pipeline
from app.annotation.annotator import DocumentNotFoundError, annotate_pdf
from app.ingestion.chunker import chunk_pages
from app.ingestion.parser import parse_pdf
from app.models import (
    AskRequest,
    AskResponse,
    ClearResponse,
    DocumentInfo,
    ExportRequest,
    SearchResult,
    UploadResponse,
)
from app.retrieval.store import add_chunks, clear_all, list_documents, search as search_chunks

load_dotenv()

app = FastAPI(title="Study Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload") #when user clicks upload, triggers api
async def upload(files: list[UploadFile]) -> list[UploadResponse]:
    UPLOADS_DIR.mkdir(exist_ok=True)
    responses = []

    for file in files:
        pdf_bytes = await file.read() #fastapi
        (UPLOADS_DIR / file.filename).write_bytes(pdf_bytes) #pathlib

        pages = parse_pdf(pdf_bytes)
        chunks = chunk_pages(pages, document_name=file.filename)
        add_chunks(chunks)

        responses.append(
            UploadResponse(
                document_name=file.filename,
                total_pages=len(pages),
                total_chunks=len(chunks),
                chunks=chunks,
            )
        )

    return responses


@app.get("/documents")
def documents() -> list[DocumentInfo]:
    """List every document currently in the vector store, including ones from past sessions."""
    return [DocumentInfo(**doc) for doc in list_documents()]


@app.delete("/clear")
def clear() -> ClearResponse:
    """Delete all uploaded PDFs and everything in the vector store."""
    deleted = 0
    if UPLOADS_DIR.exists():
        for pdf_path in UPLOADS_DIR.glob("*.pdf"):
            pdf_path.unlink()
            deleted += 1

    clear_all()
    return ClearResponse(documents_deleted=deleted)


@app.get("/search")
def search(query: str, top_k: int = 5) -> list[SearchResult]:
    return [SearchResult(**result) for result in search_chunks(query, top_k=top_k)]


@app.post("/ask")
def ask(request: AskRequest) -> AskResponse:
    try:
        result = run_pipeline(request.question, top_k=request.top_k)
    except MissingAPIKeyError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return AskResponse(
        answer=result["answer"],
        citations=result["citations"],
        verification=result["verification"],
        retried=result["retried"],
        confidence=result["confidence"],
        confidence_breakdown=result["confidence_breakdown"],
    )


@app.post("/export")
def export(request: ExportRequest) -> FileResponse:
    ask_response = {
        "answer": request.answer,
        "confidence": request.confidence,
        "confidence_breakdown": request.confidence_breakdown,
        "citations": [c.model_dump() for c in request.citations],
    }

    try:
        output_path = annotate_pdf(request.document_name, request.question, ask_response)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_path.name,
    )
