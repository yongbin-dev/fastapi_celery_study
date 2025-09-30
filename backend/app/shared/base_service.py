# app/shared/base_service.py
from typing import Any, Dict


class BaseService:
    """공통 서비스 로직을 위한 베이스 클래스"""

    def __init__(self):
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """입력 데이터 검증"""
        return True

    def preprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """전처리 로직"""
        return input_data

    def postprocess(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """후처리 로직"""
        return output_data
