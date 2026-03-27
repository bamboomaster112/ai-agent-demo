"""Assembles the full system prompt: base + source context + user preferences + RAG context."""

from app.agent.prompts import SYSTEM_PROMPT_BASE, SOURCE_CONTEXT_MAP
from app.common.supabase import get_supabase_admin


def build_system_prompt(
    user_id: str,
    source_type: str,
    rag_chunks: list[dict] | None = None,
) -> str:
    """
    Build the complete system prompt with all context layers:
    1. Base migration specialist prompt
    2. Source-specific context (TeamCity/Jenkins)
    3. User preferences (memory)
    4. RAG context (similar past migrations + reference docs)
    """
    parts = [SYSTEM_PROMPT_BASE]

    # Layer 2: Source-specific context
    source_context = SOURCE_CONTEXT_MAP.get(source_type, "")
    if source_context:
        parts.append(source_context)

    # Layer 3: User preferences
    preferences_block = _build_preferences_block(user_id)
    if preferences_block:
        parts.append(preferences_block)

    # Layer 4: RAG context
    if rag_chunks:
        rag_block = _build_rag_block(rag_chunks)
        if rag_block:
            parts.append(rag_block)

    return "\n\n".join(parts)


def _build_preferences_block(user_id: str) -> str:
    """Load active user preferences and format as a prompt section."""
    try:
        supabase = get_supabase_admin()
        result = (
            supabase.table("user_preferences")
            .select("category, preference_key, preference_value")
            .eq("user_id", user_id)
            .eq("active", True)
            .execute()
        )

        prefs = result.data
        if not prefs:
            return ""

        lines = ["## User Preferences (from past sessions)"]
        for p in prefs:
            lines.append(f"- {p['category']}/{p['preference_key']}: {p['preference_value']}")
        lines.append("\nHonor these preferences unless they conflict with the specific request.")
        return "\n".join(lines)
    except Exception:
        return ""


def _build_rag_block(chunks: list[dict]) -> str:
    """Format retrieved RAG chunks as a prompt section."""
    if not chunks:
        return ""

    migration_chunks = [c for c in chunks if c.get("doc_type") == "migration_result"]
    reference_chunks = [c for c in chunks if c.get("doc_type") != "migration_result"]

    parts = []

    if migration_chunks:
        parts.append("## Similar Past Migrations (for reference)")
        for i, chunk in enumerate(migration_chunks, 1):
            parts.append(f"### Example {i} (similarity: {chunk.get('similarity', 'N/A')})")
            parts.append(chunk["content"])

    if reference_chunks:
        parts.append("## Relevant Documentation")
        for chunk in reference_chunks:
            title = chunk.get("title", "Reference")
            parts.append(f"### {title}")
            parts.append(chunk["content"])

    return "\n\n".join(parts)
