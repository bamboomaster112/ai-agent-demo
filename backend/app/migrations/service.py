"""Migration session service: CRUD + AI interaction."""

import json
from collections.abc import AsyncGenerator

from app.agent.client import get_claude_client
from app.agent.context import get_conversation_history, save_message
from app.agent.parsers import parse_migration_response
from app.agent.prompt_builder import build_system_prompt
from app.agent.vision import build_vision_messages
from app.common.supabase import get_supabase_admin
from app.detection.service import DetectionService


class MigrationService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    def create_session(
        self, user_id: str, title: str | None, source_type: str, source_content: str | None
    ) -> dict:
        """Create a new migration session."""
        data = {
            "user_id": user_id,
            "title": title or f"Migration - {source_type}",
            "source_type": source_type,
            "source_content": source_content,
            "status": "in_progress",
        }

        # Auto-detect if content provided
        if source_content:
            detection_svc = DetectionService()
            platform_result = __import__(
                "app.detection.patterns", fromlist=["detect_platform_and_format"]
            ).detect_platform_and_format(source_content)
            type_result = __import__(
                "app.detection.patterns", fromlist=["detect_config_type"]
            ).detect_config_type(source_content)

            data.update({
                "source_platform": platform_result["source_platform"],
                "source_format": platform_result["source_format"],
                "config_type": type_result["config_type"],
                "detection_method": "heuristic",
                "detection_confidence": platform_result["confidence"],
            })

        result = self.supabase.table("migration_sessions").insert(data).execute()
        return result.data[0]

    def list_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
        result = (
            self.supabase.table("migration_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    def get_session(self, session_id: str, user_id: str) -> dict | None:
        result = (
            self.supabase.table("migration_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return result.data

    def get_session_detail(self, session_id: str, user_id: str) -> dict:
        session = self.get_session(session_id, user_id)
        if not session:
            return None

        messages = (
            self.supabase.table("messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        ).data

        workflows = (
            self.supabase.table("generated_workflows")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .execute()
        ).data

        return {
            "session": session,
            "messages": messages or [],
            "workflows": workflows or [],
        }

    def delete_session(self, session_id: str, user_id: str) -> bool:
        self.supabase.table("migration_sessions").delete().eq(
            "id", session_id
        ).eq("user_id", user_id).execute()
        return True

    def get_messages(self, session_id: str) -> list[dict]:
        result = (
            self.supabase.table("messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    async def stream_ai_response(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        image_data: list[tuple[bytes, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Send a message to Claude and stream the response as SSE events.
        Yields formatted SSE event strings.
        """
        session = self.get_session(session_id, user_id)
        if not session:
            yield f"event: error\ndata: {json.dumps({'message': 'Session not found'})}\n\n"
            return

        # Save user message
        save_message(session_id, "user", user_message)

        # Build system prompt with preferences + RAG
        rag_chunks = await self._get_rag_context(user_message, session)
        system_prompt = await build_system_prompt(
            user_id=user_id,
            source_type=session["source_type"],
            rag_chunks=rag_chunks,
        )

        # Send RAG context info
        if rag_chunks:
            yield f"event: rag\ndata: {json.dumps({'chunks': [{'content': c['content'][:200], 'similarity': c.get('similarity')} for c in rag_chunks]})}\n\n"

        # Build messages
        history = get_conversation_history(session_id)

        # Build the new user message content
        if image_data:
            new_content = build_vision_messages(user_message, image_data)
        else:
            new_content = user_message

        history.append({"role": "user", "content": new_content})

        # Stream from Claude
        client = get_claude_client()
        full_response = ""

        try:
            with client.stream_message(messages=history, system=system_prompt) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield f"event: token\ndata: {json.dumps({'text': text})}\n\n"

            # Parse the complete response
            result = parse_migration_response(full_response)

            # Save assistant message
            save_message(
                session_id,
                "assistant",
                full_response,
                metadata={
                    "has_yaml": len(result.yaml_blocks) > 0,
                    "warning_count": len(result.warnings),
                },
            )

            # Save generated workflows
            for block in result.yaml_blocks:
                self.supabase.table("generated_workflows").insert({
                    "session_id": session_id,
                    "filename": block.filename,
                    "yaml_content": block.content,
                    "notes": [
                        {"level": "warning", "text": w} for w in result.warnings
                    ] + [
                        {"level": "note", "text": n} for n in result.notes
                    ],
                }).execute()

                yield f"event: yaml\ndata: {json.dumps({'filename': block.filename, 'content': block.content})}\n\n"

            # Send notes
            for warning in result.warnings:
                yield f"event: note\ndata: {json.dumps({'level': 'warning', 'text': warning})}\n\n"
            for note in result.notes:
                yield f"event: note\ndata: {json.dumps({'level': 'note', 'text': note})}\n\n"

            # Log usage
            usage = stream.get_final_message().usage
            self.supabase.table("usage_logs").insert({
                "user_id": user_id,
                "session_id": session_id,
                "action": "migration_message",
                "tokens_in": usage.input_tokens,
                "tokens_out": usage.output_tokens,
                "model_used": stream.get_final_message().model,
            }).execute()

            yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    async def _get_rag_context(self, query: str, session: dict) -> list[dict]:
        """Retrieve relevant RAG chunks for the query."""
        try:
            from app.rag.service import RAGService
            rag_service = RAGService()
            chunks = await rag_service.retrieve_context(
                query=query,
                filter_doc_type=None,
                filter_platform=session.get("source_platform"),
            )
            return chunks
        except Exception:
            return []
