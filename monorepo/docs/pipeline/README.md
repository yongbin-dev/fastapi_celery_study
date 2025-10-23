# CR 추출 파이프라인 구현 가이드

> 복잡한 OCR → LLM → Layout → Excel 파이프라인을 위한 설계 및 구현 가이드

## 📋 목차

1. [개요](./00_overview.md)
   - 목적
   - 처리 흐름
   - 주요 요구사항

2. [설계 원칙](./01_design_principles.md)
   - 선택된 패턴: Pipeline 패턴 + Celery Chain
   - 대안 패턴 비교
   - Celery 통합 전략

3. [아키텍처](./02_architecture.md)
   - 디렉토리 구조
   - 데이터 흐름
   - 데이터 저장 전략

4. [핵심 컴포넌트](./03_components.md)
   - PipelineContext (공유 데이터 구조)
   - PipelineStage (추상 기본 클래스)
   - Celery 태스크 구조
   - Stage 구현 예시 (OCR, LLM, Layout, Excel)
   - API 엔드포인트

5. [DB 진행 상황 추적](./04_db_tracking.md)
   - DB 모델 정의 (ChainExecution, TaskLog)
   - ProcessStatus Enum
   - CRUD 함수
   - Celery Signals 통합
   - Pipeline 시작 시 ChainExecution 생성
   - API 엔드포인트
   - 장점 및 데이터 흐름

6. [에러 핸들링](./05_error_handling.md)
   - 예외 계층 구조
   - 재시도 정책
   - 에러 복구 전략

7. [모니터링 및 운영](./06_monitoring.md)
   - 로깅
   - Celery Flower 모니터링
   - 메트릭 수집

8. [테스트 전략](./07_testing.md)
   - 단위 테스트
   - 통합 테스트

9. [배포 및 확장](./08_deployment.md)
   - 환경 변수
   - 확장 고려사항

10. [향후 개선 방향](./09_improvements.md)

11. [참고 자료](./10_references.md)

12. [Pipeline 실행 제어와 동적 구성 ](./11_pipeline_orchestration.md)


---

## 🚀 빠른 시작

### 처리 흐름

```
이미지/PDF → OCR → LLM 분석 → 레이아웃 분석 → Excel 생성
```

### 주요 기술 스택

- **Backend**: FastAPI, Celery
- **Worker**: Celery Worker (비동기 처리)
- **ML**: EasyOCR, PaddleOCR
- **LLM**: OpenAI GPT-4
- **Database**: PostgreSQL, Redis
- **Storage**: Supabase

### 핵심 설계

- **패턴**: Pipeline 패턴 + Celery Chain
- **DB 추적**: ChainExecution (chain 전체) + TaskLog (개별 task)
- **자동화**: Celery Signals를 통한 자동 DB 업데이트

---

## 📂 프로젝트 구조

```
packages/
├── shared/
│   ├── pipeline/
│   │   ├── context.py          # PipelineContext
│   │   ├── stage.py            # PipelineStage 추상 클래스
│   │   ├── orchestrator.py     # PipelineOrchestrator
│   │   └── exceptions.py       # 예외 정의
│   ├── models/
│   │   ├── chain_execution.py  # ChainExecution 모델
│   │   └── task_log.py         # TaskLog 모델
│   └── repository/crud/
│       └── sync_crud/
│           ├── chain_execution.py
│           └── task_log.py
├── celery_worker/
│   ├── core/
│   │   ├── celery_app.py
│   │   └── celery_signals.py  # Celery Signals 정의
│   └── tasks/
│       ├── pipeline_tasks.py   # Celery 태스크
│       └── stages/
│           ├── ocr_stage.py
│           ├── llm_stage.py
│           ├── layout_stage.py
│           └── excel_stage.py
└── api_server/
    └── domains/pipeline/
        ├── controllers/
        │   └── pipeline_controller.py
        └── services/
            └── pipeline_service.py
```

---

## 🔗 관련 문서

- [uv 워크스페이스 설정](../uv-workspace-setup.md)
- [프로젝트 CLAUDE.md](../../CLAUDE.md)

---

## 📝 문서 작성 정보

- **최초 작성**: 2025-10-23
- **마지막 업데이트**: 2025-10-23
- **작성자**: Claude Code + User
- **버전**: 1.0
