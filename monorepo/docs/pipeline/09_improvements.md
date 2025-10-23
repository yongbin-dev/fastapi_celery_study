# 향후 개선 방향

**[← 이전: 배포 및 확장](./08_deployment.md)** | **[다음: 참고 자료 →](./10_references.md)** | **[목차](./README.md)**

---

## 1. 웹소켓 알림: 실시간 진행 상황 푸시

### 왜 필요한가?

- **현재 문제**: 클라이언트가 `/status/{chain_id}`를 주기적으로 폴링해야 함
  - 불필요한 네트워크 요청 증가
  - 서버 부하 증가
  - 실시간성 부족 (폴링 주기만큼 지연)

- **개선 효과**:
  - 실시간 진행 상황 업데이트
  - 서버 리소스 절약 (폴링 요청 제거)
  - 더 나은 사용자 경험

### 어떻게 구현할까?

**1. WebSocket 엔드포인트 추가**

```python
# api_server/domains/pipeline/controllers/pipeline_ws.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

# 연결된 클라이언트 관리
active_connections: Dict[str, Set[WebSocket]] = {}

@router.websocket("/ws/pipeline/{chain_id}")
async def pipeline_websocket(websocket: WebSocket, chain_id: str):
    """파이프라인 진행 상황 실시간 구독"""
    await websocket.accept()

    # 연결 등록
    if chain_id not in active_connections:
        active_connections[chain_id] = set()
    active_connections[chain_id].add(websocket)

    try:
        while True:
            # 연결 유지 (클라이언트가 닫을 때까지)
            await websocket.receive_text()
    except WebSocketDisconnect:
        # 연결 해제
        active_connections[chain_id].remove(websocket)
```

**2. Celery Signals에서 WebSocket으로 브로드캐스트**

```python
# celery_worker/core/celery_signals.py
import asyncio
from api_server.domains.pipeline.controllers.pipeline_ws import broadcast_update

@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, **kwargs):
    """Task 완료 후 - WebSocket 알림"""

    # DB 업데이트 (기존 로직)
    # ...

    # WebSocket으로 실시간 알림
    asyncio.create_task(
        broadcast_update(
            chain_id=chain_id,
            message={
                "type": "task_completed",
                "task_name": task.name,
                "progress": chain_exec.completed_tasks / chain_exec.total_tasks
            }
        )
    )
```

**3. 클라이언트 연결 예시**

```javascript
// 프론트엔드
const ws = new WebSocket(`ws://localhost:8000/ws/pipeline/${chainId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Progress:', data.progress);
    // UI 업데이트
};
```

---

## 2. 배치 처리: 여러 파일 한 번에 처리

### 왜 필요한가?

- **현재 문제**: 파일마다 개별 API 호출 필요
  - 100개 파일 처리 시 100번의 API 호출
  - 관리 복잡성 증가
  - 비효율적인 리소스 사용

- **개선 효과**:
  - 한 번의 요청으로 여러 파일 처리
  - 관리 편의성 향상 (단일 batch_id로 추적)
  - 우선순위 관리 용이

### 어떻게 구현할까?

**1. Batch 모델 추가**

```python
# shared/models/batch_execution.py
class BatchExecution(Base):
    """배치 실행 정보"""
    __tablename__ = "batch_executions"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(255), unique=True, index=True)
    total_files = Column(Integer, default=0)
    completed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)

    # 관계
    chains = relationship("ChainExecution", back_populates="batch")
```

**2. 배치 API 엔드포인트**

```python
# api_server/domains/pipeline/controllers/pipeline_controller.py
@router.post("/batch/cr-extract")
async def create_batch_cr_extract(
    files: List[UploadFile],
    options: CRExtractOptions
):
    """여러 파일을 배치로 처리"""

    batch_id = str(uuid.uuid4())

    # DB에 Batch 생성
    batch_exec = batch_crud.create(
        db=db,
        batch_id=batch_id,
        total_files=len(files)
    )

    # 각 파일에 대해 chain 시작
    chain_ids = []
    for file in files:
        file_path = await save_file(file)
        chain_id = start_cr_extract_pipeline(
            file_path=file_path,
            options=options,
            batch_id=batch_id  # batch와 연결
        )
        chain_ids.append(chain_id)

    return {
        "batch_id": batch_id,
        "chain_ids": chain_ids,
        "total_files": len(files)
    }
