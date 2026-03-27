from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.dependencies import UserContext, get_current_user
from app.uploads.service import UploadService

router = APIRouter()


def get_upload_service() -> UploadService:
    return UploadService()


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user: UserContext = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service),
):
    file_bytes = await file.read()
    result = service.upload_file(
        user_id=user.id,
        session_id=session_id,
        file_bytes=file_bytes,
        file_name=file.filename or "unnamed",
        mime_type=file.content_type or "application/octet-stream",
    )
    return result


@router.get("/{upload_id}/url")
async def get_signed_url(
    upload_id: str,
    user: UserContext = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service),
):
    url = service.get_signed_url(upload_id, user.id)
    return {"url": url}
