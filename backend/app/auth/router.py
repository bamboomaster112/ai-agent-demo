from fastapi import APIRouter, Depends

from app.auth.models import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    UserProfile,
)
from app.auth.service import AuthService
from app.dependencies import UserContext, get_current_user

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/signup", response_model=AuthResponse)
async def signup(
    body: SignupRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.signup(body.email, body.password, body.display_name)


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.login(body.email, body.password)


@router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.refresh_token(body.refresh_token)


@router.get("/me", response_model=UserProfile)
async def me(
    user: UserContext = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    profile = service.get_user_profile(user.id)
    return UserProfile(
        id=profile["id"],
        email=profile["email"],
        display_name=profile.get("display_name"),
        role=profile.get("role", "user"),
    )
