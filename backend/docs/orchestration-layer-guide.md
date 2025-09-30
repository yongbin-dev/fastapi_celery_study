# 오케스트레이션 레이어 가이드

## 📋 개요

**오케스트레이션 레이어**는 여러 도메인(OCR, LLM, Vision)을 조합하여 복잡한 워크플로우를 구성하는 계층입니다.

## 🏗️ 아키텍처 구조

```
app/
├── domains/                  # 개별 도메인 (단일 책임)
│   ├── ocr/                 # OCR 전용
│   ├── llm/                 # LLM 전용
│   └── vision/              # Vision 전용
│
├── orchestration/            # 🆕 도메인 간 오케스트레이션
│   ├── pipelines/           # 파이프라인 정의
│   │   ├── ai_pipeline.py           # OCR+LLM+Vision 조합
│   │   ├── document_pipeline.py     # 문서 처리 전용
│   │   └── image_pipeline.py        # 이미지 분석 전용
│   │
│   ├── workflows/           # Celery 워크플로우 패턴
│   │   └── workflow_builder.py      # Chain, Chord, Group 빌더
│   │
│   ├── services/            # 오케스트레이션 비즈니스 로직
│   │   └── pipeline_service.py
│   │
│   └── controllers/         # 파이프라인 API
│       └── pipeline_controller.py
│
├── core/                    # 공통 인프라
└── shared/                  # 공유 유틸리티
```

## 🎯 책임 분리

### 도메인 레이어 (`app/domains/`)
- **단일 책임**: 각 도메인은 자신의 기능만 수행
- **독립성**: 다른 도메인에 의존하지 않음
- **예시**:
  - OCR: 이미지 → 텍스트 추출
  - LLM: 텍스트 → 텍스트 생성
  - Vision: 이미지 → 객체 탐지

### 오케스트레이션 레이어 (`app/orchestration/`)
- **조합 책임**: 여러 도메인을 연결하여 워크플로우 구성
- **순서 제어**: Celery Chain, Chord, Group 활용
- **예시**:
  - AI 파이프라인: OCR → LLM → Vision 순차 실행
  - 문서 분석: OCR → LLM 요약
  - 병렬 처리: OCR + Vision 동시 실행

## 📦 주요 구성 요소

### 1. 파이프라인 정의 (`orchestration/pipelines/`)

여러 도메인을 조합한 워크플로우 템플릿:

```python
# app/orchestration/pipelines/ai_pipeline.py

def create_ai_processing_pipeline(chain_id: str, input_data: Dict[str, Any]):
    """
    AI 처리 파이프라인: 전처리 → 특성 추출 → 모델 추론 → 후처리
    """
    from app.core.celery.celery_tasks import (
        stage1_preprocessing,
        stage2_feature_extraction,
        stage3_model_inference,
        stage4_post_processing,
    )

    pipeline = chain(
        stage1_preprocessing.s(chain_id, input_data),
        stage2_feature_extraction.s(),
        stage3_model_inference.s(),
        stage4_post_processing.s(),
    )

    return pipeline


def create_document_pipeline(chain_id: str, document_path: str):
    """
    문서 처리 파이프라인: OCR → LLM 요약
    """
    from app.domains.ocr.tasks.ocr_tasks import extract_text_task
    from app.domains.llm.tasks.llm_tasks import generate_text_task

    pipeline = chain(
        extract_text_task.s(document_path),
        generate_text_task.s(),
    )

    return pipeline
```

### 2. 워크플로우 빌더 (`orchestration/workflows/`)

Celery 패턴을 쉽게 구성:

```python
# app/orchestration/workflows/workflow_builder.py

class WorkflowBuilder:
    """순차/병렬 워크플로우 빌더"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.tasks = []

    def add_task(self, task, *args, **kwargs):
        """태스크 추가"""
        self.tasks.append(task.s(*args, **kwargs))
        return self

    def build_chain(self):
        """순차 실행 Chain 생성"""
        return chain(*self.tasks)

    def build_group(self):
        """병렬 실행 Group 생성"""
        return group(*self.tasks)


class MultiDomainWorkflow:
    """다중 도메인 조합 워크플로우"""

    @staticmethod
    def parallel_processing(image_path: str):
        """OCR + Vision 병렬 실행"""
        from app.domains.ocr.tasks.ocr_tasks import extract_text_task
        from app.domains.vision.tasks.detection_tasks import detect_objects_task

        parallel_tasks = group(
            extract_text_task.s(image_path),
            detect_objects_task.s(image_path),
        )

        return parallel_tasks
```

