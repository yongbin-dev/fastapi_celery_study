# Redis 데이터 구조 변경 가이드

## 개요
`chain_id`로 조회할 때 전체 태스크 목록이 배열로 반환되도록 Redis 데이터 구조를 변경했습니다.

## 변경 전 vs 변경 후

### 변경 전 (단일 객체 구조)
```json
{
  "chain_id": "example-chain-123",
  "stage": 2,
  "status": "PENDING",
  "progress": 50,
  "created_at": 1640995200.0,
  "updated_at": 1640995260.0,
  "metadata": {
    "stage_name": "특성 추출",
    "substep": "벡터화"
  }
}
```

### 변경 후 (배열 구조)
```json
[
  {
    "chain_id": "example-chain-123",
    "stage": 1,
    "status": "SUCCESS",
    "progress": 100,
    "created_at": 1640995200.0,
    "updated_at": 1640995230.0,
    "metadata": {
      "stage_name": "데이터 전처리",
      "execution_time": 4.2
    }
  },
  {
    "chain_id": "example-chain-123",
    "stage": 2,
    "status": "PENDING",
    "progress": 50,
    "updated_at": 1640995260.0,
    "metadata": {
      "stage_name": "특성 추출",
      "substep": "벡터화"
    }
  },
  {
    "chain_id": "example-chain-123",
    "stage": 3,
    "status": "PENDING",
    "progress": 0,
    "updated_at": 1640995260.0,
    "metadata": {
      "stage_name": "모델 추론"
    }
  },
  {
    "chain_id": "example-chain-123",
    "stage": 4,
    "status": "PENDING",
    "progress": 0,
    "updated_at": 1640995260.0,
    "metadata": {
      "stage_name": "후처리"
    }
  }
]
```

## 주요 개선사항

### 1. 전체 파이프라인 가시성
- 한 번의 조회로 모든 단계의 상태 확인 가능
- 파이프라인 전체 진행 상황 한눈에 파악

### 2. 단계별 추적
- 각 단계의 개별 상태, 진행률, 메타데이터 추적
- 실행 시간 등 상세 메트릭 포함

### 3. 레거시 호환성
- 기존 단일 객체 데이터도 자동으로 배열로 변환
- 점진적 마이그레이션 지원

## API 엔드포인트

### 1. 전체 태스크 목록 조회
```http
GET /api/v1/tasks/ai-pipeline/{chain_id}/tasks
```

**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "chain_id": "example-chain-123",
      "stage": 1,
      "status": "SUCCESS",
      "progress": 100,
      "created_at": 1640995200.0,
      "updated_at": 1640995230.0,
      "metadata": {
        "stage_name": "데이터 전처리",
        "execution_time": 4.2
      }
    }
  ],
  "message": "체인 'example-chain-123'의 태스크 목록 조회 완료 (총 4개 태스크)"
}
```

### 2. 특정 단계 조회
```http
GET /api/v1/tasks/ai-pipeline/{chain_id}/stage/{stage}
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "chain_id": "example-chain-123",
    "stage": 2,
    "status": "PENDING",
    "progress": 70,
    "updated_at": 1640995260.0,
    "metadata": {
      "stage_name": "특성 추출",
      "substep": "벡터화"
    }
  },
  "message": "체인 'example-chain-123'의 단계 2 태스크 상태 조회 완료"
}
```

## 사용 예시

### Python 클라이언트
```python
import requests

# 전체 파이프라인 상태 조회
response = requests.get("http://localhost:5050/api/v1/tasks/ai-pipeline/example-chain-123/tasks")
pipeline_tasks = response.json()["data"]

# 진행률 계산
total_progress = sum(task["progress"] for task in pipeline_tasks) / len(pipeline_tasks)
print(f"전체 진행률: {total_progress}%")

# 실패한 단계 확인
failed_stages = [task for task in pipeline_tasks if task["status"] == "FAILURE"]
if failed_stages:
    print(f"실패한 단계: {[task['stage'] for task in failed_stages]}")
```

### JavaScript 클라이언트
```javascript
// 전체 파이프라인 상태 조회
const response = await fetch('/api/v1/tasks/ai-pipeline/example-chain-123/tasks');
const { data: pipelineTasks } = await response.json();

// 현재 실행 중인 단계 찾기
const currentStage = pipelineTasks.find(task => 
  task.status === 'PENDING' && task.progress > 0
);

// 완료된 단계 수 계산
const completedStages = pipelineTasks.filter(task => 
  task.status === 'SUCCESS'
).length;

console.log(`완료된 단계: ${completedStages}/4`);
```

## Redis 명령어 예시

### 직접 조회
```bash
# Redis에서 직접 조회
redis-cli GET "example-chain-123"

# 결과 (JSON 배열)
"[{\"chain_id\":\"example-chain-123\",\"stage\":1,\"status\":\"SUCCESS\",\"progress\":100,\"created_at\":1640995200.0,\"updated_at\":1640995230.0,\"metadata\":{\"stage_name\":\"데이터 전처리\",\"execution_time\":4.2}}]"
```

### TTL 확인
```bash
# TTL 확인
redis-cli TTL "example-chain-123"

# 결과 (초 단위)
3541
```

## 마이그레이션 가이드

### 기존 코드 업데이트
기존에 단일 객체로 처리하던 코드는 다음과 같이 업데이트해야 합니다:

```python
# 변경 전
pipeline_data = redis_client.get(chain_id)
if pipeline_data:
    task_info = json.loads(pipeline_data)
    current_stage = task_info["stage"]

# 변경 후
pipeline_data = status_manager.get_pipeline_status(chain_id)
if pipeline_data:
    # 가장 최근 업데이트된 단계 찾기
    current_task = max(pipeline_data, key=lambda x: x.get("updated_at", 0))
    current_stage = current_task["stage"]
```

이제 더 구조화되고 확장 가능한 Redis 데이터 구조를 사용할 수 있습니다!