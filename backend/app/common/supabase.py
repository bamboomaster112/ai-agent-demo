from supabase import create_client, Client

from app.config import settings

_client: Client | None = None
_admin_client: Client | None = None


def get_supabase_client() -> Client:
    """Get Supabase client using anon key (respects RLS)."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client


def get_supabase_admin() -> Client:
    """Get Supabase client using service role key (bypasses RLS)."""
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _admin_client
