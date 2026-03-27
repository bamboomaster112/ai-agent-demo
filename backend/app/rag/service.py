"""RAG service: document management, chunking, embedding, retrieval."""

import json

from app.common.supabase import get_supabase_admin
from app.rag.chunking import get_chunker
from app.rag.embedding import generate_embeddings_batch, generate_query_embedding


class RAGService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    def _get_rag_config(self) -> dict:
        """Load RAG configuration from database."""
        try:
            result = self.supabase.table("rag_config").select("key, value").execute()
            config = {}
            for row in result.data:
                config[row["key"]] = row["value"]
            return config
        except Exception:
            return {
                "chunk_size": {"tokens": 512},
                "chunk_overlap": {"tokens": 64},
                "top_k": {"value": 5},
                "similarity_threshold": {"value": 0.75},
            }

    def ingest_document(
        self,
        doc_type: str,
        content: str,
        title: str | None = None,
        source_platform: str | None = None,
        metadata: dict | None = None,
        user_id: str | None = None,
        source_format: str | None = None,
    ) -> dict:
        """Ingest a document: create record, chunk, embed, store."""
        config = self._get_rag_config()
        chunk_size = config.get("chunk_size", {}).get("tokens", 512)
        chunk_overlap = config.get("chunk_overlap", {}).get("tokens", 64)

        # Create document record
        doc_result = (
            self.supabase.table("documents")
            .insert({
                "doc_type": doc_type,
                "source_platform": source_platform,
                "title": title,
                "original_content": content,
                "metadata": metadata or {},
                "user_id": user_id,
            })
            .execute()
        )
        doc_id = doc_result.data[0]["id"]

        # Chunk the content
        chunker = get_chunker(source_format=source_format, doc_type=doc_type)
        chunks = chunker.chunk(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        if not chunks:
            return doc_result.data[0]

        # Generate embeddings in batch
        chunk_texts = [c.content for c in chunks]
        embeddings = generate_embeddings_batch(chunk_texts)

        # Store chunks with embeddings
        chunk_records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_records.append({
                "document_id": doc_id,
                "chunk_index": i,
                "content": chunk.content,
                "token_count": chunk.token_count,
                "embedding": embedding,
                "metadata": chunk.metadata,
            })

        self.supabase.table("document_chunks").insert(chunk_records).execute()

        return doc_result.data[0]

    def retrieve_context(
        self,
        query: str,
        filter_doc_type: str | None = None,
        filter_platform: str | None = None,
        top_k: int | None = None,
        threshold: float | None = None,
    ) -> list[dict]:
        """Retrieve relevant document chunks for a query."""
        config = self._get_rag_config()
        top_k = top_k or config.get("top_k", {}).get("value", 5)
        threshold = threshold or config.get("similarity_threshold", {}).get("value", 0.75)

        # Generate query embedding
        query_embedding = generate_query_embedding(query)

        # Call the similarity search function
        result = self.supabase.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": top_k,
                "filter_doc_type": filter_doc_type,
                "filter_platform": filter_platform,
            },
        ).execute()

        # Enrich with document info
        chunks = result.data or []
        for chunk in chunks:
            doc = (
                self.supabase.table("documents")
                .select("title, doc_type, source_platform")
                .eq("id", chunk["document_id"])
                .single()
                .execute()
            )
            if doc.data:
                chunk["title"] = doc.data.get("title")
                chunk["doc_type"] = doc.data.get("doc_type")

        return chunks

    def list_documents(
        self,
        doc_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        query = self.supabase.table("documents").select(
            "id, doc_type, source_platform, title, metadata, created_at"
        )
        if doc_type:
            query = query.eq("doc_type", doc_type)
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return result.data or []

    def delete_document(self, doc_id: str) -> None:
        """Delete a document and its chunks (cascade)."""
        self.supabase.table("documents").delete().eq("id", doc_id).execute()

    def auto_ingest_migration(
        self, session_id: str, user_id: str
    ) -> dict | None:
        """Auto-ingest a successful migration as a RAG document."""
        session = (
            self.supabase.table("migration_sessions")
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        ).data

        if not session or not session.get("source_content"):
            return None

        workflows = (
            self.supabase.table("generated_workflows")
            .select("yaml_content, filename")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ).data

        if not workflows:
            return None

        # Create combined content for RAG
        combined = json.dumps({
            "source": session["source_content"],
            "target": workflows[0]["yaml_content"],
            "source_type": session["source_type"],
            "config_type": session.get("config_type"),
        })

        return self.ingest_document(
            doc_type="migration_result",
            content=combined,
            title=session.get("title", f"Migration {session_id[:8]}"),
            source_platform=session.get("source_platform"),
            metadata={"session_id": session_id},
            user_id=user_id,
            source_format=session.get("source_format"),
        )
