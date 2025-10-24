"""Pipeline 패키지

파이프라인 실행을 위한 핵심 컴포넌트들을 제공합니다.
- PipelineContext: 파이프라인 실행 상태 및 데이터 관리
- PipelineStage: 스테이지 추상 기본 클래스
- PipelineOrchestrator: 파이프라인 실행 조율
- Exceptions: 파이프라인 관련 예외 처리
"""

from .context import LLMResult, OCRResult, PipelineContext
from .exceptions import PipelineError, StageError
from .orchestrator import PipelineOrchestrator
from .stage import PipelineStage

__all__ = [
    "PipelineContext",
    "OCRResult",
    "LLMResult",
    "PipelineStage",
    "PipelineOrchestrator",
    "StageError",
    "PipelineError",
]
