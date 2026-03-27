from pydantic import BaseModel


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class UserListResponse(BaseModel):
    id: str
    email: str
    display_name: str | None
    role: str
    is_active: bool
    created_at: str


class AIConfigResponse(BaseModel):
    key: str
    value: dict
    description: str | None
    min_value: float | None
    max_value: float | None


class AIConfigUpdateRequest(BaseModel):
    key: str
    value: dict


class PreviewRequest(BaseModel):
    sample_input: str
    source_type: str = "jenkins"
    overrides: dict = {}


class AnalyticsResponse(BaseModel):
    total_users: int
    total_migrations: int
    total_messages: int
    total_tokens_in: int
    total_tokens_out: int
    recent_activity: list[dict]
