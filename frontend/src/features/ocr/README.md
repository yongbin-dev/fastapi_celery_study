# OCR 이미지 비교 기능

2개의 이미지를 업로드하여 OCR 텍스트 추출 결과를 비교하고 유사도를 분석하는 기능입니다.

## 📁 폴더 구조

```
features/ocr/
├── components/
│   ├── comparison/          # 비교 레이아웃 컴포넌트
│   │   ├── ComparisonLayout.tsx
│   │   ├── ComparisonHeader.tsx
│   │   ├── ImagePanel.tsx
│   │   └── index.ts
│   ├── upload/             # 업로드 관련 컴포넌트
│   │   ├── ImageUploadZone.tsx
│   │   ├── ImagePreview.tsx
│   │   └── index.ts
│   ├── results/            # OCR 결과 표시 컴포넌트
│   │   ├── OcrResultDisplay.tsx
│   │   └── index.ts
│   ├── similarity/         # 유사도 표시 컴포넌트
│   │   ├── SimilarityDisplay.tsx
│   │   ├── SimilarityScore.tsx
│   │   ├── MetricsGrid.tsx
│   │   ├── DifferenceList.tsx
│   │   ├── AnalyzeButton.tsx
│   │   └── index.ts
│   └── index.ts
├── hooks/
│   ├── useDualOcr.ts       # 2개 이미지 상태 관리
│   ├── useOcr.ts           # OCR API 호출
│   └── index.ts
├── types/
│   ├── comparison.ts       # 비교 관련 타입
│   ├── ocr.ts             # OCR 관련 타입
│   └── index.ts
├── utils/
│   ├── similarity.ts       # 유사도 계산 (구현 필요)
│   └── index.ts
├── pages/
│   ├── OcrComparisonPage.tsx       # 메인 페이지
│   ├── OcrComparisonExample.tsx    # 사용 예시
│   └── OcrPage.tsx                 # 기존 단일 OCR 페이지
├── api/
│   └── ocrApi.ts          # API 호출
└── index.ts
```

## 🚀 사용 방법

### 1. 기본 사용

```tsx
import OcrComparisonPage from '@/features/ocr/pages/OcrComparisonPage';
import { analyzeSimilarity } from '@/features/ocr/utils/similarity';

function App() {
  return (
    <OcrComparisonPage analyzeSimilarity={analyzeSimilarity} />
  );
}
```

### 2. 라우터와 함께 사용

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import OcrComparisonPage from '@/features/ocr/pages/OcrComparisonPage';
import { analyzeSimilarity } from '@/features/ocr/utils/similarity';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/ocr/comparison"
          element={<OcrComparisonPage analyzeSimilarity={analyzeSimilarity} />}
        />
      </Routes>
    </BrowserRouter>
  );
}
```

### 3. 커스텀 유사도 함수 사용

```tsx
import type { SimilarityAnalyzer } from '@/features/ocr/types';

// 커스텀 유사도 분석 함수
const myCustomAnalyzer: SimilarityAnalyzer = async (resultA, resultB) => {
  // 여기에 유사도 계산 로직 구현
  return {
    overallScore: 90,
    metrics: {
      exactMatches: 10,
      partialMatches: 2,
      missingInA: 0,
      missingInB: 1,
      characterSimilarity: 92,
      wordSimilarity: 88,
      lineSimilarity: 90,
    },
    differences: [],
    matchedPairs: [],
  };
};

<OcrComparisonPage analyzeSimilarity={myCustomAnalyzer} />
```

## 📝 타입 정의

### SimilarityAnalyzer

```typescript
type SimilarityAnalyzer = (
  resultA: OcrResponse,
  resultB: OcrResponse
) => Promise<SimilarityResult>;
```

유사도 분석 함수의 타입입니다. 2개의 OCR 결과를 받아 유사도 분석 결과를 반환합니다.

### SimilarityResult

```typescript
interface SimilarityResult {
  overallScore: number;              // 전체 유사도 (0-100)
  metrics: SimilarityMetrics;        // 상세 메트릭
  differences: TextDifference[];     // 차이점 목록
  matchedPairs: MatchedPair[];       // 매칭된 텍스트 쌍
}
```

### SimilarityMetrics

```typescript
interface SimilarityMetrics {
  exactMatches: number;           // 완전 일치 개수
  partialMatches: number;         // 부분 일치 개수
  missingInA: number;             // A에 없는 개수
  missingInB: number;             // B에 없는 개수
  characterSimilarity: number;    // 문자 유사도 (%)
  wordSimilarity: number;         // 단어 유사도 (%)
  lineSimilarity: number;         // 라인 유사도 (%)
}
```

## 🔧 구현 필요 사항

### utils/similarity.ts

현재 `analyzeSimilarity` 함수는 임시 데이터를 반환합니다. 실제 유사도 계산 로직을 구현해야 합니다.

**구현 예정 알고리즘:**
- 레벤슈타인 거리 (Levenshtein Distance)
- 문자열 유사도 계산
- 라인별 매칭
- 차이점 추출

**참고 함수:**
```typescript
export const analyzeSimilarity = async (
  resultA: OcrResponse,
  resultB: OcrResponse
): Promise<SimilarityResult> => {
  // TODO: 유사도 계산 로직 구현
  // 1. 전체 텍스트를 라인별로 분리
  // 2. 각 라인 매칭 (레벤슈타인 거리 사용)
  // 3. 메트릭 계산 (문자/단어/라인 유사도)
  // 4. 차이점 추출
  // 5. 전체 유사도 점수 계산
};
```

## 🎨 UI 컴포넌트

### ComparisonLayout
3-column 레이아웃 (이미지 A | 유사도 | 이미지 B)
- 데스크톱: 3-column
- 모바일: 스택 레이아웃

### ImagePanel
- 이미지 업로드 (드래그앤드롭)
- 이미지 프리뷰
- OCR 실행 버튼
- OCR 결과 표시

### SimilarityDisplay
- 전체 유사도 점수
- 상세 메트릭
- 차이점 목록
- 분석 버튼

## 🔄 상태 관리

### useDualOcr Hook

2개 이미지의 상태를 관리하는 커스텀 훅입니다.

```typescript
const {
  state,                    // 전체 상태
  handleFileSelect,         // 파일 선택
  handleExtract,            // OCR 실행
  handleAnalyzeSimilarity,  // 유사도 분석
  handleClear,              // 슬롯 초기화
  handleReset,              // 전체 초기화
  canAnalyze,               // 분석 가능 여부
} = useDualOcr({ analyzeSimilarity });
```

## 📋 다음 단계

1. ✅ UI 컴포넌트 구현 완료
2. ✅ 상태 관리 구현 완료
3. ⏳ **유사도 계산 알고리즘 구현 필요**
4. ⏳ 내보내기 기능 추가
5. ⏳ 테스트 작성
6. ⏳ 접근성 개선

## 📚 참고 자료

- [레벤슈타인 거리](https://en.wikipedia.org/wiki/Levenshtein_distance)
- [문자열 유사도 알고리즘](https://en.wikipedia.org/wiki/String_metric)
