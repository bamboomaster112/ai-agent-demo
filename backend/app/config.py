from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # OpenAI (embeddings)
    openai_api_key: str = ""

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
