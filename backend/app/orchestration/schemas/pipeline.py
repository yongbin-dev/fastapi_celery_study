# schemas/pipeline.py

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.orchestration.schemas.enums import ProcessStatus


class AIPipelineRequest(BaseModel):
    """AI 파이프라인 실행 요청"""

    text: str
    options: Optional[dict] = {}
    priority: int = 5  # 1-10, 높을수록 우선순위
    callback_url: Optional[str] = None  # 완료 시 웹훅 URL


class AIPipelineResponse(BaseModel):
    """AI 파이프라인 응답"""

    pipeline_id: str
    status: str
    message: str
    estimated_duration: Optional[int] = None  # 예상 소요 시간 (초)


class StageResult(BaseModel):
    """스테이지 실행 결과를 위한 모델"""

    chain_id: str = Field(..., description="파이프라인 체인 식별자")
    stage: int = Field(..., ge=1, le=4, description="스테이지 번호")
    result: ProcessStatus = Field(..., description="결과 타입")
    data: Dict[str, Any] = Field(default_factory=dict, description="결과 데이터")
    execution_time: float = Field(..., description="실행 시간(초)")
    success: bool = Field(True, description="성공 여부")
    error_message: Optional[str] = Field(None, description="에러 메시지")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chain_id": "chain_123",
                "stage": 1,
                "result": "SUCCESS",
                "data": {"processed": "data"},
                "execution_time": 2.5,
                "success": True,
            }
        }
    }


class PipelineMetadata(BaseModel):
    """파이프라인 메타데이터를 위한 모델"""

    stage_name: str = Field(..., description="스테이지 이름")
    start_time: float = Field(..., description="시작 시간 (timestamp)")
    execution_time: Optional[float] = Field(0, description="실행 시간(초)")
    error: Optional[str] = Field("", description="에러 메시지")

    model_config = {
        "json_schema_extra": {
            "example": {
                "stage_name": "데이터 전처리",
                "start_time": 1640995200.0,
                "execution_time": 2.5,
            }
        }
    }

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "stage_name": self.stage_name,
            "start_time": self.start_time,
            "execution_time": self.execution_time,
            "error": self.error,
        }
