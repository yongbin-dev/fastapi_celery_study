# 파이프라인 오케스트레이션

**[← 이전: 참고 자료](./10_references.md)** | **[목차](./README.md)**

---

Pipeline 실행 순서를 동적으로 제어하고, 조건부 분기를 구현하는 방법을 설명합니다.

## 1. 기본 Chain (고정된 순서)

가장 단순한 형태로, 순서가 고정된 파이프라인입니다.

```python
# celery_worker/tasks/pipeline_tasks.py
from celery import chain

def start_cr_extract_pipeline(chain_id: str):
    """고정된 순서로 실행되는 기본 파이프라인"""

    workflow = chain(
        ocr_stage_task.s(chain_id),
        llm_stage_task.s(),
        layout_stage_task.s(),
        excel_stage_task.s()
    )

    result = workflow.apply_async()
    return result
```

**장점**:
- 구현이 단순하고 명확
- 예측 가능한 실행 흐름

**단점**:
- 유연성 부족
- 모든 단계가 항상 실행됨

---

## 2. 동적 Chain 구성 (Runtime 순서 결정)

실행 시점에 옵션에 따라 task 순서를 결정합니다.

```python
# api_server/domains/pipeline/services/pipeline_service.py

class CRExtractOptions(BaseModel):
    """파이프라인 실행 옵션"""
    enable_llm_analysis: bool = True
    enable_layout_analysis: bool = True
    output_format: str = "excel"  # "excel" | "json" | "csv"


def start_cr_extract_pipeline(
    file_path: str,
    options: CRExtractOptions
):
    """옵션에 따라 동적으로 파이프라인 구성"""

    chain_id = str(uuid.uuid4())

    # Task 리스트를 동적으로 구성
    tasks = []

    # 1. OCR은 항상 필수
    tasks.append(ocr_stage_task.s(chain_id))

    # 2. LLM 분석 optional
    if options.enable_llm_analysis:
        tasks.append(llm_stage_task.s())

    # 3. Layout 분석 optional
    if options.enable_layout_analysis:
        tasks.append(layout_stage_task.s())

    # 4. 출력 형식에 따라 다른 task
    if options.output_format == "excel":
        tasks.append(excel_stage_task.s())
    elif options.output_format == "json":
        tasks.append(json_export_task.s())
    elif options.output_format == "csv":
        tasks.append(csv_export_task.s())

    # 동적으로 구성된 chain 실행
    workflow = chain(*tasks)
    workflow.apply_async()

    return chain_id
```

**장점**:
- 필요한 단계만 실행 (성능 향상)
- 비용 절감 (LLM API 호출 스킵 가능)

**단점**:
- 복잡도 증가
- 테스트 케이스 증가

---

## 3. 조건부 분기 (Task 결과에 따른 경로 변경)

이전 task의 결과를 보고 다음 단계를 결정합니다.

### 3.1. OCR 품질 기반 분기

```python
# celery_worker/tasks/ocr_tasks.py

@celery.task(bind=True)
def ocr_stage_task(self, chain_id: str):
    """OCR 처리 후 품질에 따라 다음 단계 결정"""

    # OCR 실행
    result = run_ocr(chain_id)

    # OCR 품질 평가 (0.0 ~ 1.0)
    quality_score = evaluate_ocr_quality(result)

    if quality_score < 0.5:
        # 품질이 낮으면 재시도 경로
        logger.warning(f"Low OCR quality: {quality_score}, retrying...")
        retry_ocr_task.apply_async(args=[chain_id])
    else:
        # 품질이 좋으면 다음 단계 진행
        llm_stage_task.apply_async(args=[chain_id])

    return result


def evaluate_ocr_quality(ocr_result: dict) -> float:
    """OCR 결과 품질 평가"""

    # 신뢰도 점수 평균
    confidence_scores = [
        word.get("confidence", 0.0)
        for word in ocr_result.get("words", [])
    ]

    if not confidence_scores:
        return 0.0

    return sum(confidence_scores) / len(confidence_scores)
```

### 3.2. 문서 복잡도 기반 분기

```python
# celery_worker/tasks/llm_tasks.py

@celery.task(bind=True)
def llm_stage_task(self, chain_id: str, prev_result: dict):
    """LLM 분석 후 복잡도에 따라 경로 결정"""

    result = run_llm_analysis(chain_id, prev_result)

    # 문서 복잡도 평가
    complexity = result.get("complexity", "simple")

    if complexity == "complex":
        # 복잡한 문서는 고급 레이아웃 분석
        logger.info(f"Complex document detected, using advanced layout")
        advanced_layout_task.apply_async(args=[chain_id, result])
    else:
        # 단순 문서는 기본 레이아웃 분석
        logger.info(f"Simple document, using basic layout")
        layout_stage_task.apply_async(args=[chain_id, result])

    return result
```

