from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase (new key naming: publishable = anon, secret = service_role)
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Voyage AI (Anthropic's official embedding partner)
    voyage_api_key: str = ""

    # App
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    secret_key: str = "change-this-to-a-random-secret"

    # AI defaults (overridable by admin via DB)
    default_model: str = "claude-sonnet-4-20250514"
    default_temperature: float = 0.3
    default_max_tokens: int = 4096

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()
