# app/domains/ocr/services/ocr_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repository.crud import async_ocr_execution_crud
from app.shared.base_service import BaseService

from ..schemas import OCRResultDTO

logger = get_logger(__name__)


class OCRService(BaseService):
    """OCR 비즈니스 로직 서비스"""

    def __init__(self):
        super().__init__()

    async def get_all_ocr_executions(self, db: AsyncSession):
        ocr_executions = await async_ocr_execution_crud.get_multi_with_text_box(db)
        return [OCRResultDTO.model_validate(ce) for ce in ocr_executions]

ocr_service = OCRService()


def get_ocr_service():
    return ocr_service
