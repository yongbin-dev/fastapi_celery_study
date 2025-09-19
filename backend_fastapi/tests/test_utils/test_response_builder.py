# tests/test_utils/test_response_builder.py
"""
ResponseBuilder 테스트
"""

import pytest
from datetime import datetime
from app.utils.response_builder import ResponseBuilder


class TestResponseBuilder:
    """ResponseBuilder 테스트 클래스"""

    def test_success_response_basic(self):
        """기본 성공 응답 테스트"""
        response = ResponseBuilder.success(data={"id": 1, "name": "test"}, message="성공")

        assert response.success is True
        assert response.message == "성공"
        assert response.data == {"id": 1, "name": "test"}
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_success_response_with_metadata(self):
        """메타데이터가 포함된 성공 응답 테스트"""
        metadata = {"total": 100, "page": 1, "per_page": 10}
        response = ResponseBuilder.success(
            data={"items": []}, message="조회 성공", metadata=metadata
        )

        assert response.success is True
        assert response.metadata == metadata

    def test_error_response_basic(self):
        """기본 오류 응답 테스트"""
        response = ResponseBuilder.error(message="오류 발생", error_code="TEST_ERROR")

        assert response.success is False
        assert response.message == "오류 발생"
        assert response.data is None
        assert response.error["error_code"] == "TEST_ERROR"
        assert response.error["details"] is None

    def test_error_response_with_details(self):
        """상세 정보가 포함된 오류 응답 테스트"""
        details = {"field": "email", "reason": "invalid format"}
        response = ResponseBuilder.error(
            message="유효성 검사 실패", error_code="VALIDATION_ERROR", details=details
        )

        assert response.success is False
        assert response.error["error_code"] == "VALIDATION_ERROR"
        assert response.error["details"] == details

    def test_paginated_response(self):
        """페이지네이션 응답 테스트"""
        items = [{"id": i, "name": f"item{i}"} for i in range(1, 6)]
        response = ResponseBuilder.paginated(
            items=items, total=100, page=1, per_page=5, message="목록 조회 성공"
        )

        assert response.success is True
        assert response.data == items
        assert response.metadata["pagination"]["total"] == 100
        assert response.metadata["pagination"]["page"] == 1
        assert response.metadata["pagination"]["per_page"] == 5
        assert response.metadata["pagination"]["total_pages"] == 20
        assert response.metadata["pagination"]["has_next"] is True
        assert response.metadata["pagination"]["has_prev"] is False

    def test_created_response(self):
        """생성 응답 테스트"""
        data = {"id": 1, "name": "새 항목"}
        response = ResponseBuilder.created(data=data, message="생성 완료")

        assert response.success is True
        assert response.message == "생성 완료"
        assert response.data == data

    def test_no_content_response(self):
        """내용 없음 응답 테스트"""
        response = ResponseBuilder.no_content(message="삭제 완료")

        assert response.success is True
        assert response.message == "삭제 완료"
        assert response.data is None
