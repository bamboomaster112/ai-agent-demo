"""Manage conversation context for migration sessions."""

from app.common.supabase import get_supabase_admin

MAX_MESSAGES_IN_CONTEXT = 20


def get_conversation_history(session_id: str) -> list[dict]:
    """
    Load conversation history from the database.
    Returns messages formatted for the Anthropic API.
    Uses a sliding window of the last MAX_MESSAGES_IN_CONTEXT messages.
    """
    supabase = get_supabase_admin()

    result = (
        supabase.table("messages")
        .select("role, content, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )

    messages = result.data or []

    # Apply sliding window
    if len(messages) > MAX_MESSAGES_IN_CONTEXT:
        # Summarize older messages
        older = messages[:-MAX_MESSAGES_IN_CONTEXT]
        recent = messages[-MAX_MESSAGES_IN_CONTEXT:]

        summary = _summarize_older_messages(older)
        api_messages = [{"role": "user", "content": f"[Previous context summary: {summary}]"}]
        api_messages.append({"role": "assistant", "content": "I understand the previous context. Let's continue."})
    else:
        recent = messages
        api_messages = []

    # Convert to Anthropic format
    for msg in recent:
        if msg["role"] in ("user", "assistant"):
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

    return api_messages


def save_message(session_id: str, role: str, content: str, metadata: dict | None = None) -> str:
    """Save a message to the database. Returns the message ID."""
    supabase = get_supabase_admin()

    result = (
        supabase.table("messages")
        .insert({
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        })
        .execute()
    )

    return result.data[0]["id"]


def _summarize_older_messages(messages: list[dict]) -> str:
    """Create a brief summary of older messages for context compression."""
    parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"][:200]
        parts.append(f"{role}: {content}...")

    return " | ".join(parts[-5:])  # Keep last 5 summaries