### 3. 파이프라인 서비스 (`orchestration/services/`)

파이프라인 생명주기 관리:

```python
# app/orchestration/services/pipeline_service.py

class PipelineService:
    """파이프라인 오케스트레이션 서비스"""

    async def create_ai_pipeline(
        self, db: AsyncSession, redis_service: RedisService, request: AIPipelineRequest
    ) -> AIPipelineResponse:
        """AI 파이프라인 시작"""

        # 1. DB에 실행 기록 생성
        chain_execution = ChainExecution(...)
        db.add(chain_execution)
        await db.commit()

        # 2. Redis 초기화
        redis_service.initialize_pipeline_stages(chain_id)

        # 3. 파이프라인 실행
        pipeline = create_ai_processing_pipeline(chain_id, input_data)
        pipeline.apply_async()

        return AIPipelineResponse(...)
```

### 4. API 컨트롤러 (`orchestration/controllers/`)

파이프라인 REST API:

```python
# app/orchestration/controllers/pipeline_controller.py

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])

@router.post("/ai-pipeline")
async def create_ai_pipeline(request: AIPipelineRequest):
    """AI 파이프라인 시작"""
    result = await service.create_ai_pipeline(...)
    return ResponseBuilder.success(data=result)

@router.get("/ai-pipeline/{chain_id}/tasks")
async def get_pipeline_tasks(chain_id: str):
    """파이프라인 태스크 조회"""
    result = await service.get_pipeline_tasks(chain_id=chain_id)
    return ResponseBuilder.success(data=result)
```

## 🔄 Celery 워크플로우 패턴

### 1. Chain (순차 실행)

```python
from celery import chain

# OCR → LLM → Vision 순서대로 실행
workflow = chain(
    ocr_task.s(image_path),      # 1단계: OCR
    llm_task.s(),                 # 2단계: LLM (OCR 결과 사용)
    vision_task.s(image_path),    # 3단계: Vision
)
workflow.apply_async()
```

### 2. Group (병렬 실행)

```python
from celery import group

# OCR + Vision 동시 실행
workflow = group(
    ocr_task.s(image_path),
    vision_task.s(image_path),
)
workflow.apply_async()
```

### 3. Chord (병렬 실행 후 콜백)

```python
from celery import chord

# OCR + Vision 병렬 실행 후 결과 통합
workflow = chord(
    [ocr_task.s(image_path), vision_task.s(image_path)]
)(merge_results_task.s())

workflow.apply_async()
```

## 📝 새 파이프라인 추가하기

### 단계 1: 파이프라인 정의 생성

`app/orchestration/pipelines/my_pipeline.py`:

```python
from celery import chain

def create_my_custom_pipeline(chain_id: str, input_data: dict):
    """
    커스텀 파이프라인: OCR → LLM 요약 → 결과 저장
    """
    from app.domains.ocr.tasks.ocr_tasks import extract_text_task
    from app.domains.llm.tasks.llm_tasks import generate_text_task
    # from app.tasks.storage_tasks import save_result_task  # 가상 태스크

    pipeline = chain(
        extract_text_task.s(input_data["image_path"]),
        generate_text_task.s(),
        # save_result_task.s(chain_id),
    )

    return pipeline
```

### 단계 2: 서비스에 메서드 추가

`app/orchestration/services/pipeline_service.py`:

```python
async def create_my_custom_pipeline(
    self, db: AsyncSession, request: MyCustomRequest
) -> MyCustomResponse:
    """커스텀 파이프라인 시작"""

    chain_id = str(uuid.uuid4())

    # DB 기록 생성
    chain_execution = ChainExecution(...)
    db.add(chain_execution)
    await db.commit()

    # 파이프라인 실행
    from app.orchestration.pipelines.my_pipeline import create_my_custom_pipeline

    pipeline = create_my_custom_pipeline(chain_id, request.dict())
    pipeline.apply_async()

    return MyCustomResponse(...)
```

