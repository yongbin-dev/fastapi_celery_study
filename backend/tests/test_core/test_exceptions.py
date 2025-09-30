# tests/test_core/test_exceptions.py
"""
예외 처리 테스트
"""

from app.core.exceptions import (
    BaseBusinessException,
    NotFoundError,
    UnauthorizedError,
    UserAlreadyExistsException,
    UserNotFoundException,
    ValidationError,
)


class TestBaseBusinessException:
    """BaseBusinessException 테스트"""

    def test_exception_creation(self):
        """예외 생성 테스트"""
        exc = BaseBusinessException(
            message="테스트 오류",
            error_code="TEST_ERROR",
            status_code=400,
            details={"field": "value"},
        )

        assert exc.message == "테스트 오류"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"field": "value"}

    def test_exception_to_dict(self):
        """예외를 딕셔너리로 변환 테스트"""
        exc = BaseBusinessException(
            message="테스트 오류", error_code="TEST_ERROR", status_code=400
        )

        result = exc.to_dict()
        expected = {
            "error_code": "TEST_ERROR",
            "message": "테스트 오류",
            "status_code": 400,
            "details": {},
        }

        assert result == expected

    def test_exception_str_representation(self):
        """예외 문자열 표현 테스트"""
        exc = BaseBusinessException("테스트 오류", "TEST_ERROR")
        assert str(exc) == "TEST_ERROR: 테스트 오류"


class TestSpecificExceptions:
    """특정 예외들 테스트"""

    def test_validation_error(self):
        """ValidationError 테스트"""
        exc = ValidationError("입력값이 잘못되었습니다")
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_not_found_error(self):
        """NotFoundError 테스트"""
        exc = NotFoundError("사용자를 찾을 수 없습니다")
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404

    def test_unauthorized_error(self):
        """UnauthorizedError 테스트"""
        exc = UnauthorizedError()
        assert exc.error_code == "UNAUTHORIZED"
        assert exc.status_code == 401

    def test_user_not_found_exception(self):
        """UserNotFoundException 테스트"""
        exc = UserNotFoundException(user_id=123)
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["user_id"] == 123

    def test_user_already_exists_exception(self):
        """UserAlreadyExistsException 테스트"""
        exc = UserAlreadyExistsException("email", "test@example.com")
        assert exc.error_code == "USER_ALREADY_EXISTS"
        assert exc.status_code == 400
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "test@example.com"