**장점**:
- 지능적인 처리 경로 선택
- 품질과 성능 최적화

**단점**:
- 디버깅 어려움 (실행 경로가 동적)
- 평가 로직 구현 필요

---

## 4. Group + Chord (병렬 + 순차 조합)

여러 task를 병렬로 실행한 후, 결과를 모아서 처리합니다.

```python
# celery_worker/tasks/batch_tasks.py
from celery import group, chord

def start_parallel_cr_extract(file_paths: List[str]):
    """여러 파일을 병렬로 OCR 처리 후, 결과를 통합"""

    # 1단계: 모든 파일 병렬 OCR
    ocr_tasks = group(
        ocr_stage_task.s(str(uuid.uuid4()), path)
        for path in file_paths
    )

    # 2단계: OCR 완료 후 통합 분석
    # chord = group 실행 후 callback 실행
    workflow = chord(ocr_tasks)(
        merge_and_analyze_task.s()
    )

    workflow.apply_async()


@celery.task
def merge_and_analyze_task(ocr_results: List[dict]):
    """병렬 OCR 결과를 통합하여 분석"""

    logger.info(f"Merging {len(ocr_results)} OCR results")

    # 모든 텍스트 통합
    merged_text = "\n\n".join([
        result.get("text", "")
        for result in ocr_results
    ])

    # 통합 LLM 분석
    analysis = run_llm_analysis_on_text(merged_text)

    return analysis
```

**사용 시나리오**:
- 여러 페이지 PDF를 페이지별 병렬 OCR
- 다중 파일 배치 처리
- 성능 최적화 (병렬 처리)

---

## 5. 우선순위 기반 순서 제어

Task의 중요도에 따라 실행 우선순위를 설정합니다.

### 5.1. 큐별 우선순위 설정

```python
# celery_worker/core/celery_app.py

celery.conf.task_routes = {
    # 긴급: OCR은 가장 먼저
    'tasks.ocr_stage_task': {
        'queue': 'high_priority',
        'priority': 9
    },

    # 중간: LLM 분석
    'tasks.llm_stage_task': {
        'queue': 'medium_priority',
        'priority': 5
    },

    # 낮음: Excel 생성
    'tasks.excel_stage_task': {
        'queue': 'low_priority',
        'priority': 1
    },
}

# Worker 실행 시 큐 우선순위 지정
# celery -A celery_worker.core.celery_app worker \
#   -Q high_priority,medium_priority,low_priority
```

### 5.2. Task 실행 시 우선순위 지정

```python
# 긴급 요청
ocr_stage_task.apply_async(
    args=[chain_id],
    priority=9,  # 0-9, 높을수록 먼저 실행
    queue='high_priority'
)

# 일반 요청
ocr_stage_task.apply_async(
    args=[chain_id],
    priority=5,
    queue='medium_priority'
)
```

---

## 6. 실전 예시: PipelineOrchestrator

유연하고 확장 가능한 파이프라인 오케스트레이터 구현입니다.

```python
# api_server/domains/pipeline/services/pipeline_orchestrator.py

from typing import List, Dict, Callable
from celery import chain
from celery_worker.tasks.pipeline_tasks import (
    ocr_stage_task,
    llm_stage_task,
    layout_stage_task,
    excel_stage_task,
    json_export_task,
    csv_export_task,
)


class PipelineOrchestrator:
    """Pipeline 순서를 동적으로 제어하는 오케스트레이터"""

    # 사전 정의된 파이프라인 설정
    PIPELINE_CONFIGS = {
        "basic": ["ocr", "excel"],
        "advanced": ["ocr", "llm", "layout", "excel"],
        "analysis_only": ["ocr", "llm"],
        "export_only": ["ocr", "excel"],
        "custom": None  # 사용자 정의
    }

    def __init__(self):
        # Task 이름 → Celery task 매핑
        self.task_registry: Dict[str, Callable] = {
            "ocr": ocr_stage_task,
            "llm": llm_stage_task,
            "layout": layout_stage_task,
            "excel": excel_stage_task,
            "json": json_export_task,
            "csv": csv_export_task,
        }

    def create_pipeline(
        self,
        chain_id: str,
        pipeline_type: str = "advanced",
        custom_order: List[str] = None
    ):
        """Pipeline 타입에 따라 task 순서 결정 및 생성"""

        # 1. 순서 결정
        if pipeline_type == "custom" and custom_order:
            order = custom_order
        else:
            order = self.PIPELINE_CONFIGS.get(
                pipeline_type,
                ["ocr", "excel"]  # 기본값
            )

        # 2. Task 리스트 구성
        tasks = []
        for i, task_name in enumerate(order):
            task = self.task_registry.get(task_name)

            if not task:
                raise ValueError(f"Unknown task: {task_name}")

            if i == 0:
                # 첫 번째 task는 chain_id를 받음
                tasks.append(task.s(chain_id))
            else:
                # 나머지는 이전 결과를 받음
                tasks.append(task.s())

        # 3. Chain 생성
        workflow = chain(*tasks)
        return workflow

    def start(
        self,
        chain_id: str,
        pipeline_type: str = "advanced",
        custom_order: List[str] = None,
        priority: int = 5
    ):
        """Pipeline 시작"""

        workflow = self.create_pipeline(
            chain_id=chain_id,
            pipeline_type=pipeline_type,
            custom_order=custom_order
        )

        # 우선순위와 함께 실행
        result = workflow.apply_async(priority=priority)

        return result

    def validate_order(self, order: List[str]) -> bool:
        """Task 순서 유효성 검증"""

        # OCR은 항상 첫 번째여야 함
        if not order or order[0] != "ocr":
            return False

        # 모든 task가 등록되어 있어야 함
        for task_name in order:
            if task_name not in self.task_registry:
                return False

        return True
```

