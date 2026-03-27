"""Detection service: Tier 1 heuristic + Tier 2 AI fallback."""

import json
import anthropic

from app.config import settings
from app.common.supabase import get_supabase_admin
from app.detection.patterns import detect_platform_and_format, detect_config_type

CONFIDENCE_THRESHOLD = 0.7


class DetectionResult:
    def __init__(
        self,
        source_platform: str,
        source_format: str,
        config_type: str,
        confidence: float,
        method: str,
        matched_patterns: list[str] | None = None,
    ):
        self.source_platform = source_platform
        self.source_format = source_format
        self.config_type = config_type
        self.confidence = confidence
        self.method = method
        self.matched_patterns = matched_patterns or []

    def to_dict(self) -> dict:
        return {
            "source_platform": self.source_platform,
            "source_format": self.source_format,
            "config_type": self.config_type,
            "confidence": self.confidence,
            "method": self.method,
            "matched_patterns": self.matched_patterns,
        }


class DetectionService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def detect(
        self, content: str, filename: str | None = None
    ) -> DetectionResult:
        """Run Tier 1 heuristic detection, fall back to AI if low confidence."""
        # Tier 1: Heuristic
        platform_result = detect_platform_and_format(content, filename)
        type_result = detect_config_type(content)

        combined_confidence = min(
            platform_result["confidence"], type_result["confidence"]
        )

        if combined_confidence >= CONFIDENCE_THRESHOLD:
            return DetectionResult(
                source_platform=platform_result["source_platform"],
                source_format=platform_result["source_format"],
                config_type=type_result["config_type"],
                confidence=combined_confidence,
                method="heuristic",
                matched_patterns=platform_result["matched_patterns"],
            )

        # Tier 2: AI fallback
        return await self._detect_with_ai(content, filename, platform_result)

    async def _detect_with_ai(
        self, content: str, filename: str | None, heuristic_hint: dict
    ) -> DetectionResult:
        """Use Claude to classify ambiguous pipeline configurations."""
        # Get classification model from admin config
        model = "claude-haiku-4-5-20251001"
        try:
            config_row = (
                self.supabase.table("ai_config")
                .select("value")
                .eq("key", "classification_model")
                .single()
                .execute()
            )
            if config_row.data:
                model = config_row.data["value"]["value"]
        except Exception:
            pass

        prompt = f"""Analyze this CI/CD pipeline configuration and classify it.

Filename: {filename or "unknown"}
Content (first 2000 chars):
```
{content[:2000]}
```

Heuristic hint: {json.dumps(heuristic_hint)}

Respond with ONLY a JSON object:
{{
  "source_platform": "teamcity" or "jenkins",
  "source_format": "kotlin_dsl" or "xml" or "json_api" or "groovy",
  "config_type": "shared_library" or "complete_pipeline" or "fragment",
  "confidence": 0.0 to 1.0
}}"""

        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            # Extract JSON from response
            if "```" in text:
                text = text.split("```")[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

            result = json.loads(text)
            return DetectionResult(
                source_platform=result["source_platform"],
                source_format=result["source_format"],
                config_type=result["config_type"],
                confidence=result.get("confidence", 0.8),
                method="ai",
            )
        except Exception:
            # If AI also fails, return best heuristic guess
            type_result = detect_config_type(content)
            return DetectionResult(
                source_platform=heuristic_hint["source_platform"],
                source_format=heuristic_hint["source_format"],
                config_type=type_result["config_type"],
                confidence=heuristic_hint["confidence"],
                method="heuristic",
                matched_patterns=heuristic_hint["matched_patterns"],
            )

    def update_detection(
        self, session_id: str, source_platform: str, source_format: str, config_type: str
    ) -> None:
        """User override of detection result."""
        self.supabase.table("migration_sessions").update(
            {
                "source_platform": source_platform,
                "source_format": source_format,
                "config_type": config_type,
                "detection_method": "user_override",
                "detection_confidence": 1.0,
                "user_confirmed": True,
            }
        ).eq("id", session_id).execute()

    def confirm_detection(self, session_id: str) -> None:
        """User confirms the auto-detected result."""
        self.supabase.table("migration_sessions").update(
            {"user_confirmed": True}
        ).eq("id", session_id).execute()
