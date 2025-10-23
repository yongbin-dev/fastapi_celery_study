## 에러 핸들링

### 예외 계층 구조

```python
# shared/pipeline/exceptions.py

class PipelineError(Exception):
    """파이프라인 기본 예외"""
    pass

class StageError(PipelineError):
    """단계 실행 실패"""
    def __init__(self, stage_name: str, message: str):
        self.stage_name = stage_name
        super().__init__(f"[{stage_name}] {message}")

class RetryableError(StageError):
    """재시도 가능한 오류 (네트워크, 일시적 오류)"""
    pass

class FatalError(StageError):
    """재시도 불가능한 치명적 오류 (데이터 오류, 설정 오류)"""
    pass

class ValidationError(FatalError):
    """입력/출력 검증 실패"""
    pass
```

### 재시도 정책

| 단계 | 재시도 횟수 | 재시도 조건 | Backoff |
|------|------------|------------|---------|
| OCR | 3회 | 네트워크 오류, 타임아웃 | Exponential (최대 10분) |
| LLM | 3회 | Rate limit, API 오류 | Exponential (최대 10분) |
| Layout | 2회 | 처리 오류 | Linear |
| Excel | 2회 | 파일 생성 오류 | Linear |

### 에러 복구 전략

1. **부분 재실행**: 실패한 단계부터 재시작
   ```python
   # Redis에 저장된 context에서 마지막 성공 단계 확인
   # 해당 단계의 task만 다시 실행
   ```

2. **Dead Letter Queue**: 3회 재시도 실패 시
   ```python
   @celery.task(
       ...,
       on_failure=send_to_dead_letter_queue
   )
   ```

3. **수동 개입 알림**: 치명적 오류 발생 시
   ```python
   if isinstance(error, FatalError):
       send_notification_to_admin(context)
   ```

