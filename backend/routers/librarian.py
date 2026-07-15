"""
Librarian router - handles GraphRAG queries for factual information.
"""
from fastapi import APIRouter, HTTPException
from models import LibrarianQueryRequest, LibrarianQueryResponse
from services.librarian_service import LibrarianService

router = APIRouter()
_librarian_service: LibrarianService | None = None


def get_librarian_service() -> LibrarianService:
    global _librarian_service
    if _librarian_service is None:
        _librarian_service = LibrarianService()
    return _librarian_service


@router.post("/query", response_model=LibrarianQueryResponse)
async def query_knowledge_graph(request: LibrarianQueryRequest):
    """
    Query the Knowledge Graph using GraphRAG.
    
    This endpoint:
    1. Analyzes the user's question
    2. Generates appropriate Cypher queries
    3. Retrieves relevant graph data
    4. Synthesizes a factual answer using Gemini
    """
    try:
        result = await get_librarian_service().query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# Made with Bob
