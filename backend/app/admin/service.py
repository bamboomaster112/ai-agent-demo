"""Admin service: user management, AI config, analytics."""

from app.common.supabase import get_supabase_admin


class AdminService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    # ---- User Management ----

    def list_users(self, limit: int = 50, offset: int = 0) -> list[dict]:
        result = (
            self.supabase.table("user_profiles")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []

    def update_user(self, user_id: str, role: str | None = None, is_active: bool | None = None) -> dict:
        updates = {}
        if role is not None:
            updates["role"] = role
        if is_active is not None:
            updates["is_active"] = is_active

        if not updates:
            return {}

        result = (
            self.supabase.table("user_profiles")
            .update(updates)
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    # ---- AI Config ----

    def get_ai_config(self) -> list[dict]:
        result = (
            self.supabase.table("ai_config")
            .select("*")
            .order("key")
            .execute()
        )
        return result.data or []

    def update_ai_config(self, key: str, value: dict, admin_id: str) -> dict:
        result = (
            self.supabase.table("ai_config")
            .update({"value": value, "updated_by": admin_id})
            .eq("key", key)
            .execute()
        )

        # Invalidate Claude client config cache
        from app.agent.client import get_claude_client
        get_claude_client().invalidate_config_cache()

        return result.data[0] if result.data else {}

    # ---- Analytics ----

    def get_analytics(self) -> dict:
        # Total users
        users = self.supabase.table("user_profiles").select("id", count="exact").execute()
        total_users = users.count or 0

        # Total migrations
        migrations = (
            self.supabase.table("migration_sessions")
            .select("id", count="exact")
            .execute()
        )
        total_migrations = migrations.count or 0

        # Total messages
        messages = self.supabase.table("messages").select("id", count="exact").execute()
        total_messages = messages.count or 0

        # Token usage
        usage = (
            self.supabase.table("usage_logs")
            .select("tokens_in, tokens_out")
            .execute()
        )
        total_tokens_in = sum(r.get("tokens_in", 0) for r in (usage.data or []))
        total_tokens_out = sum(r.get("tokens_out", 0) for r in (usage.data or []))

        # Recent activity (last 20 logs)
        recent = (
            self.supabase.table("usage_logs")
            .select("user_id, action, model_used, tokens_in, tokens_out, created_at")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        return {
            "total_users": total_users,
            "total_migrations": total_migrations,
            "total_messages": total_messages,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "recent_activity": recent.data or [],
        }
