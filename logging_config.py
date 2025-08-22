# logging_config.py - 로깅 설정
import logging
import sys
from datetime import datetime


def setup_logging():
    """로깅 설정 초기화"""

    # 로거 생성
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if logger.handlers:
        return logger

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 파일 핸들러 (선택적)
    file_handler = logging.FileHandler(
        f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # 포맷터 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger