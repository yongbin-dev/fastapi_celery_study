# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter

from app.core.logging import get_logger
from app.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/common", tags=["COMMON"])

@router.get("/health")
async def health_check():
    """헬스 체크"""
    return ResponseBuilder.success(
        data={"status": "healthy"}, message="OCR 서비스 정상"
    )
