# app/core/logging.py
"""
로깅 설정 및 관리
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """컬러가 적용된 로그 포맷터"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 청록색
        'INFO': '\033[32m',       # 녹색
        'WARNING': '\033[33m',    # 노란색
        'ERROR': '\033[31m',      # 빨간색
        'CRITICAL': '\033[35m',   # 자홍색
        'RESET': '\033[0m'        # 리셋
    }

    def format(self, record):
        # 기본 포맷팅 적용
        formatted = super().format(record)
        
        # 컬러 적용
        if record.levelname in self.COLORS:
            color_code = self.COLORS[record.levelname]
            reset_code = self.COLORS['RESET']
            
            # 레벨명에만 색상 적용
            formatted = formatted.replace(
                f"| {record.levelname:8s} |",
                f"| {color_code}{record.levelname:8s}{reset_code} |"
            )
        
        return formatted


class LoggingManager:
    """로깅 관리자 클래스"""

    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logging()

    def _setup_logging(self):
        """로깅 설정 초기화"""
        # 환경변수에서 직접 설정 읽기 (순환 import 방지)
        log_level = os.getenv("LOG_LEVEL", "INFO")
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
        
        # 기본 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # 기존 핸들러 제거
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 포맷터 설정
        console_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        file_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
        
        date_format = '%Y-%m-%d %H:%M:%S'

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        console_formatter = ColoredFormatter(console_format, date_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 파일 핸들러들
        if log_to_file:
            self._setup_file_handlers(root_logger, file_format, date_format)
        
        # 외부 라이브러리 로깅 레벨 조정
        self._configure_external_loggers()

    def _setup_file_handlers(self, root_logger, file_format, date_format):
        """파일 핸들러들 설정"""
        file_formatter = logging.Formatter(file_format, date_format)
        
        # 1. 전체 로그 파일 (회전 로그)
        all_log_file = self.log_dir / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            all_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # 2. 에러 전용 로그 파일
        error_log_file = self.log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

        # 3. 일별 로그 파일
        today = datetime.now().strftime('%Y-%m-%d')
        daily_log_file = self.log_dir / f"app_{today}.log"
        daily_handler = logging.FileHandler(
            daily_log_file,
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(file_formatter)
        root_logger.addHandler(daily_handler)

        # 4. JSON 형식 로그 (구조화된 로그)
        enable_json_logs = os.getenv('ENABLE_JSON_LOGS', 'false').lower() == 'true'
        if enable_json_logs:
            self._setup_json_handler(root_logger)

    def _setup_json_handler(self, root_logger):
        """JSON 형식 로그 핸들러 설정"""
        try:
            import json
            
            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_entry = {
                        'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                        'level': record.levelname,
                        'logger': record.name,
                        'message': record.getMessage(),
                        'module': record.module,
                        'function': record.funcName,
                        'line': record.lineno,
                    }
                    
                    if record.exc_info:
                        log_entry['exception'] = self.formatException(record.exc_info)
                    
                    # 추가 필드들
                    if hasattr(record, 'user_id'):
                        log_entry['user_id'] = record.user_id
                    if hasattr(record, 'request_id'):
                        log_entry['request_id'] = record.request_id
                    
                    return json.dumps(log_entry, ensure_ascii=False)

            json_log_file = self.log_dir / "app.json"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.INFO)
            json_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(json_handler)
            
        except ImportError:
            logging.warning("JSON 로그 기능을 사용하려면 json 모듈이 필요합니다")

    def _configure_external_loggers(self):
        """외부 라이브러리 로거들 설정"""
        # uvicorn 로그 레벨 조정
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
        
        # SQLAlchemy 로그 설정
        db_echo = os.getenv("DB_ECHO", "false").lower() == "true"
        if db_echo:
            logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        else:
            logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
        # HTTP 요청 로그 조정
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        
        # Celery 로그 설정
        logging.getLogger("celery").setLevel(logging.INFO)
        
        # Redis 로그 설정
        logging.getLogger("redis").setLevel(logging.WARNING)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """로거 인스턴스 가져오기"""
        return logging.getLogger(name)

    def add_context_filter(self, filter_class):
        """컨텍스트 필터 추가"""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.addFilter(filter_class())


class RequestContextFilter(logging.Filter):
    """요청 컨텍스트 정보를 로그에 추가하는 필터"""
    
    def filter(self, record):
        # 여기서 요청 컨텍스트 정보를 추가할 수 있습니다
        # 예: record.request_id = get_request_id()
        return True


class UserContextFilter(logging.Filter):
    """사용자 컨텍스트 정보를 로그에 추가하는 필터"""
    
    def filter(self, record):
        # 여기서 사용자 정보를 추가할 수 있습니다
        # 예: record.user_id = get_current_user_id()
        return True


# 전역 로깅 매니저 인스턴스
logging_manager = LoggingManager()

# 편의 함수
def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 가져오기"""
    return logging_manager.get_logger(name)


# 로깅 데코레이터
def log_function_call(logger: Optional[logging.Logger] = None):
    """함수 호출을 로깅하는 데코레이터"""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            logger.debug(f"함수 호출 시작: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"함수 호출 완료: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"함수 호출 오류: {func.__name__} - {str(e)}")
                raise
        
        return wrapper
    return decorator


def log_execution_time(logger: Optional[logging.Logger] = None):
    """함수 실행 시간을 로깅하는 데코레이터"""
    import time
    
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"함수 실행 시간: {func.__name__} - {execution_time:.4f}초")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"함수 실행 오류 (소요 시간: {execution_time:.4f}초): {func.__name__} - {str(e)}")
                raise
        
        return wrapper
    return decorator