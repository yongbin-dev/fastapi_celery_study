
● OCR 결과 텍스트 유사도 검출 구현 계획

  두 개의 OCR 결과를 비교하여 텍스트 유사도를 측정하는 기능을 구현하겠습니다.

  📋 구현 계획

  1️⃣ 유사도 측정 방식 선택

  다음 3가지 방법을 조합하여 종합적인 유사도를 제공합니다:

  A. 문자열 레벨 유사도

  - Levenshtein Distance (편집 거리): 문자 추가/삭제/교체 횟수 기반
  - Jaro-Winkler Distance: 문자 위치와 공통 접두사 고려
  - SequenceMatcher (difflib): Python 표준 라이브러리, 빠른 연산

  B. 토큰 레벨 유사도

  - Jaccard Similarity: 단어 집합 간 교집합/합집합 비율
  - Cosine Similarity: TF-IDF 벡터화 후 코사인 유사도

  C. 의미론적 유사도 (선택적)

  - Sentence Transformers: 문장 임베딩 기반 의미 유사도
  - 더 정확하지만 무거운 연산 (GPU 권장)

  ---
  2️⃣ 아키텍처 설계

  app/domains/ocr/
  ├── services/
  │   ├── similarity/
  │   │   ├── __init__.py
  │   │   ├── base.py              # 유사도 측정 추상 클래스
  │   │   ├── string_similarity.py  # 문자열 기반
  │   │   ├── token_similarity.py   # 토큰 기반
  │   │   └── semantic_similarity.py # 의미론적 (선택)
  │   └── ocr_comparison_service.py # 통합 비교 서비스
  ├── schemas/
  │   └── similarity.py             # 유사도 관련 DTO
  └── controllers/
      └── comparison.py             # 비교 API 엔드포인트

  ---
  3️⃣ 데이터 구조

  입력: ocr_execution id [int , int] 2개


  출력: SimilarityResultDTO

  SimilarityResultDTO(
      overall_similarity: float,      # 0.0 ~ 1.0 종합 유사도
      string_similarity: float,       # 문자열 유사도
      token_similarity: float,        # 토큰 유사도
      semantic_similarity: Optional[float],  # 의미론적 유사도
      metrics: Dict[str, float],      # 세부 메트릭
      matched_texts: List[Tuple[str, str, float]],  # 매칭된 텍스트 쌍
      differences: List[str]          # 차이점 목록
  )

  ---
  4️⃣ 구현 단계

  Phase 1: 기본 유사도 측정

  1. ✅ base.py: 추상 클래스 정의
  2. ✅ string_similarity.py: Levenshtein, Jaro-Winkler, SequenceMatcher 구현
  3. ✅ token_similarity.py: Jaccard, Cosine 유사도 구현
  4. ✅ similarity.py: DTO 스키마 정의

  Phase 2: 통합 서비스

  5. ✅ ocr_comparison_service.py:
    - 여러 유사도 측정 방법 조합
    - 가중치 기반 종합 점수 계산
    - TextBox 단위 비교 지원

  Phase 3: API 엔드포인트

  6. ✅ comparison.py:
    - POST /ocr/compare 엔드포인트
    - ocr_execution 두개의 Id를 입력받아 text_boxes를 각각 가져와서 유사도 측정 및 반환
    - Swagger 문서화

  Phase 4: 테스트 & 검증

  7. ✅ 단위 테스트 작성
  8. ✅ 통합 테스트 (실제 OCR 결과 비교)

  ---
  5️⃣ 의존성

  [project.optional-dependencies]
  similarity = [
      "python-Levenshtein>=0.21.0",  # 빠른 편집 거리 계산
      "scikit-learn>=1.3.0",         # TF-IDF, Cosine 유사도
      "numpy>=1.24.0",
  ]
  # 선택적 (의미론적 유사도)
  semantic = [
      "sentence-transformers>=2.2.0",
      "torch>=2.0.0",
  ]

  ---
  6️⃣ API 사용 예시

  # 요청
  POST /api/v1/ocr/compare
  {
      "id1": 1,
      "id1": 2,
      "method": "all",  # "string", "token", "semantic", "all"
      "weights": {
          "string": 0.5,
          "token": 0.3,
          "semantic": 0.2
      }
  }

  # 응답
  {
      "overall_similarity": 0.92,
      "string_similarity": 0.95,  # Levenshtein
      "token_similarity": 0.90,   # Jaccard
      "semantic_similarity": 0.88,
      "metrics": {
          "levenshtein_distance": 1,
          "jaro_winkler": 0.96,
          "jaccard_index": 0.90,
          "cosine_similarity": 0.92
      },
      "differences": [
          "Position 9: 'World' vs 'Wrold'"
      ]
  }

  ---
  🎯 권장 구현 순서

  1. 기본 문자열 유사도 (가장 빠르고 가벼움) ✅
  2. 토큰 기반 유사도 (단어 수준 비교) ✅
  3. 통합 서비스 & API ✅
  4. 의미론적 유사도 (선택, 성능 허용 시)

  ---
  💡 추가 고려사항

  성능 최적화

  - 짧은 텍스트 (<100자): 모든 방법 적용
  - 긴 텍스트 (>1000자): 토큰 기반만 사용
  - 실시간 필요 시: SequenceMatcher만 사용

  언어 처리

  - 한국어: 형태소 분석 (KoNLPy) 적용 고려
  - 다국어: 공백 기반 토큰화

  Celery 태스크 통합

  - 무거운 연산(의미론적 유사도)은 비동기 처리
  - 결과 캐싱으로 반복 요청 최적화

  ---
  이제 구현을 시작할까요? 어떤 단계부터 시작하시겠습니까?

  1. 빠른 프로토타입: 기본 문자열 유사도만 (5분)
  2. 완전한 구현: 문자열 + 토큰 유사도 + API (15분)
  3. 고급 구현: 의미론적 유사도 포함 (30분+)