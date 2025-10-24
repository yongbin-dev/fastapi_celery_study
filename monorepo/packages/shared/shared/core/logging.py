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


class ColoredFormatter(logging.Formatter):
    """컬러가 적용된 로그 포맷터"""

    COLORS = {
        "DEBUG": "\033[36m",  # 청록색
        "INFO": "\033[32m",  # 녹색
        "WARNING": "\033[33m",  # 노란색
        "ERROR": "\033[31m",  # 빨간색
        "CRITICAL": "\033[35m",  # 자홍색
        "RESET": "\033[0m",  # 리셋
    }

    def format(self, record: logging.LogRecord) -> str:
        # 기본 포맷팅 적용
        formatted = super().format(record)

        # 컬러 적용
        if record.levelname in self.COLORS:
            color_code = self.COLORS[record.levelname]
            reset_code = self.COLORS["RESET"]

            # 레벨명에만 색상 적용
            formatted = formatted.replace(
                f"| {record.levelname:8s} |",
                f"| {color_code}{record.levelname:8s}{reset_code} |",
            )

        return formatted


class LoggingManager:
    """로깅 관리자 클래스"""

    def __init__(self):
        # 서비스 이름 자동 감지
        service_name = self._detect_service_name()

        # monorepo 루트 디렉토리 설정 (현재 파일 위치 기반)
        # packages/shared/shared/core/logging.py -> 4 levels up
        monorepo_root = Path(__file__).resolve().parents[4]

        # 오늘 날짜
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 로그 디렉토리 경로 구성
        self.log_dir = monorepo_root / "logs" / service_name / today_str

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

    def _detect_service_name(self) -> str:
        """
        실행 중인 프로세스의 경로를 분석하여 서비스 이름 자동 감지

        Returns:
            str: 감지된 서비스 이름 (api_server, celery_worker, ml_server 등)
        """
        # 환경 변수가 설정되어 있으면 우선 사용
        env_service_name = os.getenv("SERVICE_NAME")
        if env_service_name:
            return env_service_name

        # 현재 실행 중인 스크립트의 경로 분석
        import traceback

        # 스택 트레이스에서 packages 디렉토리 아래의 경로 찾기
        for frame_info in traceback.extract_stack():
            filepath = Path(frame_info.filename)
            parts = filepath.parts

            # packages 디렉토리를 포함하는 경로인지 확인
            if "packages" in parts:
                packages_idx = parts.index("packages")
                # packages 다음에 오는 디렉토리가 서비스 이름
                if packages_idx + 1 < len(parts):
                    service_dir = parts[packages_idx + 1]
                    # shared는 제외 (공통 라이브러리)
                    if service_dir != "shared":
                        return service_dir

        # 감지 실패 시 기본값
        return "unknown"

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
        console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        file_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(funcName)s:%(lineno)d | %(message)s"
        )

        date_format = "%Y-%m-%d %H:%M:%S"

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

    def _can_write_log_file(self, log_file: Path) -> bool:
        """로그 파일에 쓰기 권한이 있는지 확인"""
        try:
            # 파일이 존재하면 쓰기 권한 확인
            if log_file.exists():
                # 테스트 쓰기 시도
                with open(log_file, "a", encoding="utf-8"):
                    pass
                return True
            # 파일이 없으면 디렉토리 쓰기 권한 확인
            else:
                return os.access(log_file.parent, os.W_OK)
        except (PermissionError, OSError):
            return False

    def _setup_file_handlers(self, root_logger, file_format, date_format):
        """파일 핸들러들 설정"""
        file_formatter = logging.Formatter(file_format, date_format)

        # 2. 에러 전용 로그 파일
        error_log_file = self.log_dir / "error.log"
        if self._can_write_log_file(error_log_file):
            try:
                error_handler = logging.handlers.RotatingFileHandler(
                    error_log_file,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=10,
                    encoding="utf-8",
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(file_formatter)
                root_logger.addHandler(error_handler)
            except Exception as e:
                print(f"에러 로그 파일 핸들러 생성 실패: {e}", file=sys.stderr)

        # 3. 일별 로그 파일
        daily_log_file = self.log_dir / "app.log"
        if self._can_write_log_file(daily_log_file):
            try:
                daily_handler = logging.FileHandler(daily_log_file, encoding="utf-8")
                daily_handler.setLevel(logging.INFO)
                daily_handler.setFormatter(file_formatter)
                root_logger.addHandler(daily_handler)
            except Exception as e:
                print(f"일별 로그 파일 핸들러 생성 실패: {e}", file=sys.stderr)

        # 4. Celery 전용 로그 파일
        celery_log_file = self.log_dir / "celery.log"
        if self._can_write_log_file(celery_log_file):
            try:
                celery_handler = logging.FileHandler(celery_log_file, encoding="utf-8")
                celery_handler.setLevel(logging.INFO)
                celery_handler.setFormatter(file_formatter)

                # Celery 로거들에만 이 핸들러 추가
                celery_logger_names = [
                    "celery",
                    "celery.worker",
                    "celery.task",
                    "celery.beat",
                    "celery.app",
                    "celery.redirected",
                ]
                for logger_name in celery_logger_names:
                    celery_logger = logging.getLogger(logger_name)
                    celery_logger.addHandler(celery_handler)
            except Exception as e:
                print(f"Celery 로그 파일 핸들러 생성 실패: {e}", file=sys.stderr)

        # 5. DB 전용 로그 파일 (파일에만 기록, 콘솔 출력 안 함)
        db_log_file = self.log_dir / "db.log"
        if self._can_write_log_file(db_log_file):
            try:
                db_handler = logging.FileHandler(db_log_file, encoding="utf-8")
                db_handler.setLevel(logging.INFO)
                db_handler.setFormatter(file_formatter)

                # SQLAlchemy 로거들 설정
                db_logger_names = [
                    "sqlalchemy.engine",
                    "sqlalchemy.pool",
                    "sqlalchemy.dialects",
                    "sqlalchemy.orm",
                ]
                for logger_name in db_logger_names:
                    db_logger = logging.getLogger(logger_name)
                    # 기존 핸들러 모두 제거
                    db_logger.handlers.clear()
                    # DB 파일 핸들러만 추가
                    db_logger.addHandler(db_handler)
                    # 상위 로거로 전파하지 않음 (콘솔 출력 방지)
                    db_logger.propagate = False
            except Exception as e:
                print(f"DB 로그 파일 핸들러 생성 실패: {e}", file=sys.stderr)

        # 6. HTTP 요청/응답 로그 파일
        http_log_file = self.log_dir / "http.log"
        if self._can_write_log_file(http_log_file):
            try:
                http_handler = logging.FileHandler(http_log_file, encoding="utf-8")
                http_handler.setLevel(logging.INFO)
                http_handler.setFormatter(file_formatter)

                # HTTP 로거들 설정
                http_logger_names = [
                    "app.core.middleware.request_middleware",
                    "app.core.middleware.response_middleware",
                ]
                for logger_name in http_logger_names:
                    http_logger = logging.getLogger(logger_name)
                    http_logger.addHandler(http_handler)
            except Exception as e:
                print(f"HTTP 로그 파일 핸들러 생성 실패: {e}", file=sys.stderr)

        # 7. JSON 형식 로그 (구조화된 로그)
        enable_json_logs = os.getenv("ENABLE_JSON_LOGS", "false").lower() == "true"
        if enable_json_logs:
            self._setup_json_handler(root_logger)

    def _setup_json_handler(self, root_logger):
        """JSON 형식 로그 핸들러 설정"""
        try:
            import json

            class JSONFormatter(logging.Formatter):
                def format(self, record: logging.LogRecord) -> str:
                    log_entry = {
                        "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                    }

                    if record.exc_info:
                        log_entry["exception"] = self.formatException(record.exc_info)

                    return json.dumps(log_entry, ensure_ascii=False)

            json_log_file = self.log_dir / "app.json"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
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

        # SQLAlchemy 로그 설정 - 파일에만 기록, 콘솔 출력 안 함
        # DB_ECHO 설정과 관계없이 항상 INFO 레벨로 파일에 기록
        db_logger_names = [
            "sqlalchemy.engine",
            "sqlalchemy.pool",
            "sqlalchemy.dialects",
            "sqlalchemy.orm",
        ]
        for logger_name in db_logger_names:
            db_logger = logging.getLogger(logger_name)
            db_logger.setLevel(logging.INFO)
            # 콘솔 출력 방지 - 파일에만 기록
            db_logger.propagate = False

        # HTTP 요청 로그 조정
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        # Celery 로그 설정 - 세밀한 제어
        celery_loggers = {
            "celery": logging.INFO,
            "celery.worker": logging.INFO,
            "celery.task": logging.INFO,
            "celery.beat": logging.INFO,
            "celery.app": logging.INFO,
            "celery.redirected": logging.INFO,
            "celery.worker.strategy": logging.WARNING,  # 너무 자세한 로그 제한
            "celery.worker.consumer": logging.WARNING,
            "celery.worker.heartbeat": logging.WARNING,
        }

        for logger_name, level in celery_loggers.items():
            logging.getLogger(logger_name).setLevel(level)

        # Redis 로그 설정
        logging.getLogger("redis").setLevel(logging.WARNING)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """로거 인스턴스 가져오기"""
        return logging.getLogger(name)

    def add_context_filter(self, filter_class: type[logging.Filter]) -> None:
        """컨텍스트 필터 추가"""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.addFilter(filter_class())


# 전역 로깅 매니저 인스턴스
logging_manager = LoggingManager()


# 편의 함수
def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 가져오기"""
    return logging_manager.get_logger(name)
