# app/domains/ocr/schemas/similarity.py
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SimilarityRequest(BaseModel):
    """유사도 측정 요청 스키마"""

    execution_id1: int = Field(..., description="첫 번째 OCR 실행 ID")
    execution_id2: int = Field(..., description="두 번째 OCR 실행 ID")
    method: str = Field(
        default="all",
        description="유사도 측정 방법 (string, token, semantic, all)",
    )
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="각 방법의 가중치 (string, token, semantic)",
    )


class SimilarityMetrics(BaseModel):
    """상세 유사도 메트릭"""

    levenshtein_distance: Optional[int] = Field(
        None, description="Levenshtein 편집 거리"
    )
    levenshtein_similarity: Optional[float] = Field(
        None, description="Levenshtein 유사도 (0.0~1.0)"
    )
    jaro_winkler: Optional[float] = Field(None, description="Jaro-Winkler 유사도")
    sequence_matcher: Optional[float] = Field(
        None, description="SequenceMatcher 유사도"
    )
    jaccard_index: Optional[float] = Field(None, description="Jaccard 유사도")
    cosine_similarity: Optional[float] = Field(None, description="Cosine 유사도")
    semantic_similarity: Optional[float] = Field(None, description="의미론적 유사도")


class TextComparison(BaseModel):
    """텍스트 비교 결과"""

    text1: str = Field(..., description="첫 번째 텍스트")
    text2: str = Field(..., description="두 번째 텍스트")
    similarity: float = Field(..., description="유사도 점수")
    position: Optional[int] = Field(None, description="텍스트 위치")


class SimilarityResult(BaseModel):
    """유사도 측정 결과 스키마"""

    overall_similarity: float = Field(..., description="종합 유사도 (0.0~1.0)")
    string_similarity: Optional[float] = Field(None, description="문자열 유사도")
    token_similarity: Optional[float] = Field(None, description="토큰 유사도")
    semantic_similarity: Optional[float] = Field(None, description="의미론적 유사도")
    metrics: SimilarityMetrics = Field(..., description="상세 메트릭")
    matched_texts: List[TextComparison] = Field(
        default_factory=list, description="매칭된 텍스트 쌍"
    )
    differences: List[str] = Field(default_factory=list, description="차이점 목록")
    execution_id1: int = Field(..., description="첫 번째 OCR 실행 ID")
    execution_id2: int = Field(..., description="두 번째 OCR 실행 ID")


class SimilarityResponse(BaseModel):
    """유사도 측정 API 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[SimilarityResult] = Field(None, description="유사도 결과")
