# Celery 태스크 모니터링 시스템 아키텍처

## 개요

이 문서는 FastAPI + Celery 환경에서 구현된 태스크 모니터링 및 파이프라인 추적 시스템의 아키텍처를 설명합니다.

## 시스템 구성 요소

### 1. 핵심 컴포넌트

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Celery Signals    │────│   TaskInfo Model    │────│   TaskService       │
│   (실시간 추적)       │    │   (데이터 영속화)     │    │   (API 인터페이스)    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   PostgreSQL        │    │   Redis Backend     │    │   REST API          │
│   (메타데이터 저장)   │    │   (Celery 결과)     │    │   (사용자 인터페이스) │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## 2. 데이터 모델

### TaskInfo 모델 구조

```sql
CREATE TABLE task_info (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,     -- Celery 태스크 UUID
    status VARCHAR(255) NOT NULL,             -- STARTED, SUCCESS, FAILURE, etc.
    task_name VARCHAR(255) NOT NULL,          -- 예: app.tasks.ai_pipeline_orchestrator
    args TEXT,                                -- 태스크 인수
    kwargs TEXT,                              -- 태스크 키워드 인수
    result TEXT,                              -- 태스크 결과
    error_message TEXT,                       -- 오류 메시지
    traceback TEXT,                           -- 스택 트레이스
    retry_count INTEGER DEFAULT 0,            -- 재시도 횟수
    
    -- 체인/파이프라인 지원
    root_task_id VARCHAR,                     -- 체인의 루트 태스크
    parent_task_id VARCHAR,                   -- 직접적인 부모 태스크
    chain_total INTEGER,                      -- 체인의 전체 태스크 수
    
    -- 타임스탬프
    task_time TIMESTAMP WITH TIME ZONE,      -- 태스크 시작 시간
    completed_time TIMESTAMP WITH TIME ZONE, -- 태스크 완료 시간
    
    -- 인덱스
    INDEX idx_task_id (task_id),
    INDEX idx_root_task_id (root_task_id),
    INDEX idx_parent_task_id (parent_task_id)
);
```

### 체인 구조 예시

```
Pipeline: ai_pipeline_orchestrator (root)
├── stage1_preprocessing (parent: root)
├── stage2_feature_extraction (parent: stage1)
├── stage3_model_inference (parent: stage2)
└── stage4_post_processing (parent: stage3)
```

## 3. 시그널 기반 실시간 추적

### 3.1 Celery 시그널 핸들러

```python
# app/core/celery_signals.py

@signals.task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **kwds):
    """태스크 시작 전 - 데이터베이스에 초기 정보 저장"""
    
@signals.task_postrun.connect  
def task_postrun_handler(sender, task_id, task, retval, state, **kwds):
    """태스크 완료 후 - 결과 및 상태 업데이트"""
    
@signals.task_failure.connect
def task_failure_handler(sender, task_id, exception, traceback, **kwds):
    """태스크 실패 시 - 오류 정보 저장"""
    
@signals.task_retry.connect
def task_retry_handler(sender, task_id, reason, **kwds):
    """태스크 재시도 시 - 재시도 카운트 증가"""
```

### 3.2 체인 정보 추출

```python
def extract_chain_info(task, task_id: str) -> Dict[str, Any]:
    """태스크에서 chain 관련 정보를 추출"""
    chain_info = {}
    
    if hasattr(task, 'request'):
        # Root task ID (체인의 첫 번째 태스크)
        if hasattr(task.request, 'root_id'):
            chain_info['root_task_id'] = task.request.root_id
            
        # Parent task ID (직접적인 부모)  
        if hasattr(task.request, 'parent_id'):
            chain_info['parent_task_id'] = task.request.parent_id
            
        # Chain 정보
        if hasattr(task.request, 'chain'):
            chain_info['chain_total'] = len(task.request.chain) + 1
            
    return chain_info
```

## 4. 파이프라인 상태 조회 시스템

### 4.1 하이브리드 접근법

```python
def get_pipeline_status(self, pipeline_id: str) -> PipelineStatusResponse:
    """Redis + PostgreSQL + AsyncResult 트리플 하이브리드 조회"""
    
    # 1. PostgreSQL에서 체인 구조 파악
    chain_task_ids = self._get_chain_task_ids(pipeline_id)
    
    # 2. 각 태스크별 3-tier 데이터 조회
    for task_id in chain_task_ids:
        # Tier 1: Redis에서 task_name + 기본 정보
        redis_data = self._get_redis_task_meta(task_id)
        task_name = redis_data.get('task_name')
        
        # Tier 2: AsyncResult에서 실시간 상태
        async_result = celery_app.AsyncResult(task_id)
        current_state = async_result.state
        is_ready = async_result.ready()
        
        # Tier 3: PostgreSQL에서 fallback 정보
        db_data = self._get_db_task_info(task_id)
        fallback_task_name = db_data.task_name if db_data else None
        
        # 우선순위 결합
        final_task_name = task_name or fallback_task_name or 'unknown'
```

### 4.1.2 Redis 메타데이터 향상

```python
# Celery 시그널에서 Redis에 task_name 자동 저장
@signals.task_prerun.connect
def store_task_name_in_redis_early(task_id: str, task_name: str):
    redis_client.hset(f"celery-task-meta-{task_id}", mapping={
        "task_name": task_name,
        "status": "STARTED",
        "start_time": datetime.now().isoformat()
    })

@signals.task_postrun.connect
def update_redis_task_meta(sender, task_id, task_name, state):
    redis_client.hset(f"celery-task-meta-{task_id}", "task_name", task_name)
```

