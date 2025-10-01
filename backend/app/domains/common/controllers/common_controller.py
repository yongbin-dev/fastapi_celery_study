# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.domains.common.services.common_service import CommonService, get_common_service
from app.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/common", tags=["COMMON"])


@router.get("/images")
async def get_image(
    service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):

    list = await service.get_ocr_list(db)
    return ResponseBuilder.success(data=list, message="COMMON 서비스 정상")


@router.get("/ocr-images")
async def get_image_list(
    service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):

    list = await service.get_ocr_list(db)
    return ResponseBuilder.success(data=list, message="COMMON 서비스 정상")


@router.get("/ocr-images/{id}")
async def get_image_by_id(
    id: int,
    service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):

    list = await service.get_image_by_id(db, id)
    return ResponseBuilder.success(data=list, message="COMMON 서비스 정상")


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return ResponseBuilder.success(
        data={"status": "healthy"}, message="COMMON 서비스 정상"
    )
