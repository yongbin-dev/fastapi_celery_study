# Celery 신호를 통한 DB 저장 예제

현재 스키마에 맞춰서 Celery 신호를 통해 자동으로 DB에 작업 정보를 저장하는 시스템입니다.

## 🚀 주요 기능

### 자동 추적되는 정보들

1. **TaskLog**: 모든 Celery 작업의 생명주기
2. **TaskMetadata**: 작업 메타데이터 (큐, 우선순위 등)
3. **TaskExecutionHistory**: 각 시도별 실행 기록
4. **TaskResult**: 작업 결과 (성공/실패)
5. **WorkerStatus**: 워커 상태 및 통계
6. **QueueStats**: 큐 통계 (주기적 수집)

### 처리되는 Celery 신호들

- `before_task_publish`: 작업 발행 시 → TaskLog, TaskMetadata 생성
- `task_prerun`: 작업 시작 시 → TaskLog 상태 업데이트, TaskExecutionHistory 생성
- `task_success`: 작업 성공 시 → TaskLog, TaskResult, TaskExecutionHistory 업데이트
- `task_failure`: 작업 실패 시 → 에러 정보 저장
- `task_retry`: 작업 재시도 시 → 재시도 기록
- `task_revoked`: 작업 취소 시 → 취소 상태 저장
- `worker_ready`: 워커 시작 시 → WorkerStatus 생성/업데이트
- `worker_shutdown`: 워커 종료 시 → WorkerStatus 업데이트
- `heartbeat_sent`: 워커 하트비트 → WorkerStatus 갱신

## 📋 사용 방법

### 1. 기본 설정

Celery 앱이 시작될 때 자동으로 신호가 등록됩니다:

```python
# app/core/celery_app.py에서 자동 import
from . import celery_signals
```

### 2. 테스트 실행

```bash
# 1. 워커 시작
python -m celery -A app.core.celery_app worker --loglevel=info

# 2. 별도 터미널에서 테스트 실행
python test_celery_signals.py
```

### 3. 작업 정의 예제

```python
from app.core.celery_app import celery_app

@celery_app.task(bind=True, name='my_custom_task')
def my_custom_task(self, data):
    """사용자 정의 작업 - 자동으로 DB에 기록됩니다"""
    # 작업 로직
    result = process_data(data)
    
    # 진행률 업데이트 (선택사항)
    self.update_state(
        state='PROGRESS',
        meta={'current': 50, 'total': 100}
    )
    
    return result

# 작업 실행
task = my_custom_task.delay({"key": "value"})
```

### 4. 재시도 가능한 작업

```python
@celery_app.task(
    bind=True, 
    name='retry_task',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def retry_task(self, data):
    """자동 재시도 작업"""
    if random.random() < 0.7:  # 70% 확률로 실패
        raise Exception("일시적 오류")
    
    return {"status": "success"}
```

## 📊 DB에서 확인할 수 있는 정보

### TaskLog 테이블
```sql
SELECT 
    task_id,
    task_name,
    status,
    started_at,
    completed_at,
    retries,
    (completed_at - started_at) as duration
FROM task_logs 
ORDER BY created_at DESC 
LIMIT 10;
```

### WorkerStatus 테이블
```sql
SELECT 
    worker_name,
    status,
    active_tasks,
    processed_tasks,
    failed_tasks,
    (processed_tasks - failed_tasks) * 100.0 / processed_tasks as success_rate
FROM worker_status;
```

### TaskExecutionHistory 테이블
```sql
SELECT 
    t.task_name,
    h.attempt_number,
    h.status,
    h.started_at,
    h.completed_at,
    h.error_message
FROM task_execution_history h
JOIN task_logs t ON h.task_id = t.id
ORDER BY h.started_at DESC;
```

## 🔧 고급 사용법

### 1. 사용자 정의 메타데이터 추가

```python
@celery_app.task(bind=True)
def task_with_metadata(self, data, user_id=None):
    """사용자 정의 메타데이터가 있는 작업"""
    # 메타데이터는 TaskMetadata 테이블에 자동 저장됨
    return process_user_data(data, user_id)

# 사용
task = task_with_metadata.apply_async(
    args=[data],
    kwargs={'user_id': 123},
    priority=5,  # 우선순위
    eta=datetime.now() + timedelta(minutes=5)  # 실행 시간
)
```

