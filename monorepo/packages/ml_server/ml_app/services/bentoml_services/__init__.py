"""BentoML 서비스 모듈"""

from ml_app.services.bentoml_services.ocr_service import OCRBentoService

# 새로운 서비스 추가 시:
# from ml_app.bentoml_services.llm_service import LLMBentoService

__all__ = [
    "OCRBentoService",
    # "LLMBentoService",  # 추가 시 주석 해제
]
