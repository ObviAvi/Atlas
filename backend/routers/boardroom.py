"""
Boardroom router - handles multi-agent debate system.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import BoardroomDebateRequest, BoardroomDebateResponse
from services.boardroom_service import BoardroomService
import json

router = APIRouter()
_boardroom_service: BoardroomService | None = None


def get_boardroom_service() -> BoardroomService:
    global _boardroom_service
    if _boardroom_service is None:
        _boardroom_service = BoardroomService()
    return _boardroom_service


@router.post("/debate", response_model=BoardroomDebateResponse)
async def start_debate(request: BoardroomDebateRequest):
    """
    Start a multi-agent debate on the user's idea.
    
    This endpoint:
    1. Decomposes the idea to identify data requirements
    2. Retrieves relevant graph context from Neo4j
    3. Runs a debate between Strategist and Risk Analyst agents
    4. Synthesizes a final executive summary
    """
    try:
        result = await get_boardroom_service().run_debate(
            idea=request.idea,
            rounds=request.rounds or 3
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")


@router.post("/debate/stream")
async def stream_debate(request: BoardroomDebateRequest):
    """
    Stream the debate in real-time as agents respond.
    Returns Server-Sent Events (SSE) for live updates.
    """
    async def event_generator():
        try:
            async for event in get_boardroom_service().stream_debate(
                idea=request.idea,
                rounds=request.rounds or 3
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# Made with Bob