### 4.2 데이터 소스별 역할

| 데이터 소스 | 제공하는 정보 | 장점 | 단점 |
|-------------|---------------|------|------|
| **PostgreSQL** | 체인 정보, 히스토리, traceback | 영속적, 정확함, 복잡한 쿼리 | 실시간성 부족 |
| **Redis (Enhanced)** | 실시간 상태, task_name, 현재 결과 | 빠른 실시간 업데이트 | 휘발성 |
| **AsyncResult** | 정확한 state, ready() 상태 | Celery 네이티브 | task_name 없음 |

### 4.3 상태 결정 로직

```python
# 전체 파이프라인 상태 결정
if all(task.status == 'SUCCESS' for task in tasks):
    overall_state = 'SUCCESS'
elif any(task.status == 'FAILURE' for task in tasks):
    overall_state = 'FAILURE'  
elif any(task.status in ['PROGRESS', 'STARTED'] for task in tasks):
    overall_state = 'PROGRESS'
else:
    overall_state = 'PENDING'
```

## 5. API 인터페이스

### 5.1 파이프라인 생성

```http
POST /api/v1/tasks/ai-pipeline
{
    "text": "처리할 텍스트",
    "options": {},
    "priority": 5
}
```

**응답:**
```json
{
    "success": true,
    "data": {
        "pipeline_id": "4fceefce-64d8-41a1-9941-f62aa4152e63",
        "status": "STARTED",
        "message": "AI 처리 파이프라인이 시작되었습니다",
        "estimated_duration": 20
    }
}
```

### 5.2 파이프라인 상태 조회

```http
GET /api/v1/tasks/ai-pipeline/{pipeline_id}/status
```

**응답:**
```json
{
    "success": true,
    "data": {
        "pipeline_id": "4fceefce-64d8-41a1-9941-f62aa4152e63",
        "overall_state": "PROGRESS",
        "total_steps": 2,
        "tasks": [
            {
                "task_id": "4fceefce-64d8-41a1-9941-f62aa4152e63",
                "status": "SUCCESS", 
                "task_name": "app.tasks.ai_pipeline_orchestrator",
                "result": "Pipeline orchestrated successfully",
                "step": 1,
                "ready": true
            },
            {
                "task_id": "b0e5b703-8a53-44fe-9cac-83e5372a655d",
                "status": "PROGRESS",
                "task_name": "app.tasks.stage1_preprocessing", 
                "result": "{\"stage\": 1, \"progress\": 50}",
                "step": 2,
                "ready": false
            }
        ]
    }
}
```

### 5.3 태스크 히스토리 조회

```http
GET /api/v1/tasks/history?hours=24&status=SUCCESS&limit=100
```

## 6. 성능 최적화

### 6.1 데이터베이스 연결 최적화

```python
class TaskService:
    def __init__(self):
        # 동기식 DB 연결 풀 (태스크 조회용)
        sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        self.sync_engine = create_engine(sync_db_url)
        self.SyncSessionLocal = sessionmaker(bind=self.sync_engine)
```

### 6.2 인덱스 전략

```sql
-- 체인 조회 최적화
CREATE INDEX idx_root_task_id ON task_info(root_task_id);
CREATE INDEX idx_parent_task_id ON task_info(parent_task_id);

-- 시간 범위 조회 최적화  
CREATE INDEX idx_task_time ON task_info(task_time);

-- 상태별 조회 최적화
CREATE INDEX idx_status_time ON task_info(status, task_time);
```

### 6.3 메모리 관리

- **Context Manager**: 데이터베이스 연결 자동 해제
- **Thread-Safe**: RLock을 사용한 동시성 제어
- **Connection Pool**: SQLAlchemy 연결 풀 활용

## 7. 모니터링 및 로깅

### 7.1 구조화된 로깅

```python
logger.info(f"🔗 Chain 태스크: {task_name} "
           f"(Root: {chain_info['root_task_id']}, "
           f"Parent: {chain_info.get('parent_task_id', 'None')}, "
           f"Total: {chain_info.get('chain_total', '?')})")
```

### 7.2 메트릭 수집

- 태스크 성공률
- 평균 실행 시간
- 체인 완료율
- 에러 발생 빈도

## 8. 확장성 고려사항

### 8.1 수평 확장

- **다중 워커**: Celery 워커 스케일링
- **데이터베이스 샤딩**: task_id 기반 분산
- **캐싱 레이어**: Redis를 통한 빈번한 조회 캐싱

### 8.2 고가용성

- **Failover**: AsyncResult fallback 메커니즘
- **Data Consistency**: 트랜잭션을 통한 데이터 일관성
- **Error Handling**: 각 단계별 예외 처리

## 9. 보안 고려사항

- **민감 정보**: args/kwargs에서 민감 데이터 마스킹
- **접근 제어**: API 엔드포인트 인증/권한 부여
- **감사 로그**: 모든 태스크 실행 기록 유지

## 10. 사용 예시

### AI 파이프라인 실행 플로우

```python
# 1. 파이프라인 시작
pipeline_id = create_ai_pipeline({
    "text": "분석할 텍스트",
    "options": {"model": "gpt-4"}
})

# 2. 실시간 상태 추적
while True:
    status = get_pipeline_status(pipeline_id)
    if status.overall_state in ['SUCCESS', 'FAILURE']:
        break
    time.sleep(1)

# 3. 결과 확인
final_result = status.tasks[-1].result
```

이 아키텍처는 Celery의 분산 특성과 데이터베이스의 영속성을 결합하여 확장 가능하고 신뢰할 수 있는 태스크 모니터링 시스템을 제공합니다.