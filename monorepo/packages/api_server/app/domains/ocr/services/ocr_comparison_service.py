# app/domains/ocr/services/ocr_comparison_service.py
"""OCR 결과 비교 통합 서비스"""

from typing import Dict, List, Optional

from app.domains.ocr.schemas.similarity import (
    SimilarityMetrics,
    SimilarityResult,
    TextComparison,
)
from app.domains.ocr.services.similarity.string_similarity import StringSimilarity
from app.domains.ocr.services.similarity.token_similarity import TokenSimilarity
from shared.core.logging import get_logger
from shared.models import OCRExecution
from shared.repository.crud.async_crud.ocr_execution import ocr_execution_crud
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class OCRComparisonService:
    """OCR 결과 비교 서비스"""

    def __init__(self):
        self.string_similarity = StringSimilarity()
        self.token_similarity = TokenSimilarity()

    async def compare_executions(
        self,
        db: AsyncSession,
        execution_id1: int,
        execution_id2: int,
        method: str = "all",
        weights: Optional[Dict[str, float]] = None,
    ) -> SimilarityResult:
        """
        두 OCR 실행 결과를 비교합니다.

        Args:
            db: 데이터베이스 세션
            execution_id1: 첫 번째 OCR 실행 ID
            execution_id2: 두 번째 OCR 실행 ID
            method: 유사도 측정 방법 (string, token, all)
            weights: 각 방법의 가중치

        Returns:
            SimilarityResult: 유사도 측정 결과
        """
        # 기본 가중치 설정
        if weights is None:
            weights = {"string": 0.5, "token": 0.5}

        # OCR 실행 결과 조회
        execution1 = await ocr_execution_crud.get(db, execution_id1)
        execution2 = await ocr_execution_crud.get(db, execution_id2)

        if not execution1:
            raise ValueError(f"OCR 실행 ID {execution_id1}를 찾을 수 없습니다.")
        if not execution2:
            raise ValueError(f"OCR 실행 ID {execution_id2}를 찾을 수 없습니다.")

        # 텍스트 박스에서 텍스트 추출
        text1 = self._extract_text_from_execution(execution1)
        text2 = self._extract_text_from_execution(execution2)

        logger.info(
            f"OCR 결과 비교 시작: execution_id1={execution_id1}, "
            f"execution_id2={execution_id2}, method={method}"
        )

        # 유사도 계산
        string_similarity = None
        token_similarity = None
        metrics_dict = {}

        if method in ["string", "all"]:
            string_similarity = self.string_similarity.calculate(text1, text2)
            string_metrics = self.string_similarity.get_metrics(text1, text2)
            metrics_dict.update(string_metrics)

        if method in ["token", "all"]:
            token_similarity = self.token_similarity.calculate(text1, text2)
            token_metrics = self.token_similarity.get_metrics(text1, text2)
            metrics_dict.update(token_metrics)

        # 종합 유사도 계산
        overall_similarity = self._calculate_overall_similarity(
            string_similarity=string_similarity,
            token_similarity=token_similarity,
            weights=weights,
        )

        # 차이점 추출
        differences = []
        if method in ["string", "all"]:
            differences = self.string_similarity.get_differences(text1, text2)

        # TextBox 단위 비교
        matched_texts = self._compare_text_boxes(execution1, execution2)

        # 메트릭 객체 생성
        metrics = SimilarityMetrics(**metrics_dict)

        logger.info(f"OCR 결과 비교 완료: overall_similarity={overall_similarity:.4f}")

        return SimilarityResult(
            overall_similarity=overall_similarity,
            string_similarity=string_similarity,
            token_similarity=token_similarity,
            semantic_similarity=None,
            metrics=metrics,
            matched_texts=matched_texts,
            differences=differences[:10],  # 상위 10개만 반환
            execution_id1=execution_id1,
            execution_id2=execution_id2,
        )

    def _extract_text_from_execution(self, execution: OCRExecution) -> str:
        """
        OCR 실행 결과에서 전체 텍스트를 추출합니다.

        Args:
            execution: OCR 실행 객체

        Returns:
            전체 텍스트 (공백으로 연결)
        """
        texts = [box.text for box in execution.text_boxes]
        return " ".join(texts)

    def _calculate_overall_similarity(
        self,
        string_similarity: Optional[float],
        token_similarity: Optional[float],
        weights: Dict[str, float],
    ) -> float:
        """
        가중치 기반 종합 유사도를 계산합니다.

        Args:
            string_similarity: 문자열 유사도
            token_similarity: 토큰 유사도
            weights: 가중치

        Returns:
            종합 유사도 (0.0 ~ 1.0)
        """
        total_score = 0.0
        total_weight = 0.0

        if string_similarity is not None:
            weight = weights.get("string", 0.0)
            total_score += string_similarity * weight
            total_weight += weight

        if token_similarity is not None:
            weight = weights.get("token", 0.0)
            total_score += token_similarity * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def _compare_text_boxes(
        self, execution1: OCRExecution, execution2: OCRExecution
    ) -> List[TextComparison]:
        """
        두 OCR 실행의 텍스트 박스를 개별적으로 비교합니다.

        Args:
            execution1: 첫 번째 OCR 실행
            execution2: 두 번째 OCR 실행

        Returns:
            매칭된 텍스트 쌍 리스트
        """
        matched_texts = []

        # 두 실행의 텍스트 박스 수가 다를 수 있으므로 최소값 사용
        min_boxes = min(len(execution1.text_boxes), len(execution2.text_boxes))

        for i in range(min_boxes):
            box1 = execution1.text_boxes[i]
            box2 = execution2.text_boxes[i]

            # 개별 텍스트 박스 유사도 계산
            similarity = self.string_similarity.calculate(box1.text, box2.text)

            matched_texts.append(
                TextComparison(
                    text1=box1.text, text2=box2.text, similarity=similarity, position=i
                )
            )

        return matched_texts


# 싱글톤 인스턴스
ocr_comparison_service = OCRComparisonService()
