# 프로젝트 구조 개선 제안: 팀별 모델 개발 아키텍처

## 📋 현재 프로젝트 분석

### 현재 디렉토리 구조
```
backend/
├── app/
│   ├── api/v1/
│   │   ├── controllers/          # API 엔드포인트 라우터
│   │   ├── crud/                 # 데이터베이스 CRUD 작업
│   │   │   ├── async_crud/
│   │   │   └── sync_crud/
│   │   └── services/             # 비즈니스 로직
│   │       └── ai/               # AI 모델 관련 (현재 LLM만 존재)
│   │           ├── base_model.py
│   │           └── llm_model.py
│   ├── core/                     # 핵심 인프라
│   │   ├── celery/               # Celery 태스크 및 설정
│   │   ├── handler/              # 에러 핸들러
│   │   └── middleware/           # 미들웨어
│   ├── models/                   # SQLAlchemy ORM 모델
│   ├── schemas/                  # Pydantic 스키마
│   └── utils/                    # 유틸리티
├── migrations/                   # Alembic 마이그레이션
├── tests/                        # 테스트
├── docs/                         # 문서
└── scripts/                      # 유틸리티 스크립트
```

### 현재 아키텍처의 문제점

#### 1. **모델 서비스의 확장성 부족**
- `app/api/v1/services/ai/` 디렉토리에 LLM 모델만 존재
- OCR, Vision, Audio 등 다른 모델 추가 시 구조적 한계
- 팀별 독립 개발 시 충돌 가능성 높음

#### 2. **Celery 태스크의 단일 구조**
- `app/core/celery/celery_tasks.py`에 모든 파이프라인 태스크 집중
- 팀별 태스크 추가 시 Git 충돌 빈번
- 모델별 독립적인 배포 어려움

#### 3. **컨트롤러/라우터의 혼재**
- `pipeline_controller.py`에 LLM 예측 엔드포인트 포함
- 모델별 엔드포인트 분리 필요

#### 4. **공유 의존성 관리 부재**
- 팀별로 다른 Python 패키지 및 버전 사용 시 충돌
- 모델별 requirements 분리 필요

---

## 🎯 개선된 디렉토리 구조

### 제안 1: 도메인별 수직 분할 (Domain-Driven Design)

```
backend/
├── app/
│   ├── domains/                  # 🆕 도메인별 모듈화
│   │   ├── ocr/                  # OCR 팀 전용 도메인
│   │   │   ├── __init__.py
│   │   │   ├── models/           # OCR 전용 ORM 모델
│   │   │   │   └── ocr_result.py
│   │   │   ├── schemas/          # OCR 요청/응답 스키마
│   │   │   │   ├── request.py
│   │   │   │   └── response.py
│   │   │   ├── services/         # OCR 비즈니스 로직
│   │   │   │   ├── ocr_service.py
│   │   │   │   └── ocr_model.py  # 모델 로딩 및 추론
│   │   │   ├── tasks/            # OCR Celery 태스크
│   │   │   │   └── ocr_tasks.py
│   │   │   ├── controllers/      # OCR API 엔드포인트
│   │   │   │   └── ocr_controller.py
│   │   │   ├── config.py         # OCR 전용 설정
│   │   │   └── requirements.txt  # OCR 전용 의존성
│   │   │
│   │   ├── llm/                  # LLM 팀 전용 도메인
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   └── conversation.py
│   │   │   ├── schemas/
│   │   │   │   ├── request.py
│   │   │   │   └── response.py
│   │   │   ├── services/
│   │   │   │   ├── llm_service.py
│   │   │   │   └── llm_model.py  # GPT, Llama 등
│   │   │   ├── tasks/
│   │   │   │   └── llm_tasks.py
│   │   │   ├── controllers/
│   │   │   │   └── llm_controller.py
│   │   │   ├── config.py
│   │   │   └── requirements.txt
│   │   │
│   │   ├── vision/               # Vision 팀 전용 도메인
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   └── detection_result.py
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   │   ├── detection_service.py
│   │   │   │   └── segmentation_service.py
│   │   │   ├── tasks/
│   │   │   │   ├── detection_tasks.py
│   │   │   │   └── segmentation_tasks.py
│   │   │   ├── controllers/
│   │   │   │   └── vision_controller.py
│   │   │   ├── config.py
│   │   │   └── requirements.txt
│   │   │
│   │   └── audio/                # Audio 팀 전용 도메인
│   │       ├── services/
│   │       │   ├── stt_service.py
│   │       │   └── tts_service.py
│   │       ├── tasks/
│   │       ├── controllers/
│   │       ├── config.py
│   │       └── requirements.txt
│   │
│   ├── core/                     # 공유 인프라 (변경 최소화)
│   │   ├── celery/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py    # Celery 앱 인스턴스
│   │   │   └── task_decorators.py
│   │   ├── middleware/
│   │   ├── database.py
│   │   ├── redis_client.py
│   │   └── exceptions.py
│   │
│   ├── api/                      # API 버전 관리
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   └── router.py         # 도메인별 라우터 자동 등록
│   │   └── v2/
│   │
│   ├── shared/                   # 🆕 도메인 간 공유 코드
│   │   ├── base_model.py         # 모든 AI 모델의 베이스 클래스
│   │   ├── base_service.py       # 공통 서비스 로직
│   │   ├── response_builder.py
│   │   └── validators.py
│   │
│   └── main.py                   # FastAPI 앱 진입점
│
├── migrations/                   # Alembic 마이그레이션 (공유)
├── tests/
│   ├── test_domains/             # 🆕 도메인별 테스트
│   │   ├── test_ocr/
│   │   ├── test_llm/
│   │   └── test_vision/
│   └── test_core/
│
├── docs/                         # 문서
│   ├── architecture.md
│   ├── domain-guidelines.md      # 🆕 도메인 개발 가이드
│   └── api-conventions.md
│
├── scripts/
│   ├── install_domain_deps.py    # 🆕 도메인별 의존성 설치
│   └── generate_domain.py        # 🆕 새 도메인 스캐폴딩
│
├── pyproject.toml                # 공통 의존성
└── requirements/                 # 🆕 환경별 의존성 관리
    ├── base.txt                  # 필수 공통 패키지
    ├── dev.txt
    ├── prod.txt
    └── domains/
        ├── ocr.txt               # OCR 전용
        ├── llm.txt               # LLM 전용
        └── vision.txt            # Vision 전용
```

