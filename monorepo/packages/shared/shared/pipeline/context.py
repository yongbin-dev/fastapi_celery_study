"""PipelineContext - 파이프라인 실행 상태 및 데이터 관리

전체 파이프라인의 상태, 중간 결과, 메타데이터를 관리합니다.
Redis에 저장되어 여러 스테이지 간 데이터를 공유합니다.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from shared.schemas.enums import PipelineStatus


class PipelineContext(BaseModel):
    """파이프라인 실행 컨텍스트

    Attributes:
        context_id: 고유 컨텍스트 ID
        status: 현재 파이프라인 상태
        data: 스테이지 간 공유 데이터
        metadata: 실행 메타데이터 (시작 시간, 종료 시간 등)
        error: 에러 정보 (발생 시)
    """

    context_id: str = Field(..., description="고유 컨텍스트 ID")
    status: PipelineStatus = Field(
        default=PipelineStatus.PENDING,
        description="파이프라인 실행 상태"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="스테이지 간 공유 데이터"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="실행 메타데이터"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="에러 정보"
    )

    class Config:
        use_enum_values = True

    def update_status(self, status: PipelineStatus) -> None:
        """파이프라인 상태 업데이트"""
        self.status = status
        self.metadata["last_updated"] = datetime.utcnow().isoformat()

    def set_stage_data(self, stage_name: str, data: Any) -> None:
        """특정 스테이지의 결과 데이터 저장"""
        self.data[stage_name] = data
        self.metadata["last_updated"] = datetime.utcnow().isoformat()

    def get_stage_data(self, stage_name: str) -> Optional[Any]:
        """특정 스테이지의 결과 데이터 조회"""
        return self.data.get(stage_name)

    def set_error(self, stage_name: str, error: str, traceback: Optional[str] = None):
        """에러 정보 저장"""
        self.error = {
            "stage": stage_name,
            "error": error,
            "traceback": traceback,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.update_status(PipelineStatus.FAILURE)