### 2. 통계 정보 조회

```python
from app.core.celery_signals import get_task_statistics
from app.core.database import SyncSessionLocal

session = SyncSessionLocal()
stats = get_task_statistics(session)
print(stats)  # {'SUCCESS': 45, 'FAILURE': 5, 'PENDING': 2}
session.close()
```

### 3. 오래된 레코드 정리

```python
from app.core.celery_signals import cleanup_old_records
from app.core.database import SyncSessionLocal

session = SyncSessionLocal()
deleted_count = cleanup_old_records(session, days=30)
print(f"정리된 레코드: {deleted_count}개")
session.close()
```

## 🎯 실시간 모니터링

### 1. Flower 대시보드
```bash
python -m celery -A app.core.celery_app flower --port=5555
```
브라우저에서 http://localhost:5555 접속

### 2. 프로그래밍 방식 모니터링

```python
from app.core.database import SyncSessionLocal
from app.models import TaskLog, WorkerStatus

def get_realtime_status():
    session = SyncSessionLocal()
    try:
        # 실행 중인 작업
        running_tasks = session.query(TaskLog).filter_by(status='STARTED').all()
        
        # 온라인 워커
        online_workers = session.query(WorkerStatus).filter_by(status='ONLINE').all()
        
        return {
            'running_tasks': len(running_tasks),
            'online_workers': len(online_workers),
            'tasks': [{'id': t.task_id, 'name': t.task_name} for t in running_tasks]
        }
    finally:
        session.close()
```

## ⚡ 성능 최적화

### 1. 배치 처리를 위한 신호 비활성화 (선택사항)

```python
from celery import group

# 대량 작업 시 신호 오버헤드 방지
@celery_app.task(bind=True, track_started=False)
def batch_task(self, data):
    """배치 처리용 작업 (시작 신호 비활성화)"""
    return process_batch(data)

# 그룹으로 실행
job = group(batch_task.s(item) for item in large_dataset)
result = job.apply_async()
```

### 2. 중요한 작업만 추적

```python
@celery_app.task(bind=True, name='critical_task')
def critical_task(self, data):
    """중요한 작업 - 상세 추적"""
    return process_critical_data(data)

@celery_app.task(bind=True, name='simple_task', track_started=False)
def simple_task(self, data):
    """단순한 작업 - 최소 추적"""
    return process_simple_data(data)
```

## 🐛 트러블슈팅

### 1. 신호가 작동하지 않는 경우

```python
# celery_app.py에서 import 순서 확인
from . import celery_signals  # 이게 최상단에 있어야 함
```

### 2. DB 연결 오류

```python
# celery_signals.py의 get_db_session() 함수 확인
# 로그에서 "DB 세션 생성 실패" 메시지 확인
```

### 3. 메모리 사용량 증가

```python
# 주기적으로 오래된 레코드 정리
from app.core.celery_signals import cleanup_old_records

# crontab으로 주기적 실행 권장
# 0 2 * * * cd /path/to/project && python -c "from app.core.celery_signals import cleanup_old_records; from app.core.database import SyncSessionLocal; session = SyncSessionLocal(); cleanup_old_records(session, 30); session.close()"
```

## 📈 모니터링 대시보드 구축

실제 프로덕션에서는 이 데이터를 활용해 Grafana나 커스텀 대시보드를 구축할 수 있습니다:

```python
# API 엔드포인트 예제
from fastapi import APIRouter
from app.core.database import SyncSessionLocal
from app.models import TaskLog, WorkerStatus

router = APIRouter()

@router.get("/task-stats")
def get_task_stats():
    session = SyncSessionLocal()
    try:
        stats = session.query(TaskLog.status, func.count(TaskLog.id))\
            .group_by(TaskLog.status).all()
        return {status: count for status, count in stats}
    finally:
        session.close()

@router.get("/worker-status")
def get_worker_status():
    session = SyncSessionLocal()
    try:
        workers = session.query(WorkerStatus).all()
        return [worker.to_dict() for worker in workers]
    finally:
        session.close()
```

이제 모든 Celery 작업이 자동으로 DB에 기록되고 추적됩니다! 🎉