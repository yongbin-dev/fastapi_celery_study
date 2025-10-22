# app/domains/ocr/services/similarity/token_similarity.py
from typing import Dict, List, Set

from shared.core.logging import get_logger

from .base import BaseSimilarity

logger = get_logger(__name__)


class TokenSimilarity(BaseSimilarity):
    """토큰 기반 유사도 측정"""

    def get_method_name(self) -> str:
        return "token"

    def _tokenize(self, text: str) -> List[str]:
        """
        텍스트를 토큰(단어)으로 분리합니다.

        Args:
            text: 입력 텍스트

        Returns:
            토큰 리스트
        """
        # 공백 기반 토큰화 (한국어, 영어 모두 지원)
        return text.split()

    def calculate(self, text1: str, text2: str) -> float:
        """
        토큰 기반 유사도를 계산합니다 (Jaccard Index 기반).

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

        tokens1 = set(self._tokenize(text1))
        tokens2 = set(self._tokenize(text2))

        # Jaccard Index
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if len(union) == 0:
            return 0.0

        return len(intersection) / len(union)

    def get_metrics(self, text1: str, text2: str) -> Dict[str, float]:
        """
        상세한 토큰 유사도 메트릭을 반환합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            메트릭 딕셔너리
        """
        metrics = {}

        # Jaccard Index
        metrics["jaccard_index"] = self.calculate(text1, text2)

        # Cosine Similarity
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

            # TF-IDF 벡터화
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            result = cosine_similarity(tfidf_matrix)
            cosine_sim = float(result[0, 1])
            metrics["cosine_similarity"] = cosine_sim

        except ImportError:
            logger.warning(
                "scikit-learn 패키지가 설치되지 않았습니다. "
                "Cosine 유사도를 사용하려면 설치하세요: pip install scikit-learn"
            )
        except Exception as e:
            logger.error(f"Cosine 유사도 계산 중 오류: {e}")

        return metrics

    def get_common_tokens(self, text1: str, text2: str) -> Set[str]:
        """
        두 텍스트의 공통 토큰을 반환합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            공통 토큰 집합
        """
        tokens1 = set(self._tokenize(text1))
        tokens2 = set(self._tokenize(text2))

        return tokens1.intersection(tokens2)

    def get_unique_tokens(self, text1: str, text2: str) -> tuple:
        """
        각 텍스트의 고유 토큰을 반환합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            (text1 고유 토큰, text2 고유 토큰)
        """
        tokens1 = set(self._tokenize(text1))
        tokens2 = set(self._tokenize(text2))

        unique1 = tokens1 - tokens2
        unique2 = tokens2 - tokens1

        return unique1, unique2
