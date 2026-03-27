from pydantic import BaseModel


class DocumentCreate(BaseModel):
    doc_type: str
    source_platform: str | None = None
    title: str | None = None
    content: str
    metadata: dict = {}


class DocumentResponse(BaseModel):
    id: str
    doc_type: str
    source_platform: str | None
    title: str | None
    metadata: dict
    created_at: str


class SearchRequest(BaseModel):
    query: str
    doc_type: str | None = None
    source_platform: str | None = None
    top_k: int = 5
    threshold: float = 0.75


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    similarity: float
    metadata: dict = {}


class RAGConfigUpdate(BaseModel):
    key: str
    value: dict