### 6.1. API 엔드포인트 구현

```python
# api_server/domains/pipeline/controllers/pipeline_controller.py

from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    """Pipeline 실행 요청"""
    pipeline_type: str = "advanced"  # "basic" | "advanced" | "analysis_only" | "custom"
    custom_order: Optional[List[str]] = None
    priority: int = 5  # 0-9


@router.post("/cr-extract")
async def create_cr_extract_job(
    file: UploadFile,
    request: PipelineRequest
):
    """CR 추출 파이프라인 시작"""

    # 파일 저장
    chain_id = str(uuid.uuid4())
    file_path = await save_uploaded_file(file, chain_id)

    # Orchestrator 생성
    orchestrator = PipelineOrchestrator()

    # 사용자 정의 순서 검증
    if request.pipeline_type == "custom":
        if not request.custom_order:
            raise HTTPException(
                status_code=400,
                detail="custom_order is required for custom pipeline"
            )

        if not orchestrator.validate_order(request.custom_order):
            raise HTTPException(
                status_code=400,
                detail="Invalid task order. OCR must be first."
            )

    # Pipeline 시작
    try:
        orchestrator.start(
            chain_id=chain_id,
            pipeline_type=request.pipeline_type,
            custom_order=request.custom_order,
            priority=request.priority
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "chain_id": chain_id,
        "pipeline_type": request.pipeline_type,
        "order": request.custom_order or orchestrator.PIPELINE_CONFIGS[request.pipeline_type]
    }


@router.get("/pipeline-types")
async def get_available_pipeline_types():
    """사용 가능한 파이프라인 타입 조회"""

    orchestrator = PipelineOrchestrator()

    return {
        "types": list(orchestrator.PIPELINE_CONFIGS.keys()),
        "configs": orchestrator.PIPELINE_CONFIGS,
        "available_tasks": list(orchestrator.task_registry.keys())
    }
```

---

## 7. API 사용 예시

### 7.1. 기본 파이프라인 (OCR → LLM → Layout → Excel)

```bash
curl -X POST "http://localhost:8000/pipeline/cr-extract" \
  -F "file=@document.pdf" \
  -F 'request={"pipeline_type": "advanced"}'
```

**Response**:
```json
{
  "chain_id": "abc123...",
  "pipeline_type": "advanced",
  "order": ["ocr", "llm", "layout", "excel"]
}
```

### 7.2. 간단한 파이프라인 (OCR → Excel)

```bash
curl -X POST "http://localhost:8000/pipeline/cr-extract" \
  -F "file=@document.pdf" \
  -F 'request={"pipeline_type": "basic"}'
```

### 7.3. 사용자 정의 순서 (OCR → Layout → JSON)

```bash
curl -X POST "http://localhost:8000/pipeline/cr-extract" \
  -F "file=@document.pdf" \
  -F 'request={"pipeline_type": "custom", "custom_order": ["ocr", "layout", "json"]}'
```

### 7.4. 높은 우선순위로 실행

```bash
curl -X POST "http://localhost:8000/pipeline/cr-extract" \
  -F "file=@document.pdf" \
  -F 'request={"pipeline_type": "advanced", "priority": 9}'
```

### 7.5. 사용 가능한 파이프라인 타입 조회

```bash
curl -X GET "http://localhost:8000/pipeline/pipeline-types"
```

