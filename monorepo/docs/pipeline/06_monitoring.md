## 모니터링 및 운영

### 로깅

```python
# 각 Stage에서 구조화된 로깅
import logging
import structlog

logger = structlog.get_logger(__name__)

class OCRStage(PipelineStage):
    async def execute(self, context: PipelineContext):
        logger.info(
            "ocr_stage_started",
            context_id=context.context_id,
            file_path=context.input_file_path,
            ocr_engine=context.options.get("ocr_engine")
        )

        # ... 처리 ...

        logger.info(
            "ocr_stage_completed",
            context_id=context.context_id,
            text_length=len(context.ocr_result["text"]),
            confidence=context.ocr_result["confidence"]
        )
```

### Celery Flower 모니터링

```bash
# Flower 실행
celery -A celery_worker.core.celery_app flower --port=5555

# 브라우저에서 접속
http://localhost:5555
```

**모니터링 가능한 정보:**
- 각 태스크 실행 상태 (성공/실패/진행중)
- 재시도 횟수 및 에러 로그
- 처리 시간 통계
- 워커 상태 및 리소스 사용량

### 메트릭 수집 (선택적)

```python
# Prometheus 메트릭 예시
from prometheus_client import Counter, Histogram

pipeline_started = Counter(
    'pipeline_started_total',
    'Total pipelines started'
)

pipeline_completed = Counter(
    'pipeline_completed_total',
    'Total pipelines completed',
    ['status']  # success, failed
)

stage_duration = Histogram(
    'pipeline_stage_duration_seconds',
    'Stage execution duration',
    ['stage_name']
)

# 사용
pipeline_started.inc()
with stage_duration.labels(stage_name='OCRStage').time():
    # ... stage execution ...
    pass
```

