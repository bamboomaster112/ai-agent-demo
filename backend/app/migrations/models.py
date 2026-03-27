from pydantic import BaseModel
from datetime import datetime


class CreateSessionRequest(BaseModel):
    title: str | None = None
    source_type: str
    source_content: str | None = None


class SendMessageRequest(BaseModel):
    content: str
    upload_ids: list[str] = []


class SessionResponse(BaseModel):
    id: str
    title: str | None
    source_type: str
    source_platform: str | None = None
    source_format: str | None = None
    config_type: str | None = None
    detection_confidence: float | None = None
    status: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict = {}
    created_at: str


class WorkflowResponse(BaseModel):
    id: str
    filename: str
    yaml_content: str
    notes: list = []
    version: int
    created_at: str


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse] = []
    workflows: list[WorkflowResponse] = []
