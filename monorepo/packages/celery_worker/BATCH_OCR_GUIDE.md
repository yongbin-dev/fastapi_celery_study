# Batch OCR 사용 가이드

BentoML OCR 서비스의 배치 처리 기능 사용 방법을 설명합니다.

## 개요

배치 OCR 기능을 사용하면 여러 이미지를 한 번의 API 호출로 처리할 수 있습니다.

### 주요 특징

1. **배치 처리**: 여러 이미지를 한 번에 처리
2. **자동 분기**: PipelineContext의 `is_batch` 플래그로 단일/배치 자동 선택
3. **개별 결과 저장**: 각 이미지마다 개별 OCRExecution 레코드 생성
4. **실패 처리**: 일부 이미지 실패 시에도 나머지 이미지는 정상 처리

## API 엔드포인트

### BentoML 서버

```bash
# 단일 이미지 OCR
POST http://localhost:3000/extract_text

# 배치 이미지 OCR
POST http://localhost:3000/extract_text_batch
```

## 사용 방법

### 1. PipelineContext 생성 (단일 이미지)

```python
from shared.pipeline.context import PipelineContext

context = PipelineContext(
    chain_id="chain-123",
    private_img="/path/to/image.jpg",
    public_file_path="/public/image.jpg",
    is_batch=False,  # 단일 이미지 처리
    options={
        "language": "korean",
        "confidence_threshold": 0.5,
        "use_angle_cls": True
    }
)
```

### 2. PipelineContext 생성 (배치 처리)

```python
from shared.pipeline.context import PipelineContext

context = PipelineContext(
    chain_id="batch-123",
    private_imgs=[
        "/path/to/image1.jpg",
        "/path/to/image2.jpg",
        "/path/to/image3.jpg"
    ],
    public_file_paths=[
        "/public/image1.jpg",
        "/public/image2.jpg",
        "/public/image3.jpg"
    ],
    is_batch=True,  # 배치 처리
    options={
        "language": "korean",
        "confidence_threshold": 0.5,
        "use_angle_cls": True
    }
)
```

### 3. OCRStage 실행

```python
from tasks.stages.ocr_stage import OCRStage

# OCRStage는 자동으로 단일/배치를 구분하여 처리
stage = OCRStage()
result_context = await stage.execute(context)

# 단일 처리 결과 확인
if not context.is_batch:
    print(f"텍스트 박스 수: {len(result_context.ocr_result.text_boxes)}")

# 배치 처리 결과 확인
if context.is_batch:
    print(f"처리된 이미지 수: {len(result_context.ocr_results)}")
    for idx, result in enumerate(result_context.ocr_results):
        print(f"이미지 {idx+1}: {len(result.text_boxes)} 텍스트 박스")
```

### 4. BentoML 클라이언트 사용 (Python)

```python
from examples.bentoml_client_example import BentoMLClient

client = BentoMLClient(base_url="http://localhost:3000")

# 배치 OCR 실행
result = client.extract_text_batch(
    private_imgs=[
        "/path/to/image1.jpg",
        "/path/to/image2.jpg",
        "/path/to/image3.jpg"
    ],
    language="korean",
    confidence_threshold=0.5,
    use_angle_cls=True
)

print(f"총 처리: {result['total_processed']}")
print(f"성공: {result['total_success']}")
print(f"실패: {result['total_failed']}")
```

### 5. cURL 사용

```bash
curl -X POST "http://localhost:3000/extract_text_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "request_data": {
      "language": "korean",
      "confidence_threshold": 0.5,
      "use_angle_cls": true
    },
    "private_imgs": [
      "/path/to/image1.jpg",
      "/path/to/image2.jpg",
      "/path/to/image3.jpg"
    ]
  }'
```

## DB 저장

### 단일 이미지

- 1개의 `OCRExecution` 레코드 생성
- 각 텍스트 박스는 `OCRTextBox` 테이블에 저장

### 배치 이미지

- 이미지 개수만큼 `OCRExecution` 레코드 생성
- 각 이미지의 텍스트 박스는 개별 execution에 연결
- 실패한 이미지는 `status='failed'`로 저장

## 타임아웃 설정

배치 처리는 이미지 개수에 따라 타임아웃이 자동 조정됩니다:

```python
timeout = 30.0 + (len(private_imgs) * 10.0)
```

- 기본 30초 + 이미지당 10초
- 예: 5개 이미지 = 80초 타임아웃

## 에러 처리

### 서버 오류 (5xx)
- `RetryableError` 발생
- Celery가 자동으로 재시도

### 클라이언트 오류 (4xx)
- `ValueError` 발생
- 재시도 없이 실패 처리

### 부분 실패
- 배치 처리에서 일부 이미지만 실패한 경우
- 성공한 이미지는 정상 처리
- 실패한 이미지는 빈 text_boxes로 반환

## 성능 고려사항

1. **배치 크기**: 너무 큰 배치는 타임아웃 발생 가능
   - 권장: 10개 이하

2. **메모리**: 모든 이미지를 메모리에 로드하므로 큰 이미지는 주의
   - 대용량 이미지는 단일 처리 권장

3. **동시성**: BentoML은 내부적으로 순차 처리
   - 병렬 처리가 필요하면 여러 요청으로 분할

## 예제 코드

전체 예제는 다음 파일을 참고하세요:
- `packages/ml_server/examples/bentoml_client_example.py`
