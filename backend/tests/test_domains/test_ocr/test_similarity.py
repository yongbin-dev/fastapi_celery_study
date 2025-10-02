# tests/test_domains/test_ocr/test_similarity.py
"""OCR 유사도 측정 단위 테스트"""

from app.domains.ocr.services.similarity.string_similarity import StringSimilarity
from app.domains.ocr.services.similarity.token_similarity import TokenSimilarity


class TestStringSimilarity:
    """문자열 유사도 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.similarity = StringSimilarity()

    def test_identical_texts(self):
        """동일한 텍스트의 유사도는 1.0"""
        text = "Hello World"
        result = self.similarity.calculate(text, text)
        assert result == 1.0

    def test_completely_different_texts(self):
        """완전히 다른 텍스트의 유사도는 0.0에 가까움"""
        text1 = "Hello"
        text2 = "안녕하세요"
        result = self.similarity.calculate(text1, text2)
        assert result < 0.3

    def test_similar_texts(self):
        """유사한 텍스트의 유사도는 높음"""
        text1 = "Hello World"
        text2 = "Hello Wrold"  # 오타 하나
        result = self.similarity.calculate(text1, text2)
        assert result > 0.8

    def test_empty_texts(self):
        """빈 텍스트 처리"""
        # 둘 다 빈 문자열
        assert self.similarity.calculate("", "") == 1.0
        # 하나만 빈 문자열
        assert self.similarity.calculate("Hello", "") == 0.0
        assert self.similarity.calculate("", "World") == 0.0

    def test_case_sensitivity(self):
        """대소문자 구분"""
        text1 = "Hello"
        text2 = "hello"
        result = self.similarity.calculate(text1, text2)
        # 완전히 다르지는 않지만 1.0은 아님
        assert 0.5 < result < 1.0

    def test_metrics(self):
        """상세 메트릭 반환 테스트"""
        text1 = "Hello World"
        text2 = "Hello Wrold"
        metrics = self.similarity.get_metrics(text1, text2)

        # 기본 메트릭 존재 확인
        assert "sequence_matcher" in metrics
        assert isinstance(metrics["sequence_matcher"], float)

        # Levenshtein이 설치되어 있으면 추가 메트릭 확인
        if "levenshtein_distance" in metrics:
            assert isinstance(metrics["levenshtein_distance"], float)
            assert isinstance(metrics["levenshtein_similarity"], float)
            assert isinstance(metrics["jaro_winkler"], float)

    def test_differences(self):
        """차이점 추출 테스트"""
        text1 = "Hello World"
        text2 = "Hello Wrold"
        differences = self.similarity.get_differences(text1, text2)

        assert len(differences) > 0
        assert any("Position" in diff for diff in differences)

    def test_korean_text(self):
        """한국어 텍스트 유사도"""
        text1 = "안녕하세요 반갑습니다"
        text2 = "안녕하세요 반갑습니다"
        result = self.similarity.calculate(text1, text2)
        assert result == 1.0

        text3 = "안녕하세요 반가워요"
        result2 = self.similarity.calculate(text1, text3)
        assert 0.5 < result2 < 1.0


class TestTokenSimilarity:
    """토큰 유사도 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.similarity = TokenSimilarity()

    def test_identical_texts(self):
        """동일한 텍스트의 유사도는 1.0"""
        text = "Hello World Test"
        result = self.similarity.calculate(text, text)
        assert result == 1.0

    def test_no_common_tokens(self):
        """공통 토큰이 없으면 유사도 0.0"""
        text1 = "Hello World"
        text2 = "안녕하세요 세계"
        result = self.similarity.calculate(text1, text2)
        assert result == 0.0

    def test_partial_overlap(self):
        """부분적으로 겹치는 토큰"""
        text1 = "Hello World Test"
        text2 = "Hello Python Test"
        result = self.similarity.calculate(text1, text2)
        # Jaccard Index: {Hello, Test} / {Hello, World, Test, Python} = 2/4 = 0.5
        assert result == 0.5

    def test_empty_texts(self):
        """빈 텍스트 처리"""
        assert self.similarity.calculate("", "") == 1.0
        assert self.similarity.calculate("Hello", "") == 0.0
        assert self.similarity.calculate("", "World") == 0.0

    def test_word_order_independence(self):
        """단어 순서는 Jaccard에 영향 없음"""
        text1 = "Hello World Test"
        text2 = "Test World Hello"
        result = self.similarity.calculate(text1, text2)
        assert result == 1.0

    def test_metrics(self):
        """상세 메트릭 반환 테스트"""
        text1 = "Hello World Test"
        text2 = "Hello Python Test"
        metrics = self.similarity.get_metrics(text1, text2)

        # 기본 메트릭 존재 확인
        assert "jaccard_index" in metrics
        assert isinstance(metrics["jaccard_index"], float)

        # scikit-learn이 설치되어 있으면 Cosine 유사도 확인
        if "cosine_similarity" in metrics:
            assert isinstance(metrics["cosine_similarity"], float)
            assert 0.0 <= metrics["cosine_similarity"] <= 1.0

    def test_common_tokens(self):
        """공통 토큰 추출 테스트"""
        text1 = "Hello World Test"
        text2 = "Hello Python Test"
        common = self.similarity.get_common_tokens(text1, text2)

        assert "Hello" in common
        assert "Test" in common
        assert len(common) == 2

    def test_unique_tokens(self):
        """고유 토큰 추출 테스트"""
        text1 = "Hello World Test"
        text2 = "Hello Python Test"
        unique1, unique2 = self.similarity.get_unique_tokens(text1, text2)

        assert "World" in unique1
        assert "Python" in unique2

    def test_korean_tokens(self):
        """한국어 토큰화 테스트"""
        text1 = "안녕하세요 반갑습니다 테스트"
        text2 = "안녕하세요 반갑습니다 검증"

        result = self.similarity.calculate(text1, text2)
        # 공통: {안녕하세요, 반갑습니다}, 전체: {안녕하세요, 반갑습니다, 테스트, 검증}
        # Jaccard: 2/4 = 0.5
        assert result == 0.5


class TestSimilarityComparison:
    """문자열 vs 토큰 유사도 비교 테스트"""

    def setup_method(self):
        self.string_sim = StringSimilarity()
        self.token_sim = TokenSimilarity()

    def test_word_order_sensitivity(self):
        """단어 순서 변경 시 차이"""
        text1 = "Hello World Test"
        text2 = "Test World Hello"

        # 문자열 유사도는 순서 변경에 민감
        string_result = self.string_sim.calculate(text1, text2)
        assert string_result < 0.8

        # 토큰 유사도는 순서에 무관
        token_result = self.token_sim.calculate(text1, text2)
        assert token_result == 1.0

    def test_typo_detection(self):
        """오타 감지 차이"""
        text1 = "Hello World"
        text2 = "Hello Wrold"  # 오타

        # 문자열 유사도는 오타를 잘 감지
        string_result = self.string_sim.calculate(text1, text2)
        assert string_result > 0.8

        # 토큰 유사도는 오타를 완전히 다른 단어로 인식
        token_result = self.token_sim.calculate(text1, text2)
        # Jaccard: {Hello} / {Hello, World, Wrold} = 1/3 ≈ 0.333
        assert abs(token_result - 0.333) < 0.01
