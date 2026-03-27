from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from app.dependencies import UserContext, get_current_user
from app.migrations.models import (
    CreateSessionRequest,
    MessageResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from app.migrations.service import MigrationService

router = APIRouter()


def get_migration_service() -> MigrationService:
    return MigrationService()


@router.post("/", response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    user: UserContext = Depends(get_current_user),
    service: MigrationService = Depends(get_migration_service),
):
    session = service.create_session(
        user_id=user.id,
        title=body.title,
        source_type=body.source_type,
        source_content=body.source_content,
    )
    return session


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    user: UserContext = Depends(get_current_user),
    service: MigrationService = Depends(get_migration_service),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    return service.list_sessions(user.id, limit, offset)


@router.get("/{session_id}")
async def get_session_detail(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    service: MigrationService = Depends(get_migration_service),
):
    detail = service.get_session_detail(session_id, user.id)
    if not detail:
        from app.common.exceptions import NotFoundError
        raise NotFoundError("Session not found")
    return detail


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    service: MigrationService = Depends(get_migration_service),
):
    service.delete_session(session_id, user.id)
    return {"status": "deleted"}


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    service: MigrationService = Depends(get_migration_service),
):
    return service.get_messages(session_id)


@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    user: UserContext = Depends(get_current_user),
    service: MigrationService = Depends(get_migration_service),
):
    """Send a message and stream the AI response via SSE."""
    return EventSourceResponse(
        service.stream_ai_response(
            session_id=session_id,
            user_id=user.id,
            user_message=body.content,
        )
    )