**Response**:
```json
{
  "types": ["basic", "advanced", "analysis_only", "export_only", "custom"],
  "configs": {
    "basic": ["ocr", "excel"],
    "advanced": ["ocr", "llm", "layout", "excel"],
    "analysis_only": ["ocr", "llm"],
    "export_only": ["ocr", "excel"],
    "custom": null
  },
  "available_tasks": ["ocr", "llm", "layout", "excel", "json", "csv"]
}
```

---

## 8. DB 추적 통합

PipelineOrchestrator는 기존 DB 추적 시스템과 완벽하게 호환됩니다.

```python
# celery_worker/core/celery_signals.py

@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, **kwargs):
    """Task 시작 전 - 어떤 순서든 자동으로 추적"""

    chain_id = args[0]
    db = next(get_db())

    try:
        # ChainExecution 조회
        chain_exec = chain_execution_crud.get_by_chain_id(db, chain_id=chain_id)

        if chain_exec:
            # TaskLog 생성 (task 이름은 자동 감지)
            task_log_crud.create_task_log(
                db=db,
                task_id=task_id,
                task_name=task.name,  # "ocr_stage_task", "llm_stage_task" 등
                status=ProcessStatus.STARTED.value,
                chain_execution_id=chain_exec.id
            )
    finally:
        db.close()
```

**장점**:
- Pipeline 순서가 바뀌어도 자동으로 추적됨
- 사용자 정의 순서도 정상 추적
- 조건부 분기도 모두 기록됨

---

## 9. 실행 경로 시각화

다양한 실행 경로를 다이어그램으로 표현하면:

### 9.1. 기본 경로
```
파일 업로드
    ↓
OCR Task
    ↓
LLM Task
    ↓
Layout Task
    ↓
Excel Task
    ↓
완료
```

### 9.2. 조건부 분기 경로
```
파일 업로드
    ↓
OCR Task
    ↓
품질 평가
    ├─ 낮음 → Retry OCR → LLM Task
    └─ 높음 → LLM Task
            ↓
        복잡도 평가
            ├─ 복잡 → Advanced Layout
            └─ 단순 → Basic Layout
                    ↓
                Excel Task
                    ↓
                완료
```

### 9.3. 사용자 정의 경로
```
파일 업로드
    ↓
OCR Task
    ↓
[사용자가 선택한 순서대로 실행]
    ↓
완료
```

---

## 10. 모니터링 및 디버깅

### 10.1. 실행 경로 로깅

```python
# celery_worker/tasks/pipeline_tasks.py

@celery.task(bind=True)
def ocr_stage_task(self, chain_id: str):
    """실행 경로를 로깅하는 OCR task"""

    logger.info(f"[Pipeline Route] {chain_id} - Starting OCR stage")

    result = run_ocr(chain_id)

    # 다음 경로 결정 및 로깅
    quality = evaluate_ocr_quality(result)

    if quality < 0.5:
        logger.warning(f"[Pipeline Route] {chain_id} - Low quality, retry path")
        next_task = retry_ocr_task
    else:
        logger.info(f"[Pipeline Route] {chain_id} - Good quality, LLM path")
        next_task = llm_stage_task

    next_task.apply_async(args=[chain_id])

    return result
```

### 10.2. Flower 대시보드에서 경로 확인

Celery Flower를 실행하면 실제 실행된 task 순서를 확인할 수 있습니다:

```bash
# Flower 실행
celery -A celery_worker.core.celery_app flower --port=5555

# http://localhost:5555 에서 확인
```

---

## 11. 장단점 비교

| 방법 | 장점 | 단점 | 사용 시나리오 |
|------|------|------|---------------|
| **고정 Chain** | 단순, 예측 가능 | 유연성 없음 | 표준 워크플로우 |
| **동적 Chain** | 유연, 효율적 | 복잡도 증가 | 옵션 기반 실행 |
| **조건부 분기** | 지능적 처리 | 디버깅 어려움 | 품질 기반 선택 |
| **Group+Chord** | 병렬 처리 가능 | 구현 복잡 | 배치 처리 |
| **우선순위 제어** | 리소스 최적화 | 큐 관리 필요 | 긴급 요청 처리 |
| **Orchestrator** | 매우 유연 | 초기 구현 비용 | 복잡한 시스템 |

---

## 12. 권장 사항

### 12.1. 시작 단계
1. **고정 Chain**으로 시작 (간단한 구현)
2. 기본 기능 검증

### 12.2. 발전 단계
3. **동적 Chain** 추가 (옵션 지원)
4. **우선순위 제어** 도입 (성능 최적화)

### 12.3. 고급 단계
5. **Orchestrator 패턴** 적용 (유연성 확보)
6. **조건부 분기** 추가 (지능적 처리)
7. **Group+Chord** 활용 (병렬 처리)

---

**[← 이전: 참고 자료](./10_references.md)** | **[목차](./README.md)**
