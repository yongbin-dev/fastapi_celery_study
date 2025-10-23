"""Pipeline 예외 클래스

파이프라인 및 스테이지 실행 중 발생하는 예외를 정의합니다.
"""


class PipelineError(Exception):
    """파이프라인 실행 중 발생하는 예외

    Attributes:
        message: 에러 메시지
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class StageError(Exception):
    """스테이지 실행 중 발생하는 예외

    Attributes:
        stage_name: 에러가 발생한 스테이지 이름
        message: 에러 메시지
    """

    def __init__(self, stage_name: str, message: str):
        self.stage_name = stage_name
        self.message = message
        super().__init__(f"[{stage_name}] {message}")
