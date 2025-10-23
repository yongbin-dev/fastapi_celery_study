## 설계 원칙

### 선택된 패턴: Pipeline 패턴 + Celery Chain

**왜 이 방식인가?**

현재 프로젝트의 Celery 기반 비동기 처리 인프라를 최대한 활용하면서:

- ✅ 각 단계를 독립적으로 실행/재시도 가능
- ✅ 확장 가능 (새로운 단계 추가 용이)
- ✅ 테스트 및 모니터링 용이
- ✅ 리소스 효율적 (단계별 병렬 처리 가능)

### 대안 패턴 비교

| 패턴 | 장점 | 단점 | 적합성 |
|------|------|------|--------|
| **Pipeline 패턴** | 명확한 데이터 흐름, 테스트 용이 | Context 객체 설계 필요 | ✅ **채택** |
| Chain of Responsibility | 단계 추가/제거 용이 | 데이터 전달 복잡 | ⚠️ 복잡도 증가 |
| Saga 패턴 | 강력한 에러 복구 | 구현 복잡도 높음 | ❌ 과도한 설계 |

### Celery 통합 전략

**선택: 각 단계를 별도 Celery 태스크로 분리 + Chain 연결**

```python
# ✅ 추천 방식
chain(
    ocr_stage_task.s(context_id),
    llm_stage_task.s(),
    layout_stage_task.s(),
    excel_stage_task.s()
).apply_async()
```

**장점:**
- 단계별 독립적인 재시도 정책 설정
- 부분 실패 시 해당 단계부터만 재실행
- Celery Flower로 각 단계 모니터링
- 여러 파일 동시 처리 시 병렬 실행

