from fastapi import APIRouter, Depends, Query

from app.dependencies import UserContext, require_admin
from app.admin.models import (
    AIConfigResponse,
    AIConfigUpdateRequest,
    AnalyticsResponse,
    PreviewRequest,
    UserListResponse,
    UserUpdateRequest,
)
from app.admin.service import AdminService

router = APIRouter()


def get_admin_service() -> AdminService:
    return AdminService()


# ---- User Management ----

@router.get("/users", response_model=list[UserListResponse])
async def list_users(
    admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    return service.list_users(limit, offset)


@router.patch("/users/{user_id}", response_model=UserListResponse)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.update_user(user_id, body.role, body.is_active)


# ---- AI Config ----

@router.get("/ai-config", response_model=list[AIConfigResponse])
async def get_ai_config(
    admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.get_ai_config()


@router.put("/ai-config")
async def update_ai_config(
    body: AIConfigUpdateRequest,
    admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    result = service.update_ai_config(body.key, body.value, admin.id)
    return {"status": "updated", "config": result}


# ---- Preview ----

@router.post("/preview")
async def preview_migration(
    body: PreviewRequest,
    admin: UserContext = Depends(require_admin),
):
    """Dry-run a migration with optional parameter overrides."""
    from app.agent.client import get_claude_client
    from app.agent.prompts import SYSTEM_PROMPT_BASE, SOURCE_CONTEXT_MAP

    system = SYSTEM_PROMPT_BASE + SOURCE_CONTEXT_MAP.get(body.source_type, "")
    client = get_claude_client()

    response = client.create_message(
        messages=[{
            "role": "user",
            "content": f"Convert this pipeline to GitHub Actions:\n```\n{body.sample_input}\n```",
        }],
        system=system,
        model=body.overrides.get("model"),
        temperature=body.overrides.get("temperature"),
        max_tokens=body.overrides.get("max_tokens"),
    )

    return {
        "output": response.content[0].text,
        "model": response.model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


# ---- Analytics ----

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.get_analytics()
