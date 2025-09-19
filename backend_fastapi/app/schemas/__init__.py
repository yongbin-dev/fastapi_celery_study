# schemas/__init__.py

# Enums
from .enums import ProcessStatus

# Stage models
from .stage import StageInfo

# Response models
from .responses import (
    TaskStatusResponse,
    PipelineStatusResponse,
    PipelineStagesResponse,
    StageDetailResponse,
)

# Pipeline models
from .pipeline import AIPipelineRequest, AIPipelineResponse
from .predict import PredictResponse, PredictRequest

# Export all for backward compatibility
__all__ = [
    # Enums
    "ProcessStatus",
    # Stage
    "StageInfo",
    # Responses
    "TaskStatusResponse",
    "PipelineStatusResponse",
    "PipelineStagesResponse",
    "StageDetailResponse",
    "PredictResponse",
    "PredictRequest",
    # Pipeline
    "AIPipelineRequest",
    "AIPipelineResponse",
]
