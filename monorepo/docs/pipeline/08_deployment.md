## 배포 및 확장

### 환경 변수

```bash
# .env
REDIS_URL=redis://localhost:6379/0
ML_SERVER_URL=http://ml-server:8001
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Celery 설정
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 확장 고려사항

1. **워커 스케일링**: Celery 워커 수 조정
   ```bash
   celery -A celery_worker.core.celery_app worker -c 4  # 4개의 워커
   ```

2. **큐 분리**: 단계별로 별도 큐 사용
   ```python
   @celery.task(queue='ocr_queue')
   def ocr_stage_task(...): ...

   @celery.task(queue='llm_queue')
   def llm_stage_task(...): ...
   ```

3. **우선순위 처리**: 긴급 요청 우선 처리
   ```python
   workflow.apply_async(priority=9)  # 0-9, 높을수록 우선
   ```

