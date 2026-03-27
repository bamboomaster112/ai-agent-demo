from fastapi import Depends, Request
from pydantic import BaseModel

from app.common.exceptions import ForbiddenError, UnauthorizedError
from app.common.supabase import get_supabase_admin


class UserContext(BaseModel):
    id: str
    email: str
    role: str


async def get_current_user(request: Request) -> UserContext:
    """Extract and validate the JWT from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1]
    supabase = get_supabase_admin()

    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if user is None:
            raise UnauthorizedError()
    except Exception:
        raise UnauthorizedError()

    # Get profile with role
    profile = (
        supabase.table("user_profiles")
        .select("role, is_active")
        .eq("id", user.id)
        .single()
        .execute()
    )

    if not profile.data or not profile.data.get("is_active", True):
        raise ForbiddenError("Account is disabled")

    return UserContext(
        id=user.id,
        email=user.email,
        role=profile.data.get("role", "user"),
    )


async def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    """Ensure the current user has admin role."""
    if user.role != "admin":
        raise ForbiddenError("Admin access required")
    return user
