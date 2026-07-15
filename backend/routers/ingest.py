"""
Ingestion router - handles data ingestion into Neo4j Knowledge Graph.
"""
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from models import (
    IngestRequest,
    IngestResponse,
    GraphVisualizationResponse,
    DocumentListResponse,
    DeleteDocumentResponse,
)
from services.ingestion_service import IngestionService
from mock_data import get_mock_documents

# Accepted upload types and a sane size ceiling for a text document.
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".md", ".markdown", ".text"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter()
_ingestion_service: IngestionService | None = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service


@router.post("/", response_model=IngestResponse)
async def ingest_data(request: IngestRequest):
    """
    Ingest raw text data into the Knowledge Graph.
    
    This endpoint:
    1. Chunks the input text
    2. Extracts entities and relationships using Gemini
    3. Loads them into Neo4j AuraDB
    """
    try:
        result = await get_ingestion_service().ingest_text(
            text=request.text,
            clear_existing=request.clear_existing,
            title=request.title,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/upload", response_model=IngestResponse)
async def ingest_uploaded_file(
    file: UploadFile = File(..., description="A plain-text or Markdown document to ingest"),
    title: str | None = Form(default=None, description="Optional title; defaults to the filename"),
    clear_existing: bool = Form(default=False, description="Clear graph before ingesting"),
):
    """
    Ingest an uploaded text document into the Knowledge Graph.

    Accepts a plain-text or Markdown file, decodes it as UTF-8, and runs it
    through the same chunk → extract → load pipeline as raw-text ingestion.
    """
    filename = file.filename or "uploaded document"
    _, ext = os.path.splitext(filename.lower())
    if ext and ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
            ),
        )

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw)} bytes). Max is {MAX_UPLOAD_BYTES} bytes.",
        )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File is not valid UTF-8 text. Please upload a plain-text or Markdown file.",
        )

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Default the document title to the filename (without extension).
    resolved_title = (title or "").strip() or os.path.splitext(filename)[0]

    try:
        return await get_ingestion_service().ingest_text(
            text=text,
            clear_existing=clear_existing,
            title=resolved_title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/samples")
async def list_sample_documents():
    """List available mock documents for demo ingestion."""
    return {"documents": get_mock_documents()}


@router.post("/samples", response_model=IngestResponse)
async def ingest_sample_documents(
    clear_existing: bool = Query(default=False, description="Clear graph before loading samples"),
):
    """Ingest all mock sample documents into the Knowledge Graph."""
    try:
        return await get_ingestion_service().ingest_documents(
            documents=get_mock_documents(),
            clear_existing=clear_existing,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample ingestion failed: {str(e)}")


@router.get("/status")
async def get_ingestion_status():
    """
    Get the current status of the Knowledge Graph.
    Returns counts of nodes and relationships.
    """
    try:
        status = await get_ingestion_service().get_graph_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/graph", response_model=GraphVisualizationResponse)
async def get_graph_visualization(limit: int = 150):
    """
    Return nodes and relationships for frontend graph visualization.
    """
    try:
        return await get_ingestion_service().get_graph_visualization(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {str(e)}")


@router.post("/embed")
async def embed_documents():
    """
    Embed all Document nodes that are missing vectors.
    Run after ingestion or to backfill an existing graph.
    """
    try:
        count = get_ingestion_service().hybrid_retrieval.embed_all_documents()
        return {"status": "success", "embedded_documents": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List ingested documents (grouped by title) with chunk/entity counts."""
    try:
        documents = await get_ingestion_service().list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/documents", response_model=DeleteDocumentResponse)
async def delete_document(
    title: str = Query(..., description="Title of the document to delete"),
):
    """
    Delete a single document and prune the entities it uniquely added.

    Removes the document's text chunks and any entity that was mentioned only by
    this document. Entities shared with other documents are preserved.
    """
    try:
        result = await get_ingestion_service().delete_document(title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("message", "Document not found"))
    return result


@router.delete("/clear")
async def clear_graph():
    """
    Clear all data from the Knowledge Graph.
    USE WITH CAUTION - This deletes all nodes and relationships!
    """
    try:
        await get_ingestion_service().clear_graph()
        return {"status": "success", "message": "Knowledge Graph cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear graph: {str(e)}")

# Made with Bob
