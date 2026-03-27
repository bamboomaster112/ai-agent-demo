from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: "UserProfile"


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    role: str = "user"


class RefreshRequest(BaseModel):
    refresh_token: str
