## 테스트 전략

### 단위 테스트

```python
# tests/test_ocr_stage.py
import pytest
from celery_worker.tasks.stages.ocr_stage import OCRStage
from shared.pipeline.context import PipelineContext

@pytest.mark.asyncio
async def test_ocr_stage_success():
    """OCR 단계 정상 실행 테스트"""
    # Given
    context = PipelineContext(
        context_id="test-001",
        input_file_path="/path/to/test.jpg",
        options={"ocr_engine": "easyocr"}
    )
    stage = OCRStage()

    # When
    result = await stage.run(context)

    # Then
    assert result.ocr_result is not None
    assert "text" in result.ocr_result
    assert result.status == "ocrstage_completed"

@pytest.mark.asyncio
async def test_ocr_stage_validation_error():
    """OCR 단계 입력 검증 실패 테스트"""
    # Given
    context = PipelineContext(
        context_id="test-002",
        input_file_path="",  # 빈 경로
        options={}
    )
    stage = OCRStage()

    # When / Then
    with pytest.raises(ValueError, match="input_file_path is required"):
        await stage.run(context)
```

### 통합 테스트

```python
# tests/test_pipeline_integration.py
import pytest
from celery_worker.tasks.pipeline_tasks import start_cr_extract_pipeline

@pytest.mark.integration
def test_full_pipeline_execution():
    """전체 파이프라인 실행 테스트"""
    # Given
    test_file_path = "/path/to/test_cr_document.pdf"
    options = {
        "ocr_engine": "mock",  # 테스트용 mock 엔진
        "llm_model": "mock"
    }

    # When
    context_id = start_cr_extract_pipeline(test_file_path, options)

    # Wait for completion (테스트 환경에서는 동기 실행)
    # ...

    # Then
    context = load_context_from_redis(context_id)
    assert context.status == "completed"
    assert context.excel_file_path is not None
```

