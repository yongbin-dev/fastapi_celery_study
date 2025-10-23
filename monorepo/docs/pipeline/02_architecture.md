## 아키텍처

### 디렉토리 구조

```
packages/
├── shared/
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── context.py          # PipelineContext - 전체 파이프라인 상태/데이터
│   │   ├── stage.py            # PipelineStage - 추상 기본 클래스
│   │   ├── orchestrator.py     # PipelineOrchestrator - 실행 조율
│   │   └── exceptions.py       # StageError, PipelineError 등
│   └── models/
│       └── pipeline_run.py     # DB 모델 (실행 이력)
│
├── celery_worker/
│   └── tasks/
│       ├── pipeline_tasks.py   # Celery 태스크 정의 (진입점)
│       ├── stages/
│       │   ├── __init__.py
│       │   ├── ocr_stage.py    # OCR 처리 로직
│       │   ├── llm_stage.py    # LLM 분석 로직
│       │   ├── layout_stage.py # 레이아웃 분석
│       │   └── excel_stage.py  # Excel 생성
│       └── orchestration.py    # 파이프라인 시작/관리
│
└── api_server/
    └── domains/
        └── pipeline/
            ├── controllers/
            │   └── pipeline_controller.py  # API 엔드포인트
            ├── services/
            │   └── pipeline_service.py     # 비즈니스 로직
            └── schemas/
                └── pipeline_schemas.py     # Request/Response 스키마
```

### 데이터 흐름

```
┌─────────────┐
│ 1. API 요청 │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│ 2. PipelineContext 생성      │
│    context_id 발급           │
│    Redis에 저장              │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 3. Celery Chain 시작         │
└──────┬───────────────────────┘
       │
       ├─► OCR Task ──────► Context 업데이트 ──► Redis
       │
       ├─► LLM Task ──────► Context 업데이트 ──► Redis
       │
       ├─► Layout Task ───► Context 업데이트 ──► Redis
       │
       └─► Excel Task ────► Context 업데이트 ──► Redis + DB + Supabase

       ▼
┌──────────────────────────────┐
│ 4. 클라이언트 폴링           │
│    GET /status/{context_id}  │
└──────────────────────────────┘
```

### 데이터 저장 전략

| 데이터 종류 | 저장소 | 이유 |
|------------|--------|------|
| 중간 실행 상태 | Redis | 빠른 읽기/쓰기, TTL 설정 가능 |
| 최종 결과 파일 | Supabase Storage | 대용량 파일, 영구 보관 |
| 실행 메타데이터 | PostgreSQL | 검색/분석 용이, 영구 보관 |

