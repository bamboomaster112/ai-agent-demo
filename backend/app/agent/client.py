"""Anthropic Claude API wrapper with streaming support."""

import time

import anthropic

from app.config import settings
from app.common.supabase import get_supabase_admin

CONFIG_CACHE_TTL_SECONDS = 300  # 5 minutes


class ClaudeClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._config_cache: dict | None = None
        self._config_cache_time: float = 0.0

    def _get_ai_config(self) -> dict:
        """Load AI config from database (admin-configured). Cached with TTL."""
        if (
            self._config_cache is not None
            and (time.monotonic() - self._config_cache_time) < CONFIG_CACHE_TTL_SECONDS
        ):
            return self._config_cache

        try:
            supabase = get_supabase_admin()
            rows = supabase.table("ai_config").select("key, value").execute()
            config = {}
            for row in rows.data:
                config[row["key"]] = row["value"]["value"]
            self._config_cache = config
            self._config_cache_time = time.monotonic()
            return config
        except Exception:
            return {
                "model": settings.default_model,
                "temperature": settings.default_temperature,
                "max_tokens": settings.default_max_tokens,
            }

    def invalidate_config_cache(self):
        self._config_cache = None
        self._config_cache_time = 0.0

    def stream_message(
        self,
        messages: list[dict],
        system: str,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> anthropic.MessageStream:
        """Stream a message from Claude. Returns an Anthropic MessageStream."""
        config = self._get_ai_config()

        return self.client.messages.stream(
            model=model or config.get("model", settings.default_model),
            max_tokens=max_tokens or int(config.get("max_tokens", settings.default_max_tokens)),
            temperature=temperature or float(config.get("temperature", settings.default_temperature)),
            system=system,
            messages=messages,
        )

    def create_message(
        self,
        messages: list[dict],
        system: str,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> anthropic.types.Message:
        """Non-streaming message creation."""
        config = self._get_ai_config()

        return self.client.messages.create(
            model=model or config.get("model", settings.default_model),
            max_tokens=max_tokens or int(config.get("max_tokens", settings.default_max_tokens)),
            temperature=temperature or float(config.get("temperature", settings.default_temperature)),
            system=system,
            messages=messages,
        )


# Singleton
_claude_client: ClaudeClient | None = None


def get_claude_client() -> ClaudeClient:
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
