from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import ProcessStatus
from .task_log import TaskLogResponse


class ChainExecutionCreate(BaseModel):
    """ChainExecution 생성용 스키마"""

    chain_id: str = Field(..., description="체인 ID")
    chain_name: str = Field(..., description="체인 이름")
    total_tasks: int = Field(..., description="총 작업 수")
    input_data: Optional[Dict[str, Any]] = Field(None, description="입력 데이터")
    initiated_by: Optional[str] = Field(None, description="시작한 사용자/시스템")


class ChainExecutionUpdate(BaseModel):
    """ChainExecution 업데이트용 스키마"""

    chain_name: Optional[str] = Field(None, description="체인 이름")
    status: Optional[ProcessStatus] = Field(None, description="실행 상태")
    completed_tasks: Optional[int] = Field(None, description="완료된 작업 수")
    failed_tasks: Optional[int] = Field(None, description="실패한 작업 수")
    final_result: Optional[Dict[str, Any]] = Field(None, description="최종 결과")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class ChainExecutionResponse(BaseModel):
    """ChainExecution 응답용 스키마"""

    id: int
    chain_id: str
    status: ProcessStatus
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    initiated_by: Optional[str]
    input_data: Optional[Dict[str, Any]]
    final_result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    task_logs: List[TaskLogResponse] = Field(
        default_factory=list,
        description="관련 작업 로그 목록"
    )

    model_config = ConfigDict(from_attributes=True)



# Forward reference 해결을 위한 모델 업데이트
ChainExecutionResponse.model_rebuild()
