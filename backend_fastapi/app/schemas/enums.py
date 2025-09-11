# schemas/enums.py

from enum import Enum




class ProcessStatus(str, Enum):
    """프로세스 실행 상태"""
    PENDING = "PENDING"      # 대기 중
    STARTED = "STARTED"      # 시작됨
    SUCCESS = "SUCCESS"      # 성공
    FAILURE = "FAILURE"      # 실패
    RETRY = "RETRY"          # 재시도
    REVOKED = "REVOKED"      # 취소됨