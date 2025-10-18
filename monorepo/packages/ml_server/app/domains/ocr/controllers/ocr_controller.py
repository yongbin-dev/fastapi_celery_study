# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.get("/languages")
async def get_supported_languages():
    """지원하는 언어 목록 조회"""
    languages = [
        {"code": "korean", "name": "한국어"},
        {"code": "english", "name": "영어"},
        {"code": "chinese", "name": "중국어"},
        {"code": "japanese", "name": "일본어"},
    ]

    return ResponseBuilder.success(
        data={"languages": languages}, message="지원 언어 목록"
    )


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return ResponseBuilder.success(
        data={"status": "healthy"}, message="OCR 서비스 정상"
    )
