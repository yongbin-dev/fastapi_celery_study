# app/domains/ocr/services/similarity/string_similarity.py
import difflib
from typing import Dict

from app.core.logging import get_logger

from .base import BaseSimilarity

logger = get_logger(__name__)


class StringSimilarity(BaseSimilarity):
    """문자열 기반 유사도 측정"""

    def get_method_name(self) -> str:
        return "string"

    def calculate(self, text1: str, text2: str) -> float:
        """
        문자열 유사도를 계산합니다 (SequenceMatcher 기반).

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            0.0 ~ 1.0 사이의 유사도 점수
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def get_metrics(self, text1: str, text2: str) -> Dict[str, float]:
        """
        상세한 문자열 유사도 메트릭을 반환합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            메트릭 딕셔너리
        """
        metrics = {}

        # SequenceMatcher 유사도
        metrics["sequence_matcher"] = self.calculate(text1, text2)

        # Levenshtein 거리 및 유사도
        try:
            import Levenshtein

            lev_distance = Levenshtein.distance(text1, text2)
            max_len = max(len(text1), len(text2))
            lev_similarity = 1.0 - (lev_distance / max_len if max_len > 0 else 0.0)

            metrics["levenshtein_distance"] = float(lev_distance)
            metrics["levenshtein_similarity"] = lev_similarity

            # Jaro-Winkler 유사도
            metrics["jaro_winkler"] = Levenshtein.jaro_winkler(text1, text2)

        except ImportError:
            logger.warning(
                "python-Levenshtein 패키지가 설치되지 않았습니다. "
                "고급 문자열 유사도 측정을 사용하려면 설치하세요: "
                "pip install python-Levenshtein"
            )

        return metrics

    def get_differences(self, text1: str, text2: str) -> list:
        """
        두 텍스트의 차이점을 반환합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            차이점 목록
        """
        differences = []
        matcher = difflib.SequenceMatcher(None, text1, text2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                differences.append(
                    f"Position {i1}-{i2}: '{text1[i1:i2]}' → '{text2[j1:j2]}'"
                )
            elif tag == "delete":
                differences.append(f"Position {i1}-{i2}: Deleted '{text1[i1:i2]}'")
            elif tag == "insert":
                differences.append(f"Position {j1}-{j2}: Inserted '{text2[j1:j2]}'")

        return differences
