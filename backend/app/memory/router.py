from fastapi import APIRouter, Depends

from app.dependencies import UserContext, get_current_user
from app.memory.models import PreferenceCreate, PreferenceResponse, PreferenceUpdate
from app.memory.service import MemoryService

router = APIRouter()


def get_memory_service() -> MemoryService:
    return MemoryService()


@router.get("/", response_model=list[PreferenceResponse])
async def list_preferences(
    user: UserContext = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
):
    return service.list_preferences(user.id)


@router.post("/", response_model=PreferenceResponse)
async def create_preference(
    body: PreferenceCreate,
    user: UserContext = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
):
    return service.create_preference(
        user_id=user.id,
        category=body.category,
        preference_key=body.preference_key,
        preference_value=body.preference_value,
        source="manual",
    )


@router.put("/{pref_id}", response_model=PreferenceResponse)
async def update_preference(
    pref_id: str,
    body: PreferenceUpdate,
    user: UserContext = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
):
    return service.update_preference(pref_id, user.id, body.preference_value)


@router.delete("/{pref_id}")
async def delete_preference(
    pref_id: str,
    user: UserContext = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
):
    service.delete_preference(pref_id, user.id)
    return {"status": "deleted"}


@router.post("/extract/{session_id}")
async def extract_preferences_from_session(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
):
    """Extract preferences from a conversation session using AI."""
    from app.common.supabase import get_supabase_admin

    supabase = get_supabase_admin()
    messages = (
        supabase.table("messages")
        .select("role, content")
        .eq("session_id", session_id)
        .execute()
    ).data or []

    results = await service.extract_preferences_with_ai(user.id, messages)
    return {"extracted": len(results), "preferences": results}