---

## 📌 핵심 개선 사항

### 1. **도메인별 완전한 격리**

#### 장점
- ✅ 팀별 독립 개발: 각 팀이 자신의 도메인 디렉토리에서만 작업
- ✅ Git 충돌 최소화: 서로 다른 파일 경로
- ✅ 독립 배포 가능: 도메인별 Docker 이미지 생성 가능
- ✅ 코드 리뷰 간소화: 도메인별 PR 분리

#### 구현 예시: OCR 도메인

```python
# app/domains/ocr/services/ocr_model.py
from app.shared.base_model import BaseModel
from paddleocr import PaddleOCR

class OCRModel(BaseModel):
    def __init__(self):
        self.model = None

    def load_model(self):
        self.model = PaddleOCR(use_angle_cls=True, lang='korean')
        self.is_loaded = True

    def predict(self, input_data):
        result = self.model.ocr(input_data['image_path'])
        return {"text": result, "confidence": 0.95}
```

```python
# app/domains/ocr/tasks/ocr_tasks.py
from app.celery_app import celery_app
from .services.ocr_model import OCRModel

@celery_app.task(bind=True, name="ocr.extract_text")
def extract_text_task(self, image_path: str):
    model = OCRModel()
    model.load_model()
    return model.predict({"image_path": image_path})
```

```python
# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter
from ..schemas.request import OCRRequest
from ..schemas.response import OCRResponse
from ..tasks.ocr_tasks import extract_text_task

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/extract", response_model=OCRResponse)
async def extract_text(request: OCRRequest):
    task = extract_text_task.delay(request.image_path)
    return {"task_id": task.id, "status": "PENDING"}
```

### 2. **Celery 태스크 네임스페이스 분리**

```python
# app/domains/ocr/tasks/ocr_tasks.py
@celery_app.task(name="ocr.extract_text")      # 네임스페이스: ocr.*
def extract_text_task(...): pass

# app/domains/llm/tasks/llm_tasks.py
@celery_app.task(name="llm.generate_text")     # 네임스페이스: llm.*
def generate_text_task(...): pass

# app/domains/vision/tasks/detection_tasks.py
@celery_app.task(name="vision.detect_objects") # 네임스페이스: vision.*
def detect_objects_task(...): pass
```

**장점:**
- 태스크 이름 충돌 방지
- Flower 모니터링에서 팀별 필터링 가능
- 팀별 Celery worker 실행 가능

```bash
# OCR 팀 전용 worker
celery -A app.celery_app worker -Q ocr -n ocr_worker@%h

# LLM 팀 전용 worker
celery -A app.celery_app worker -Q llm -n llm_worker@%h
```

### 3. **의존성 관리 전략**

#### 기존 문제
- 모든 팀의 패키지가 하나의 `pyproject.toml`에 혼재
- PyTorch, TensorFlow, PaddlePaddle 등 대용량 패키지 중복 설치

#### 개선안: 계층적 의존성

```toml
# pyproject.toml (공통 의존성만)
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
celery = "^5.3.4"
redis = "^5.0.1"
sqlalchemy = "^2.0.23"
pydantic = "^2.5.3"

[tool.poetry.group.ocr]
optional = true

[tool.poetry.group.ocr.dependencies]
paddleocr = "^2.7.0"
opencv-python = "^4.9.0"

[tool.poetry.group.llm]
optional = true

[tool.poetry.group.llm.dependencies]
transformers = "^4.36.0"
torch = "^2.1.0"

[tool.poetry.group.vision]
optional = true

[tool.poetry.group.vision.dependencies]
ultralytics = "^8.1.0"
```

