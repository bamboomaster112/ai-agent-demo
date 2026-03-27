from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import UserContext, get_current_user
from app.detection.service import DetectionService

router = APIRouter()


def get_detection_service() -> DetectionService:
    return DetectionService()


class DetectRequest(BaseModel):
    content: str
    filename: str | None = None


class DetectResponse(BaseModel):
    source_platform: str
    source_format: str
    config_type: str
    confidence: float
    method: str
    matched_patterns: list[str] = []


class OverrideRequest(BaseModel):
    source_platform: str
    source_format: str
    config_type: str


@router.post("/", response_model=DetectResponse)
async def detect_pipeline(
    body: DetectRequest,
    user: UserContext = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
):
    result = await service.detect(body.content, body.filename)
    return result.to_dict()


@router.put("/migrations/{session_id}/detection")
async def override_detection(
    session_id: str,
    body: OverrideRequest,
    user: UserContext = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
):
    service.update_detection(
        session_id, body.source_platform, body.source_format, body.config_type
    )
    return {"status": "updated"}


@router.post("/migrations/{session_id}/confirm-detection")
async def confirm_detection(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    service: DetectionService = Depends(get_detection_service),
):
    service.confirm_detection(session_id)
    return {"status": "confirmed"}
