"""PipelineContext - 파이프라인 실행 상태 및 데이터 관리

전체 파이프라인의 상태, 중간 결과, 메타데이터를 관리합니다.
Redis에 저장되어 여러 스테이지 간 데이터를 공유합니다.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from shared.schemas.ocr_db import TextBoxDTO


class OCRResult(BaseModel):
    """OCR 단계 결과 스키마

    Attributes:
        text: 추출된 텍스트
        confidence: 신뢰도 점수 (0.0 ~ 1.0)
        bboxes: 텍스트 영역 좌표 리스트 (optional)
        metadata: 추가 메타데이터 (엔진 정보, 처리 시간 등)
    """

    text: str = Field(..., description="추출된 텍스트")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 점수")
    bbox: list[TextBoxDTO] = Field(default=[], description="텍스트 영역 좌표 리스트")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="추가 메타데이터"
    )


class LLMResult(BaseModel):
    """LLM 분석 결과 스키마

    Attributes:
        analysis: 분석 결과 텍스트
        confidence: 신뢰도 점수 (0.0 ~ 1.0)
        entities: 추출된 엔티티 정보 (optional)
        metadata: 추가 메타데이터 (모델 정보, 프롬프트, 토큰 사용량 등)
    """

    analysis: str = Field(..., description="분석 결과 텍스트")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 점수")
    entities: Optional[Dict[str, Any]] = Field(
        default=None, description="추출된 엔티티 정보"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="추가 메타데이터"
    )


class PipelineContext(BaseModel):
    """파이프라인 실행 컨텍스트

    Attributes:
        context_id: 고유 컨텍스트 ID
        input_file_path: 입력 파일 경로
        options: 파이프라인 옵션 (OCR 엔진, LLM 모델 등)
        ocr_result: OCR 단계 결과
        llm_result: LLM 분석 결과
        layout_result: 레이아웃 분석 결과
        status: 현재 파이프라인 상태
        current_stage: 현재 실행 중인 스테이지
        error: 에러 메시지
        retry_count: 재시도 횟수
        created_at: 생성 시간
        updated_at: 마지막 업데이트 시간
    """

    # 기본 정보
    context_id: str = Field(..., description="고유 컨텍스트 ID")
    input_file_path: str = Field(..., description="입력 파일 경로")
    options: Dict[str, Any] = Field(default_factory=dict, description="파이프라인 옵션")

    # 단계별 결과 (Pydantic 스키마 사용)
    ocr_result: Optional[OCRResult] = Field(default=None, description="OCR 단계 결과")
    llm_result: Optional[LLMResult] = Field(default=None, description="LLM 분석 결과")
    # layout_result: Optional[Dict[str, Any]] = Field(
    #     default=None, description="레이아웃 분석 결과"
    # )

    # 상태 관리
    status: str = Field(default="pending", description="현재 파이프라인 상태")
    current_stage: Optional[str] = Field(
        default=None, description="현재 실행 중인 스테이지"
    )
    error: Optional[str] = Field(default=None, description="에러 메시지")
    retry_count: int = Field(default=0, description="재시도 횟수")

    # 타임스탬프
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="생성 시간"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="마지막 업데이트 시간",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def set_error(self):
        pass

    def update_status(self, status: str, stage: Optional[str] = None) -> None:
        """상태 업데이트 헬퍼

        Args:
            status: 새로운 상태
            stage: 현재 스테이지 (선택적)
        """
        self.status = status
        if stage:
            self.current_stage = stage
        self.updated_at = datetime.now(timezone.utc)