```

**3. Celery Group 활용**

```python
# 모든 파일을 병렬로 처리
from celery import group

tasks = [
    start_cr_extract_pipeline.s(file_path, options)
    for file_path in file_paths
]

job = group(tasks)
result = job.apply_async()
```

---

## 3. 결과 캐싱: 동일 파일 재처리 방지

### 왜 필요한가?

- **현재 문제**: 같은 파일을 다시 업로드하면 전체 과정 재실행
  - 불필요한 비용 (OCR, LLM API 호출)
  - 처리 시간 낭비
  - 리소스 낭비

- **개선 효과**:
  - 즉시 결과 반환 (수초 vs 수분)
  - API 비용 절감 (OCR, LLM 호출 생략)
  - 서버 리소스 절약

### 어떻게 구현할까?

**1. 파일 해시 기반 캐싱**

```python
import hashlib

def calculate_file_hash(file_path: str) -> str:
    """파일의 SHA256 해시 계산"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

**2. 캐시 조회 로직**

```python
@router.post("/cr-extract")
async def create_cr_extract_job(file: UploadFile):
    """CR 추출 (캐시 지원)"""

    # 1. 파일 저장
    file_path = await save_file(file)

    # 2. 파일 해시 계산
    file_hash = calculate_file_hash(file_path)

    # 3. 캐시 조회
    cached_result = cache_crud.get_by_hash(db, file_hash=file_hash)

    if cached_result and not cached_result.is_expired():
        # 캐시 히트 - 즉시 반환
        return {
            "chain_id": cached_result.chain_id,
            "cached": True,
            "result": cached_result.result
        }

    # 4. 캐시 미스 - 새로 처리
    chain_id = start_cr_extract_pipeline(file_path, options)

    # 5. 캐시 저장 (완료 후 Celery signal에서)
    return {
        "chain_id": chain_id,
        "cached": False
    }
```

**3. 캐시 모델**

```python
# shared/models/result_cache.py
class ResultCache(Base):
    """처리 결과 캐시"""
    __tablename__ = "result_caches"

    id = Column(Integer, primary_key=True)
    file_hash = Column(String(64), unique=True, index=True)
    chain_id = Column(String(255))
    result = Column(JSON)  # 최종 결과

    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)  # 캐시 만료 시간

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
```

---

## 4. A/B 테스트: 여러 모델 성능 비교

### 왜 필요한가?

- **현재 문제**: 어떤 OCR/LLM 모델이 최적인지 모름
  - EasyOCR vs PaddleOCR?
  - GPT-4 vs Claude?
  - 정확도 vs 비용 trade-off

- **개선 효과**:
  - 데이터 기반 모델 선택
  - 비용 최적화
  - 정확도 향상

### 어떻게 구현할까?

**1. 실험 설정 모델**

```python
# shared/models/ab_experiment.py
class ABExperiment(Base):
    """A/B 테스트 실험"""
    __tablename__ = "ab_experiments"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))  # "OCR 모델 비교"
    variant_a = Column(JSON)  # {"ocr": "easyocr", "llm": "gpt-4"}
    variant_b = Column(JSON)  # {"ocr": "paddleocr", "llm": "gpt-4"}

    traffic_split = Column(Float, default=0.5)  # 50/50 분할
    is_active = Column(Boolean, default=True)
```

**2. 트래픽 분할 로직**

```python
import random

def get_experiment_variant(chain_id: str, experiment: ABExperiment):
    """실험 그룹 할당"""

    # 일관성 있는 할당 (같은 chain_id는 항상 같은 그룹)
    hash_value = int(hashlib.md5(chain_id.encode()).hexdigest(), 16)

    if (hash_value % 100) < (experiment.traffic_split * 100):
        return experiment.variant_a
    else:
        return experiment.variant_b
```

**3. 결과 분석**

```python
# 실험 결과 조회
SELECT
    variant,
    COUNT(*) as total,
    AVG(accuracy_score) as avg_accuracy,
    AVG(processing_time) as avg_time,
    AVG(cost) as avg_cost
FROM ab_test_results
WHERE experiment_id = 1
GROUP BY variant;
```

**4. API 통합**

```python
@router.post("/cr-extract")
async def create_cr_extract_job(file: UploadFile):
    """CR 추출 (A/B 테스트 지원)"""

    chain_id = str(uuid.uuid4())

    # 활성 실험 조회
    experiment = get_active_experiment(db)

    if experiment:
        # 실험 그룹 할당
        options = get_experiment_variant(chain_id, experiment)
    else:
        # 기본 옵션
        options = default_options

    # 파이프라인 시작
    start_cr_extract_pipeline(file_path, options)
```

---

## 5. 사용자 피드백: 결과 수정 및 재학습

### 왜 필요한가?

- **현재 문제**: 잘못된 결과를 사용자가 수정할 방법 없음
  - OCR 오류를 수정할 수 없음
  - 모델이 개선되지 않음
  - 반복적인 오류 발생

- **개선 효과**:
  - 사용자가 결과 수정 가능
  - 수정 데이터로 모델 재학습
  - 점진적 정확도 향상

### 어떻게 구현할까?

**1. 피드백 모델**

```python
# shared/models/user_feedback.py
class UserFeedback(Base):
    """사용자 피드백"""
    __tablename__ = "user_feedbacks"

    id = Column(Integer, primary_key=True)
    chain_id = Column(String(255), index=True)

    # 원본 결과
    original_result = Column(JSON)

    # 사용자 수정 결과
    corrected_result = Column(JSON)

    # 피드백 타입
    feedback_type = Column(String(50))  # "ocr_error", "llm_error", "layout_error"

    # 메타 정보
    user_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
```

**2. 피드백 API**

```python
@router.post("/feedback/{chain_id}")
async def submit_feedback(
    chain_id: str,
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """사용자 피드백 제출"""

    # ChainExecution 조회
    chain_exec = db.query(ChainExecution).filter(
        ChainExecution.chain_id == chain_id
    ).first()

    # 피드백 저장
    user_feedback = UserFeedback(
        chain_id=chain_id,
        original_result=chain_exec.final_result,
        corrected_result=feedback.corrected_result,
        feedback_type=feedback.feedback_type,
        user_id=feedback.user_id
    )
    db.add(user_feedback)
    db.commit()

    # 재학습 큐에 추가 (비동기)
    add_to_training_queue.delay(user_feedback.id)

    return {"message": "Feedback submitted"}
```

**3. 재학습 파이프라인**

```python
# celery_worker/tasks/training_tasks.py
@celery.task
def retrain_ocr_model():
    """피드백 데이터로 OCR 모델 재학습"""

    # 1. 피드백 데이터 수집
    feedbacks = db.query(UserFeedback).filter(
        UserFeedback.feedback_type == "ocr_error",
        UserFeedback.is_used_for_training == False
    ).limit(1000).all()

    # 2. 학습 데이터 준비
    training_data = prepare_training_data(feedbacks)

    # 3. 모델 재학습 (fine-tuning)
    model = load_base_ocr_model()
    model.fine_tune(training_data)

    # 4. 모델 저장
    model.save("models/ocr_v2.pt")

    # 5. 피드백 사용 표시
    for fb in feedbacks:
        fb.is_used_for_training = True
    db.commit()
```

**4. 피드백 대시보드**

```python
@router.get("/feedback/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """피드백 통계 조회"""

    stats = db.query(
        UserFeedback.feedback_type,
        func.count(UserFeedback.id).label('count')
    ).group_by(UserFeedback.feedback_type).all()

    return {
        "total_feedbacks": sum(s.count for s in stats),
        "by_type": {s.feedback_type: s.count for s in stats},
        "training_ready": get_training_ready_count(db)
    }
```

---

## 구현 우선순위

개선 항목들의 추천 구현 순서:

1. **웹소켓 알림** (난이도: 중, 효과: 높음)
   - 사용자 경험 즉시 개선
   - 서버 부하 감소

2. **결과 캐싱** (난이도: 낮, 효과: 높음)
   - 빠른 구현 가능
   - 비용 절감 효과 큼

3. **배치 처리** (난이도: 중, 효과: 중)
   - 대량 처리 시나리오에서 필수

4. **사용자 피드백** (난이도: 중, 효과: 장기적)
   - 점진적 품질 개선

5. **A/B 테스트** (난이도: 높, 효과: 장기적)
   - 데이터 기반 최적화
   - 충분한 트래픽 필요

---

**[← 이전: 배포 및 확장](./08_deployment.md)** | **[다음: 참고 자료 →](./10_references.md)** | **[목차](./README.md)**
