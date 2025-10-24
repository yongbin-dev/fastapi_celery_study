"""Pipeline 예외 클래스

파이프라인 및 스테이지 실행 중 발생하는 예외를 정의합니다.
"""


class PipelineError(Exception):
    """파이프라인 기본 예외

    Attributes:
        message: 에러 메시지
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class StageError(PipelineError):
    """스테이지 실행 실패

    Attributes:
        stage_name: 에러가 발생한 스테이지 이름
        message: 에러 메시지
    """

    def __init__(self, stage_name: str, message: str):
        self.stage_name = stage_name
        self.message = message
        super().__init__(f"[{stage_name}] {message}")


class RetryableError(StageError):
    """재시도 가능한 오류 (네트워크, 일시적 오류)

    네트워크 오류, 서버 오류 등 재시도로 해결 가능한 오류를 나타냅니다.
    Celery의 autoretry_for에 사용됩니다.

    Attributes:
        stage_name: 에러가 발생한 스테이지 이름
        message: 에러 메시지
    """

    pass


class FatalError(StageError):
    """재시도 불가능한 치명적 오류 (데이터 오류, 설정 오류)

    재시도해도 해결되지 않는 오류를 나타냅니다.
    예: 데이터 형식 오류, 설정 오류, 권한 오류 등

    Attributes:
        stage_name: 에러가 발생한 스테이지 이름
        message: 에러 메시지
    """

    pass


class ValidationError(FatalError):
    """입력/출력 검증 실패

    데이터 검증에 실패한 경우 발생합니다.
    예: 필수 필드 누락, 데이터 타입 불일치 등

    Attributes:
        stage_name: 에러가 발생한 스테이지 이름
        message: 에러 메시지
    """

    pass
