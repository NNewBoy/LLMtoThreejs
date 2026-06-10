"""AI router — SSE chat endpoint and skills listing."""

import json
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.ai import AIChatRequest, SkillInfo, SkillsListResponse
from schemas.common import UnifiedResponse
from services.ai_service import AIService

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _svc(db: Session = Depends(get_db)) -> AIService:
    return AIService(db)


@router.post("/chat")
async def chat(body: AIChatRequest, svc: AIService = Depends(_svc)):
    """SSE endpoint for AI chat. Streams skill execution events."""

    async def event_generator():
        async for sse_block in svc.chat_stream(
            cabinet_id=body.cabinet_id,
            message=body.message,
            history=[m.model_dump() for m in body.history],
        ):
            # sse_block is already formatted as "event: X\ndata: Y\n\n"
            # Parse it back for EventSourceResponse
            lines = sse_block.strip().split("\n")
            event_name = None
            data_str = None
            for line in lines:
                if line.startswith("event:"):
                    event_name = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data_str = line[len("data:"):].strip()

            if event_name and data_str:
                yield {"event": event_name, "data": data_str}

    return EventSourceResponse(event_generator())


@router.get("/skills", response_model=UnifiedResponse)
def list_skills(svc: AIService = Depends(_svc)):
    """List all available skills with their metadata."""
    skills = svc.get_skills_list()
    return UnifiedResponse(
        success=True,
        data=SkillsListResponse(
            skills=[SkillInfo(**s) for s in skills]
        ).model_dump(),
    )