### 단계 3: API 엔드포인트 추가

`app/orchestration/controllers/pipeline_controller.py`:

```python
@router.post("/my-custom-pipeline")
async def create_my_custom_pipeline(
    request: MyCustomRequest,
    service: PipelineService = Depends(get_pipeline_service),
    db: AsyncSession = Depends(get_db),
):
    """커스텀 파이프라인 실행"""
    result = await service.create_my_custom_pipeline(db=db, request=request)
    return ResponseBuilder.success(data=result)
```

## 🎨 실제 사용 예시

### 예시 1: 문서 분석 파이프라인

```bash
# API 요청
POST /api/v1/pipelines/document-analysis
{
  "document_path": "/uploads/contract.pdf"
}

# 워크플로우
1. OCR: PDF → 텍스트 추출
2. LLM: 주요 내용 요약
3. LLM: 법률 조항 분석
4. 결과 통합 및 저장
```

### 예시 2: 이미지 콘텐츠 분석

```bash
# API 요청
POST /api/v1/pipelines/image-analysis
{
  "image_path": "/uploads/photo.jpg"
}

# 워크플로우 (병렬)
1-1. Vision: 객체 탐지
1-2. OCR: 이미지 내 텍스트 추출
2. LLM: 통합 설명 생성
```

## ⚠️ 주의사항

### 1. 도메인 간 의존성 최소화

❌ **잘못된 예**: 도메인이 다른 도메인을 직접 호출
```python
# app/domains/ocr/services/ocr_service.py (나쁜 예)
from app.domains.llm.tasks.llm_tasks import generate_text_task  # ❌ 도메인 간 의존

def process(self, image_path):
    text = self.extract(image_path)
    summary = generate_text_task.delay(text)  # ❌ 다른 도메인 호출
```

✅ **올바른 예**: 오케스트레이션 레이어에서 조합
```python
# app/orchestration/pipelines/document_pipeline.py (좋은 예)
def create_document_pipeline(image_path):
    pipeline = chain(
        extract_text_task.s(image_path),    # OCR 도메인
        generate_text_task.s(),              # LLM 도메인
    )
    return pipeline
```

### 2. 태스크 네임스페이스 준수

각 도메인 태스크는 고유한 네임스페이스를 사용:

```python
# OCR 도메인
@celery_app.task(name="ocr.extract_text")

# LLM 도메인
@celery_app.task(name="llm.generate_text")

# Vision 도메인
@celery_app.task(name="vision.detect_objects")
```

## 📊 API 엔드포인트

### 오케스트레이션 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/pipelines/ai-pipeline` | AI 처리 파이프라인 시작 |
| GET | `/api/v1/pipelines/ai-pipeline/{chain_id}/tasks` | 파이프라인 태스크 조회 |
| DELETE | `/api/v1/pipelines/ai-pipeline/{chain_id}/cancel` | 파이프라인 취소 |
| GET | `/api/v1/pipelines/history` | 파이프라인 히스토리 조회 |

### 도메인별 API

| 도메인 | 경로 | 설명 |
|--------|------|------|
| LLM | `/api/v1/llm/*` | LLM 단일 작업 |
| OCR | `/api/v1/ocr/*` | OCR 단일 작업 |
| Vision | `/api/v1/vision/*` | Vision 단일 작업 |

## 🚀 다음 단계

1. **새 파이프라인 개발**: 비즈니스 요구사항에 맞는 커스텀 파이프라인 추가
2. **워크플로우 최적화**: Chord, Group을 활용한 병렬 처리
3. **모니터링 강화**: Flower에서 파이프라인별 성능 추적
4. **에러 핸들링**: 파이프라인 실패 시 재시도 및 롤백 전략

## 📚 참고 문서

- [아키텍처 개선 제안](./architecture-improvement.md)
- [도메인 개발 가이드](./domain-setup-guide.md)
- [Celery 공식 문서 - Canvas](https://docs.celeryq.dev/en/stable/userguide/canvas.html)