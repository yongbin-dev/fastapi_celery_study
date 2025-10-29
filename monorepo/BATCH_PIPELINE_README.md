# 배치 파이프라인 시스템

대량 이미지를 청크 단위로 병렬 처리하는 배치 파이프라인 시스템입니다.

## 📋 개요

기존의 단일 이미지 처리 파이프라인을 확장하여 100개, 1000개 이상의 이미지를 효율적으로 처리할 수 있는 배치 시스템입니다.

### 주요 특징

- **청크 기반 병렬 처리**: 이미지를 작은 청크(기본 10개)로 분할하여 병렬 처리
- **실시간 진행 상황 추적**: 배치 처리 진행률, 완료/실패 이미지 수 실시간 확인
- **장애 복구**: 청크 단위 재시도로 실패 시 최소 범위만 재처리
- **확장성**: Celery의 분산 처리로 워커 추가만으로 성능 확장 가능

## 🏗️ 아키텍처

### 데이터베이스 모델

#### BatchExecution (배치 실행)
```python
- batch_id: 배치 고유 ID (UUID)
- batch_name: 배치 이름
- total_images: 총 이미지 수
- completed_images: 완료된 이미지 수
- failed_images: 실패한 이미지 수
- total_chunks: 총 청크 수
- completed_chunks: 완료된 청크 수
- chunk_size: 청크당 이미지 수
```

#### ChainExecution (개별 파이프라인)
```python
- batch_id: 연결된 배치 ID (nullable)
```

### 태스크 구조

```
start_batch_pipeline()
  ├─ BatchExecution 생성
  ├─ 파일 경로를 청크로 분할
  └─ Celery group으로 병렬 실행
      ├─ process_chunk_task(chunk_0)
      │   └─ start_pipeline() × N
      ├─ process_chunk_task(chunk_1)
      │   └─ start_pipeline() × N
      └─ process_chunk_task(chunk_N)
          └─ start_pipeline() × N
```

## 🚀 사용 방법

### 1. DB 마이그레이션

```bash
# PostgreSQL에 마이그레이션 실행
psql -U your_user -d your_database -f migrations/001_add_batch_execution.sql
```

### 2. API 호출

#### 배치 파이프라인 시작

```bash
curl -X POST "http://localhost:8000/pipeline/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "batch_name=test_batch_001" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**응답:**
```json
{
  "success": true,
  "data": {
    "context_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "배치 파이프라인 시작됨: 100개 이미지"
  }
}
```

#### 배치 상태 조회

```bash
curl "http://localhost:8000/pipeline/batch/{batch_id}"
```

**응답:**
```json
{
  "success": true,
  "data": {
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "STARTED",
    "total_images": 100,
    "completed_images": 45,
    "failed_images": 2,
    "progress_percentage": 47.0,
    "started_at": "2025-01-15T10:30:00",
    "estimated_time_remaining": 120.5
  }
}
```

#### 배치 목록 조회

```bash
curl "http://localhost:8000/pipeline/batch?limit=10"
```

## ⚙️ 설정

### 청크 크기 조정

배치 시작 시 `chunk_size` 파라미터로 조정 가능:

```python
# celery_worker/tasks/pipeline_tasks.py
start_batch_pipeline(
    batch_name="my_batch",
    file_paths=file_paths,
    public_file_paths=public_file_paths,
    options={},
    chunk_size=20,  # 청크당 20개 이미지
)
```

**권장 청크 크기:**
- 작은 이미지 (< 1MB): 20-50개
- 중간 이미지 (1-5MB): 10-20개
- 큰 이미지 (> 5MB): 5-10개

### Celery 워커 수 조정

```bash
# 워커 수 증가로 처리량 향상
celery -A celery_app worker --loglevel=info --concurrency=8
```

## 📊 성능 예측

### 처리 시간 예측

```
총 처리 시간 ≈ (총 이미지 수 / 청크 크기) × 이미지당 처리 시간 / 워커 수
```

**예시:**
- 1000개 이미지
- 청크 크기: 10
- 이미지당 처리 시간: 5초
- 워커 수: 4

```
처리 시간 ≈ (1000 / 10) × 5 / 4 = 125초 (약 2분)
```

## 🔍 모니터링

### 진행 상황 확인

```python
# 실시간 진행률 체크
import requests
import time

batch_id = "your-batch-id"

while True:
    response = requests.get(f"http://localhost:8000/pipeline/batch/{batch_id}")
    data = response.json()["data"]

    print(f"진행률: {data['progress_percentage']:.1f}%")
    print(f"완료: {data['completed_images']}/{data['total_images']}")
    print(f"실패: {data['failed_images']}")

    if data["status"] in ["SUCCESS", "FAILURE"]:
        break

    time.sleep(5)
```

### Celery Flower 모니터링

```bash
# Flower 웹 UI 시작
celery -A celery_app flower
```

브라우저에서 `http://localhost:5555` 접속

## 🐛 문제 해결

### 배치가 시작되지 않는 경우

1. Celery 워커 상태 확인:
```bash
celery -A celery_app inspect active
```

2. Redis 연결 확인:
```bash
redis-cli ping
```

3. DB 연결 확인:
```bash
psql -U your_user -d your_database -c "SELECT 1;"
```

### 청크 처리 실패

개별 청크 실패 시 자동으로 재시도됩니다 (최대 3회).
실패한 청크는 `failed_chunks` 카운터에 반영되며, 해당 청크의 이미지들은 `failed_images`에 포함됩니다.

### 메모리 부족

청크 크기를 줄이거나 워커의 메모리를 증가시키세요:

```bash
# 청크 크기 감소
chunk_size=5

# 또는 워커 동시성 감소
celery -A celery_app worker --concurrency=2
```

## 📈 향후 개선 사항

- [ ] 배치 우선순위 큐
- [ ] 동적 청크 크기 조정
- [ ] 실패한 이미지만 재처리하는 기능
- [ ] 배치 처리 통계 대시보드
- [ ] WebSocket 기반 실시간 진행 상황 알림
- [ ] S3/MinIO 직접 연동

## 📝 API 문서

전체 API 문서는 FastAPI Swagger UI에서 확인:
```
http://localhost:8000/docs
```

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
