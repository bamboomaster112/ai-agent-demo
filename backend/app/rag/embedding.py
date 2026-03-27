"""Embedding generation service using Voyage AI (Anthropic's official partner)."""

import voyageai

from app.config import settings
from app.common.supabase import get_supabase_admin

_voyage_client: voyageai.Client | None = None


def _get_voyage_client() -> voyageai.Client:
    """Get or create Voyage AI client singleton."""
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=settings.voyage_api_key)
    return _voyage_client


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
    return "voyage-3.5"


def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    client = _get_voyage_client()
    model = _get_embedding_model()

    result = client.embed([text], model=model, input_type="document")
    return result.embeddings[0]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call."""
    if not texts:
        return []

    client = _get_voyage_client()
    model = _get_embedding_model()

    # Voyage AI supports up to 128 texts per batch
    all_embeddings: list[list[float]] = []
    batch_size = 128

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = client.embed(batch, model=model, input_type="document")
        all_embeddings.extend(result.embeddings)

    return all_embeddings


def generate_query_embedding(text: str) -> list[float]:
    """Generate an embedding for a search query (uses input_type='query')."""
    client = _get_voyage_client()
    model = _get_embedding_model()

    result = client.embed([text], model=model, input_type="query")
    return result.embeddings[0]
