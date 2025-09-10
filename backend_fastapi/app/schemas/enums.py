# schemas/enums.py

from enum import Enum


class TaskStatus(str, Enum):
    """Celery 태스크 상태"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class StageStatus(str, Enum):
    """Stage 상태를 나타내는 Enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(str, Enum):
    """파이프라인 단계"""
    PREPROCESSING = "preprocessing"
    FEATURE_EXTRACTION = "feature_extraction"
    MODEL_INFERENCE = "model_inference"
    POST_PROCESSING = "post_processing"