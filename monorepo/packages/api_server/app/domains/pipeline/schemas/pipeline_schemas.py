"""Pipeline Schemas - 파이프라인 Request/Response 스키마

파이프라인 API의 요청/응답 스키마를 정의합니다.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from shared.schemas.enums import PipelineStatus


class PipelineStartRequest(BaseModel):
    """파이프라인 시작 요청

    Attributes:
        image_path: 처리할 이미지 경로
        options: 추가 옵션
    """

    image_path: str = Field(..., description="처리할 이미지 경로")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 옵션"
    )


class PipelineStartResponse(BaseModel):
    """파이프라인 시작 응답

    Attributes:
        context_id: 생성된 컨텍스트 ID
        status: 초기 상태
        message: 응답 메시지
    """

    context_id: str = Field(..., description="생성된 컨텍스트 ID")
    status: PipelineStatus = Field(..., description="초기 상태")
    message: str = Field(..., description="응답 메시지")

    class Config:
        use_enum_values = True


class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 조회 응답

    Attributes:
        context_id: 컨텍스트 ID
        status: 현재 상태
        data: 스테이지 결과 데이터
        error: 에러 정보 (있는 경우)
    """

    context_id: str = Field(..., description="컨텍스트 ID")
    status: PipelineStatus = Field(..., description="현재 상태")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="스테이지 결과 데이터"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="에러 정보"
    )

    class Config:
        use_enum_values = True
