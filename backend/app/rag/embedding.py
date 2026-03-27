"""Embedding generation service using OpenAI."""

import openai

from app.config import settings
from app.common.supabase import get_supabase_admin


def _get_embedding_model() -> str:
    """Get the configured embedding model from rag_config."""
    try:
        supabase = get_supabase_admin()
        result = (
            supabase.table("rag_config")
            .select("value")
            .eq("key", "embedding_model")
            .single()
            .execute()
        )
        if result.data:
            return result.data["value"]["value"]
    except Exception:
        pass
    return "text-embedding-3-small"


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    client = openai.OpenAI(api_key=settings.openai_api_key)
    model = _get_embedding_model()

    response = client.embeddings.create(
        model=model,
        input=text,
    )

    return response.data[0].embedding


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call."""
    client = openai.OpenAI(api_key=settings.openai_api_key)
    model = _get_embedding_model()

    response = client.embeddings.create(
        model=model,
        input=texts,
    )

    return [item.embedding for item in response.data]
