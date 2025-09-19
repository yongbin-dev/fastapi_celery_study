# schemas/enums.py

from enum import Enum


class ProcessStatus(str, Enum):
    PENDING = "PENDING"  # 대기 중
    STARTED = "STARTED"  # 시작됨
    SUCCESS = "SUCCESS"  # 성공
    RUNNING = "RUNNING"  # 진행 중
    FAILURE = "FAILURE"  # 실패
    RETRY = "RETRY"  # 재시도
    REVOKED = "REVOKED"  # 취소됨
