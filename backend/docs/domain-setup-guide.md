# 도메인별 개발 환경 설정 가이드

## 📌 개요

이 프로젝트는 팀별로 독립적인 도메인 개발이 가능하도록 구성되어 있습니다.
각 도메인(OCR, LLM, Vision 등)은 독립적인 의존성과 구조를 가지고 있습니다.

## 🔧 환경 설정 방법

### 1. 기본 환경 설치

모든 팀원이 공통으로 설치해야 하는 패키지:

```bash
# 기본 의존성 설치
pip install -r requirements/base.txt

# 개발 환경 도구 설치
pip install -r requirements/dev.txt
```

### 2. 도메인별 의존성 설치

각 팀은 자신의 도메인에 필요한 패키지만 추가로 설치:

#### LLM 팀
```bash
pip install -r requirements/domains/llm.txt
```

#### OCR 팀
```bash
pip install -r requirements/domains/ocr.txt
```

#### Vision 팀
```bash
pip install -r requirements/domains/vision.txt
```

#### 전체 설치 (운영 환경 또는 통합 테스트)
```bash
pip install -r requirements/base.txt
pip install -r requirements/domains/llm.txt
pip install -r requirements/domains/ocr.txt
pip install -r requirements/domains/vision.txt
pip install -r requirements/prod.txt
```

### 3. Poetry 사용 시 (권장)

```bash
# 기본 의존성 설치
poetry install

# LLM 도메인 추가
poetry install --with llm

# OCR 도메인 추가
poetry install --with ocr

# Vision 도메인 추가
poetry install --with vision

# 전체 설치
poetry install --with llm,ocr,vision,prod
```

## 📁 도메인별 파일 구조

각 도메인은 다음과 같은 표준 구조를 따릅니다:

```
app/domains/{domain_name}/
├── __init__.py
├── models/              # SQLAlchemy ORM 모델
├── schemas/             # Pydantic 스키마
│   ├── __init__.py
│   ├── request.py       # 요청 스키마
│   └── response.py      # 응답 스키마
├── services/            # 비즈니스 로직
│   ├── __init__.py
│   └── {domain}_model.py
├── tasks/               # Celery 태스크
│   ├── __init__.py
│   └── {domain}_tasks.py
├── controllers/         # FastAPI 라우터
│   ├── __init__.py
│   └── {domain}_controller.py
└── config/              # 도메인별 설정 (선택)
```

## 🚀 새 도메인 추가하기

### 1. 디렉토리 구조 생성

```bash
# 새 도메인 디렉토리 생성
mkdir -p app/domains/새도메인/{models,schemas,services,tasks,controllers,config}
```

### 2. 필수 파일 생성

#### `app/domains/새도메인/__init__.py`
```python
# app/domains/새도메인/__init__.py
"""
새도메인 도메인 모듈
"""
```

#### `app/domains/새도메인/schemas/__init__.py`
```python
from .request import 새도메인Request
from .response import 새도메인Response

__all__ = ["새도메인Request", "새도메인Response"]
```

#### `app/domains/새도메인/services/__init__.py`
```python
from .새도메인_model import 새도메인Model

__all__ = ["새도메인Model"]
```

#### `app/domains/새도메인/controllers/새도메인_controller.py`
```python
from fastapi import APIRouter
from app.utils.response_builder import ResponseBuilder

router = APIRouter(prefix="/새도메인", tags=["새도메인"])

@router.get("/")
async def get_info():
    return ResponseBuilder.success(
        data={"message": "새도메인 API"},
        message="새도메인 정보"
    )
```

### 3. 의존성 파일 생성

`requirements/domains/새도메인.txt` 파일 생성:
```txt
# requirements/domains/새도메인.txt
# 새도메인 전용 의존성

# 필요한 패키지 추가
your-package==1.0.0
```

### 4. 자동 라우터 등록

컨트롤러에 `router` 객체가 있으면 자동으로 등록됩니다.
`app/api/v1/router.py`가 모든 도메인을 자동 검색합니다.

## 🔍 개발 가이드

### Celery 태스크 작성

도메인별로 네임스페이스를 사용하여 태스크 이름 충돌 방지:

```python
# app/domains/ocr/tasks/ocr_tasks.py
from app.celery_app import celery_app

@celery_app.task(bind=True, name="ocr.extract_text")
def extract_text_task(self, image_path: str):
    # OCR 로직
    pass
```

### API 엔드포인트 작성

```python
# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter
from ..schemas import OCRRequest, OCRResponse
from ..tasks.ocr_tasks import extract_text_task

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/extract", response_model=ApiResponse[OCRResponse])
async def extract_text(request: OCRRequest):
    task = extract_text_task.delay(request.image_path)
    return ResponseBuilder.success(
        data={"task_id": task.id, "status": "PENDING"}
    )
```

### 공유 코드 활용

모든 AI 모델은 `app/shared/base_model.py`를 상속:

```python
from app.shared.base_model import BaseModel

class OCRModel(BaseModel):
    def load_model(self):
        # 모델 로딩 구현
        pass

    def predict(self, input_data):
        # 추론 구현
        pass
```

## 🧪 테스트 작성

도메인별 테스트 디렉토리:

```bash
tests/test_domains/test_ocr/
├── test_ocr_model.py
├── test_ocr_service.py
└── test_ocr_api.py
```

테스트 실행:
```bash
# 특정 도메인 테스트
pytest tests/test_domains/test_ocr/

# 전체 테스트
pytest
```

## 📝 커밋 컨벤션

도메인별 변경사항 커밋 시:

```bash
# LLM 도메인 수정
git commit -m "feat(llm): 새로운 GPT 모델 추가"

# OCR 도메인 수정
git commit -m "fix(ocr): PaddleOCR 인코딩 오류 수정"

# Vision 도메인 수정
git commit -m "refactor(vision): YOLO 모델 로딩 최적화"
```

## 🔄 팀별 작업 흐름

### 1. 브랜치 전략
```bash
# 도메인별 feature 브랜치 생성
git checkout -b feature/ocr-text-enhancement
git checkout -b feature/llm-chatbot
git checkout -b feature/vision-segmentation
```

### 2. 개발 및 테스트
```bash
# 자신의 도메인 의존성 설치
pip install -r requirements/domains/ocr.txt

# 개발 진행
# ...

# 테스트 실행
pytest tests/test_domains/test_ocr/
```

### 3. PR 생성
- PR 제목: `[OCR] 텍스트 추출 정확도 개선`
- 리뷰어: OCR 팀원 지정
- 라벨: `domain:ocr`

## 🚨 주의사항

1. **의존성 충돌 방지**
   - 공통 의존성(`requirements/base.txt`)은 전체 합의 후 수정
   - 도메인 전용 의존성만 자유롭게 추가

2. **네임스페이스 준수**
   - Celery 태스크: `{domain}.{task_name}`
   - API 경로: `/api/v1/{domain}/...`

3. **공유 코드 수정 시**
   - `app/shared/` 수정은 전체 팀 리뷰 필요
   - 하위 호환성 유지

4. **테스트 필수**
   - 모든 PR은 도메인 테스트 통과 필요
   - CI/CD 파이프라인에서 자동 검증

## 📚 추가 문서

- [아키텍처 개선 제안](./architecture-improvement.md)
- [API 컨벤션](./api-conventions.md) (향후 추가)
- [배포 가이드](./deployment-guide.md) (향후 추가)