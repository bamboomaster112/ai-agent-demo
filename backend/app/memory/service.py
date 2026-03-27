"""User preference/memory service: extraction, storage, retrieval."""

import re
import json

from app.common.supabase import get_supabase_admin

# Regex patterns for explicit preference detection
EXPLICIT_PATTERNS = [
    (
        re.compile(r"(?:always|prefer|use)\s+(?:to\s+)?(?:use\s+)?(ubuntu[- ]\d+\.\d+)", re.IGNORECASE),
        "runner_image",
        "default_runner",
    ),
    (
        re.compile(r"(?:prefer|use|want)\s+matrix\s+builds?", re.IGNORECASE),
        "build_strategy",
        "prefer_matrix",
    ),
    (
        re.compile(r"(?:always|prefer)\s+(?:to\s+)?use\s+(?:self[- ]hosted)\s+runners?", re.IGNORECASE),
        "runner_image",
        "self_hosted",
    ),
    (
        re.compile(r"(?:use|prefer)\s+(npm|yarn|pnpm)\b", re.IGNORECASE),
        "tooling",
        "package_manager",
    ),
    (
        re.compile(r"(?:use|prefer)\s+(gradle|maven)\b", re.IGNORECASE),
        "tooling",
        "build_tool",
    ),
    (
        re.compile(r"(?:don't|do not|never)\s+use\s+([\w-]+)", re.IGNORECASE),
        "tooling",
        "excluded_tool",
    ),
]


class MemoryService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    def list_preferences(self, user_id: str) -> list[dict]:
        result = (
            self.supabase.table("user_preferences")
            .select("*")
            .eq("user_id", user_id)
            .eq("active", True)
            .order("category")
            .execute()
        )
        return result.data or []

    def create_preference(
        self,
        user_id: str,
        category: str,
        preference_key: str,
        preference_value: str,
        source: str = "manual",
        confidence: float = 1.0,
        source_message_id: str | None = None,
    ) -> dict:
        result = (
            self.supabase.table("user_preferences")
            .upsert(
                {
                    "user_id": user_id,
                    "category": category,
                    "preference_key": preference_key,
                    "preference_value": preference_value,
                    "source": source,
                    "confidence": confidence,
                    "source_message_id": source_message_id,
                    "active": True,
                },
                on_conflict="user_id,category,preference_key",
            )
            .execute()
        )
        return result.data[0]

    def update_preference(self, pref_id: str, user_id: str, value: str) -> dict:
        # Log audit
        old = (
            self.supabase.table("user_preferences")
            .select("preference_value")
            .eq("id", pref_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        result = (
            self.supabase.table("user_preferences")
            .update({"preference_value": value, "source": "manual"})
            .eq("id", pref_id)
            .eq("user_id", user_id)
            .execute()
        )

        # Audit log
        if old.data:
            self.supabase.table("preference_audit_log").insert({
                "preference_id": pref_id,
                "action": "updated",
                "old_value": old.data["preference_value"],
                "new_value": value,
            }).execute()

        return result.data[0] if result.data else {}

    def delete_preference(self, pref_id: str, user_id: str) -> None:
        """Soft-delete: set active=false."""
        self.supabase.table("user_preferences").update(
            {"active": False}
        ).eq("id", pref_id).eq("user_id", user_id).execute()

        self.supabase.table("preference_audit_log").insert({
            "preference_id": pref_id,
            "action": "deleted",
        }).execute()

    def extract_preferences_from_text(
        self, user_id: str, text: str, message_id: str | None = None
    ) -> list[dict]:
        """Extract explicit preferences from user message text using regex patterns."""
        extracted = []
        for pattern, category, key in EXPLICIT_PATTERNS:
            match = pattern.search(text)
            if match:
                value = match.group(1) if match.lastindex else "true"
                pref = self.create_preference(
                    user_id=user_id,
                    category=category,
                    preference_key=key,
                    preference_value=value,
                    source="explicit",
                    confidence=0.9,
                    source_message_id=message_id,
                )
                extracted.append(pref)
        return extracted

    def extract_preferences_with_ai(
        self, user_id: str, conversation_messages: list[dict]
    ) -> list[dict]:
        """Use Claude to extract implicit preferences from a conversation."""
        from app.agent.client import get_claude_client

        conversation_text = "\n".join(
            f"{m['role']}: {m['content'][:500]}" for m in conversation_messages
        )

        prompt = f"""Analyze this conversation and extract user preferences about CI/CD pipelines and workflows.
Return a JSON array of preferences. Only extract preferences the user clearly stated or strongly implied.

Conversation:
{conversation_text[:4000]}

Return ONLY a JSON array:
[{{"category": "runner_image|build_strategy|tooling|style|general", "key": "preference_name", "value": "preference_value", "confidence": 0.0-1.0}}]

If no preferences found, return an empty array: []"""

        try:
            client = get_claude_client()
            response = client.create_message(
                messages=[{"role": "user", "content": prompt}],
                system="You extract user preferences from conversations. Return only valid JSON.",
                max_tokens=500,
                temperature=0.1,
            )

            text = response.content[0].text.strip()
            if "```" in text:
                text = text.split("```")[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

            preferences = json.loads(text)
            results = []
            for pref in preferences:
                result = self.create_preference(
                    user_id=user_id,
                    category=pref["category"],
                    preference_key=pref["key"],
                    preference_value=pref["value"],
                    source="inferred",
                    confidence=pref.get("confidence", 0.7),
                )
                results.append(result)
            return results
        except Exception:
            return []