**설치 방법:**
```bash
# OCR 팀 개발 환경
poetry install --with ocr

# LLM 팀 개발 환경
poetry install --with llm

# 전체 운영 환경
poetry install --with ocr,llm,vision,prod
```

### 4. **자동 라우터 등록**

```python
# app/api/v1/router.py
from fastapi import APIRouter
from importlib import import_module
import pkgutil
import app.domains

api_router = APIRouter()

# 모든 도메인의 컨트롤러 자동 검색 및 등록
for _, domain_name, _ in pkgutil.iter_modules(app.domains.__path__):
    try:
        controller_module = import_module(f"app.domains.{domain_name}.controllers.{domain_name}_controller")
        api_router.include_router(
            controller_module.router,
            prefix=f"/{domain_name}",
            tags=[domain_name.upper()]
        )
        print(f"✅ Loaded domain: {domain_name}")
    except (ImportError, AttributeError):
        print(f"⚠️ No controller found for domain: {domain_name}")
```

**장점:**
- 새 도메인 추가 시 `main.py` 수정 불필요
- 플러그인 아키텍처처럼 동작
- 도메인 활성화/비활성화 용이

---

## 🔧 마이그레이션 가이드

### 단계 1: 디렉토리 구조 생성

```bash
# 스크립트 실행으로 자동 생성
python scripts/generate_domain.py --name ocr
python scripts/generate_domain.py --name llm
python scripts/generate_domain.py --name vision
```

### 단계 2: 기존 코드 이동

```bash
# LLM 모델 이동
app/api/v1/services/ai/llm_model.py
→ app/domains/llm/services/llm_model.py

# Celery 태스크 분리
app/core/celery/celery_tasks.py
→ app/domains/ocr/tasks/ocr_tasks.py
→ app/domains/llm/tasks/llm_tasks.py
```

### 단계 3: Import 경로 수정

```python
# Before
from app.api.v1.services.ai.llm_model import LLMModel

# After
from app.domains.llm.services.llm_model import LLMModel
```

### 단계 4: 도메인별 요구사항 정의

각 팀에서 작성:
```txt
# requirements/domains/ocr.txt
paddleocr==2.7.0
opencv-python==4.9.0.80
Pillow==10.2.0

# requirements/domains/llm.txt
transformers==4.36.0
torch==2.1.0
sentence-transformers==2.2.2

# requirements/domains/vision.txt
ultralytics==8.1.0
torchvision==0.16.0
```

---

## 📊 비교표

| 항목 | 현재 구조 | 개선된 구조 |
|------|----------|------------|
| **파일 충돌** | 높음 (공유 파일 다수) | 낮음 (도메인 격리) |
| **의존성 관리** | 전체 통합 | 도메인별 선택 설치 |
| **배포 단위** | 단일 앱 | 도메인별 마이크로서비스 가능 |
| **테스트 독립성** | 낮음 | 높음 (도메인별 실행) |
| **새 팀 온보딩** | 복잡 (전체 이해 필요) | 간단 (도메인만 이해) |
| **코드 리뷰** | 전체 팀 검토 | 도메인 팀만 검토 |

---

## 🚀 추가 권장 사항

### 1. **도메인별 Docker 이미지**

```dockerfile
# Dockerfile.ocr
FROM python:3.11-slim
WORKDIR /app
COPY requirements/base.txt .
COPY requirements/domains/ocr.txt .
RUN pip install -r base.txt -r ocr.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### 2. **도메인별 환경 변수**

```env
# .env.ocr
OCR_MODEL_PATH=/models/ocr
OCR_LANGUAGE=korean
OCR_CONFIDENCE_THRESHOLD=0.8

# .env.llm
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7
```

### 3. **도메인 개발 가이드 문서**

각 도메인 디렉토리에 `README.md` 생성:
```markdown
# OCR 도메인

## 팀 정보
- 팀명: OCR Team
- 담당자: @ocr-team
- Slack: #team-ocr

## 로컬 개발
\`\`\`bash
poetry install --with ocr
poetry run pytest tests/test_domains/test_ocr/
\`\`\`

## API 엔드포인트
- POST /api/v1/ocr/extract - 텍스트 추출
- GET /api/v1/ocr/models - 사용 가능한 모델 목록
```

---

## ✅ 결론

### 핵심 개선 효과

1. **팀별 병렬 개발**: 각 팀이 독립적으로 작업하여 개발 속도 향상
2. **유지보수성 향상**: 도메인별로 명확한 책임 분리
3. **확장성**: 새로운 모델/팀 추가 시 기존 코드 영향 최소화
4. **배포 유연성**: 도메인별 개별 배포 또는 전체 통합 배포 선택 가능

### 단계적 적용 방안

**Phase 1 (1주차):**
- `app/domains/` 디렉토리 생성
- LLM 도메인 이동 (기존 코드 리팩토링)

**Phase 2 (2주차):**
- OCR 도메인 신규 개발
- 자동 라우터 등록 구현

**Phase 3 (3주차):**
- Vision 도메인 추가
- 도메인별 의존성 분리

**Phase 4 (4주차):**
- 도메인별 테스트 작성
- CI/CD 파이프라인 업데이트