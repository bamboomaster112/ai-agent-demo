from app.common.supabase import get_supabase_admin
from app.common.exceptions import BadRequestError, UnauthorizedError


class AuthService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    def signup(self, email: str, password: str, display_name: str | None = None) -> dict:
        try:
            response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {"display_name": display_name or email.split("@")[0]}
                    },
                }
            )
            if response.user is None:
                raise BadRequestError("Signup failed")

            session = response.session
            return {
                "access_token": session.access_token if session else "",
                "refresh_token": session.refresh_token if session else "",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "display_name": display_name or email.split("@")[0],
                    "role": "user",
                },
            }
        except BadRequestError:
            raise
        except Exception as e:
            raise BadRequestError(f"Signup failed: {str(e)}")

    def login(self, email: str, password: str) -> dict:
        try:
            response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if response.user is None or response.session is None:
                raise UnauthorizedError("Invalid credentials")

            # Get profile
            profile = (
                self.supabase.table("user_profiles")
                .select("role, display_name")
                .eq("id", response.user.id)
                .single()
                .execute()
            )

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "display_name": profile.data.get("display_name", ""),
                    "role": profile.data.get("role", "user"),
                },
            }
        except (UnauthorizedError, BadRequestError):
            raise
        except Exception:
            raise UnauthorizedError("Invalid credentials")

    def refresh_token(self, refresh_token: str) -> dict:
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            if response.session is None:
                raise UnauthorizedError("Invalid refresh token")

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        except UnauthorizedError:
            raise
        except Exception:
            raise UnauthorizedError("Token refresh failed")

    def get_user_profile(self, user_id: str) -> dict:
        profile = (
            self.supabase.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return profile.data
