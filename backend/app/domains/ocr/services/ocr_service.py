# app/domains/ocr/services/ocr_service.py
from app.shared.base_service import BaseService
from typing import Dict, Any
import os


class OCRService(BaseService):
    """OCR 비즈니스 로직 서비스"""

    def __init__(self):
        super().__init__()

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """OCR 입력 데이터 검증"""
        if "image_path" not in input_data:
            return False

        image_path = input_data["image_path"]

        # 파일 존재 확인
        if not os.path.exists(image_path):
            return False

        # 이미지 파일 확장자 검증
        valid_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        _, ext = os.path.splitext(image_path)

        if ext.lower() not in valid_extensions:
            return False

        return True

    def preprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """전처리: 이미지 경로 정규화"""
        if "image_path" in input_data:
            input_data["image_path"] = os.path.abspath(input_data["image_path"])
        return input_data