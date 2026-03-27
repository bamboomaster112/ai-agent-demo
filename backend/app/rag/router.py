from fastapi import APIRouter, Depends, Query

from app.dependencies import UserContext, get_current_user, require_admin
from app.rag.models import DocumentCreate, DocumentResponse, RAGConfigUpdate, SearchRequest
from app.rag.service import RAGService

router = APIRouter()


def get_rag_service() -> RAGService:
    return RAGService()


@router.post("/documents", response_model=DocumentResponse)
async def upload_document(
    body: DocumentCreate,
    user: UserContext = Depends(require_admin),
    service: RAGService = Depends(get_rag_service),
):
    result = service.ingest_document(
        doc_type=body.doc_type,
        content=body.content,
        title=body.title,
        source_platform=body.source_platform,
        metadata=body.metadata,
        user_id=user.id,
    )
    return result


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    user: UserContext = Depends(require_admin),
    service: RAGService = Depends(get_rag_service),
    doc_type: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    return service.list_documents(doc_type=doc_type, limit=limit, offset=offset)


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    user: UserContext = Depends(require_admin),
    service: RAGService = Depends(get_rag_service),
):
    service.delete_document(doc_id)
    return {"status": "deleted"}


@router.post("/search")
async def search_documents(
    body: SearchRequest,
    user: UserContext = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
):
    results = service.retrieve_context(
        query=body.query,
        filter_doc_type=body.doc_type,
        filter_platform=body.source_platform,
        top_k=body.top_k,
        threshold=body.threshold,
    )
    return {"results": results}


@router.get("/config")
async def get_rag_config(
    user: UserContext = Depends(require_admin),
    service: RAGService = Depends(get_rag_service),
):
    return service._get_rag_config()


@router.put("/config")
async def update_rag_config(
    body: RAGConfigUpdate,
    user: UserContext = Depends(require_admin),
    service: RAGService = Depends(get_rag_service),
):
    from app.common.supabase import get_supabase_admin
    supabase = get_supabase_admin()
    supabase.table("rag_config").update(
        {"value": body.value, "updated_by": user.id}
    ).eq("key", body.key).execute()
    return {"status": "updated"}
