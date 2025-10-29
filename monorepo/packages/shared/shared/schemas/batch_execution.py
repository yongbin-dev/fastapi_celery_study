from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import ProcessStatus


class BatchExecutionCreate(BaseModel):
    """BatchExecution 생성용 스키마"""

    batch_id: str = Field(..., description="배치 고유 ID")
    batch_name: str = Field(..., description="배치 이름")
    total_images: int = Field(..., description="총 이미지 수")
    chunk_size: int = Field(default=10, description="청크당 이미지 수")
    input_data: Optional[Dict[str, Any]] = Field(None, description="입력 데이터 (이미지 경로 목록)")
    options: Optional[Dict[str, Any]] = Field(None, description="파이프라인 옵션")
    initiated_by: Optional[str] = Field(None, description="시작한 사용자/시스템")


class BatchExecutionUpdate(BaseModel):
    """BatchExecution 업데이트용 스키마"""

    status: Optional[ProcessStatus] = Field(None, description="실행 상태")
    completed_images: Optional[int] = Field(None, description="완료된 이미지 수")
    failed_images: Optional[int] = Field(None, description="실패한 이미지 수")
    completed_chunks: Optional[int] = Field(None, description="완료된 청크 수")
    failed_chunks: Optional[int] = Field(None, description="실패한 청크 수")
    final_result: Optional[Dict[str, Any]] = Field(None, description="최종 결과")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class BatchExecutionResponse(BaseModel):
    """BatchExecution 응답용 스키마"""

    id: int
    batch_id: str
    batch_name: str
    status: ProcessStatus
    total_images: int
    completed_images: int
    failed_images: int
    total_chunks: int
    completed_chunks: int
    failed_chunks: int
    chunk_size: int
    progress_percentage: float = Field(..., description="진행률 (0-100)")
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    initiated_by: Optional[str]
    input_data: Optional[Dict[str, Any]]
    options: Optional[Dict[str, Any]]
    final_result: Optional[Dict[str, Any]]
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BatchStartRequest(BaseModel):
    """배치 시작 요청 스키마"""

    batch_name: str = Field(..., description="배치 이름")
    file_paths: List[str] = Field(..., description="처리할 이미지 파일 경로 목록")
    public_file_paths: List[str] = Field(..., description="공개 이미지 파일 경로 목록")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="파이프라인 옵션")
    chunk_size: int = Field(default=10, ge=1, le=100, description="청크당 이미지 수 (1-100)")
    initiated_by: Optional[str] = Field(default="api_server", description="시작한 사용자/시스템")


class BatchStatusResponse(BaseModel):
    """배치 상태 응답 스키마"""

    batch_id: str
    status: ProcessStatus
    total_images: int
    completed_images: int
    failed_images: int
    progress_percentage: float
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    estimated_time_remaining: Optional[float] = Field(None, description="예상 남은 시간 (초)")


# Forward reference 해결을 위한 모델 업데이트
BatchExecutionResponse.model_rebuild()
