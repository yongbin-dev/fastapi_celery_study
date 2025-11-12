# BentoML 적용 가이드

## 개요

이 문서는 기존 gRPC 기반 ML 서버에 BentoML을 적용하는 방법을 설명합니다.

### 아키텍처

**하이브리드 방식**: 기존 gRPC 서버와 BentoML HTTP API를 병행하여 제공

```
┌─────────────────────────────────────────┐
│         ML Server Architecture          │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌──────────────┐   │
│  │   gRPC      │    │  BentoML     │   │
│  │   Server    │    │  HTTP API    │   │
│  │  (port:     │    │  (port:      │   │
│  │   50051)    │    │   3000)      │   │
│  └──────┬──────┘    └──────┬───────┘   │
│         │                  │           │
│         └────────┬─────────┘           │
│                  │                     │
│         ┌────────▼─────────┐           │
│         │  OCR Engine      │           │
│         │  Factory         │           │
│         │  - EasyOCR       │           │
│         │  - PaddleOCR     │           │
│         │  - Mock          │           │
│         └──────────────────┘           │
│                                         │
└─────────────────────────────────────────┘
```

### 장점

1. **유연성**: gRPC와 HTTP 두 가지 인터페이스 모두 지원
2. **점진적 마이그레이션**: 기존 gRPC 클라이언트와의 호환성 유지
3. **모델 관리**: BentoML의 강력한 모델 관리 기능 활용
4. **배포 간소화**: BentoML의 컨테이너화 및 배포 도구 활용
5. **모니터링**: BentoML의 내장 모니터링 및 로깅 기능

---

## 1. 프로젝트 구조

```
packages/ml_server/
├── ml_app/
│   ├── bentoml_services/         # 새로 추가
│   │   ├── __init__.py
│   │   └── ocr_service.py        # BentoML 서비스 정의
│   ├── grpc_services/            # 기존 gRPC 서비스
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   └── server.py
│   ├── engines/                  # 공통 OCR 엔진
│   │   └── ocr/
│   │       ├── base.py
│   │       ├── easyocr_engine.py
│   │       ├── paddleocr_engine.py
│   │       └── OCREngineFactory.py
│   └── models/
│       └── ocr_model.py
├── bentofile.yaml                # 새로 추가
├── requirements-bentoml.txt      # 새로 추가
├── Dockerfile.bentoml            # 새로 추가
├── Dockerfile.gpu                # 기존 gRPC용
└── pyproject.toml                # 업데이트됨
```

---

## 2. 설정 파일

### 2.1 pyproject.toml

BentoML 의존성이 추가되었습니다:

```toml
dependencies = [
    # ... 기존 의존성
    "bentoml>=1.3.0",  # BentoML 모델 서빙
]
```

### 2.2 bentofile.yaml

BentoML 빌드 설정:

```yaml
service: "ml_app.bentoml_services:OCRBentoService"
name: ocr-service
description: "OCR 텍스트 추출 서비스 (BentoML + gRPC 하이브리드)"

python:
  requirements_txt: ./requirements-bentoml.txt
  lock_packages: true

docker:
  distro: debian
  python_version: "3.12"
  system_packages:
    - libgl1-mesa-glx
    - libglib2.0-0
    - git
```

### 2.3 requirements-bentoml.txt

BentoML 서비스에 필요한 의존성:

```txt
bentoml>=1.3.0
fastapi>=0.115.6
uvicorn[standard]>=0.37.0
pydantic>=2.10.4

# OCR 엔진
paddleocr>=2.8.0,<3.0.0
paddlepaddle>=2.6.2,<3.0.0
easyocr>=1.7.2

# ML 라이브러리
torch>=2.2.0
torchvision>=0.17.0
numpy<2.0.0
```

---

## 3. BentoML 서비스 구현

### 3.1 OCR 서비스 (ml_app/bentoml_services/ocr_service.py)

```python
import bentoml
from PIL import Image

@bentoml.service(
    name="ocr_service",
    resources={"cpu": "2", "memory": "4Gi"},
)
class OCRBentoService:
    """BentoML OCR 서비스"""

    def __init__(self):
        from shared.config import settings
        self.engine_type = settings.OCR_ENGINE

    @bentoml.api
    async def extract_text(
        self,
        image: Image.Image,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ) -> OCRResponse:
        """단일 이미지에서 텍스트 추출"""
        # OCR 모델 실행
        model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)
        result = model.predict(image_data, confidence_threshold=confidence_threshold)

        return OCRResponse(...)

    @bentoml.api
    async def extract_text_batch(
        self,
        images: List[Image.Image],
        ...
    ) -> BatchOCRResponse:
        """배치 이미지 OCR 처리"""
        # 배치 처리 로직
        ...

    @bentoml.api
    async def health_check(self) -> Dict[str, any]:
        """헬스 체크"""
        ...
```

---

## 4. 사용 방법

### 4.1 로컬 개발

#### 의존성 설치

```bash
# 루트 디렉토리에서
uv sync

# 또는 ml_server 패키지만 설치
cd packages/ml_server
uv pip install -e ".[ocr-cpu]"
```

#### BentoML 서비스 실행

```bash
# packages/ml_server 디렉토리에서
bentoml serve ml_app.bentoml_services:OCRBentoService

# 또는 포트 지정
bentoml serve ml_app.bentoml_services:OCRBentoService \
  --host 0.0.0.0 \
  --port 3000 \
  --workers 2
```

#### API 테스트

서비스가 실행되면 자동으로 Swagger UI가 제공됩니다:

- Swagger UI: http://localhost:3000
- OpenAPI 스펙: http://localhost:3000/openapi.json

**cURL 예시**:

```bash
# 단일 이미지 OCR
curl -X POST "http://localhost:3000/extract_text" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_image.jpg" \
  -F "language=korean" \
  -F "confidence_threshold=0.5"

# 헬스 체크
curl "http://localhost:3000/health_check"
```

**Python 클라이언트 예시**:

```python
import requests
from PIL import Image

# 이미지 로드
image = Image.open("test_image.jpg")

# API 호출
response = requests.post(
    "http://localhost:3000/extract_text",
    files={"image": open("test_image.jpg", "rb")},
    data={
        "language": "korean",
        "confidence_threshold": 0.5,
        "use_angle_cls": True,
    }
)

result = response.json()
print(f"추출된 텍스트: {result['text']}")
print(f"신뢰도: {result['overall_confidence']}")
```

### 4.2 BentoML Bento 빌드

Bento는 BentoML의 배포 단위입니다:

```bash
cd packages/ml_server

# Bento 빌드
bentoml build

# 빌드된 Bento 목록 확인
bentoml list

# 특정 Bento 정보 확인
bentoml get ocr-service:latest
```

빌드 결과:

```
Successfully built Bento(tag="ocr-service:xyz123abc")

To containerize the Bento:
$ bentoml containerize ocr-service:xyz123abc

To push to BentoCloud:
$ bentoml push ocr-service:xyz123abc
```

### 4.3 컨테이너화

#### 방법 1: BentoML 자동 컨테이너화 (권장)

```bash
# Bento를 Docker 이미지로 빌드
bentoml containerize ocr-service:latest

# 생성된 이미지 확인
docker images | grep ocr-service

# 실행
docker run -p 3000:3000 ocr-service:latest
```

#### 방법 2: 커스텀 Dockerfile 사용

```bash
# 루트 디렉토리에서
docker build -f packages/ml_server/Dockerfile.bentoml -t bentoml_server:latest .

# 실행
docker run -p 3000:3000 bentoml_server:latest
```

### 4.4 Docker Compose 사용

기존 docker-compose.yml에 bentoml_server 서비스가 추가되었습니다:

```bash
# BentoML 서버만 실행
docker-compose up bentoml_server

# 전체 스택 실행 (gRPC + BentoML)
docker-compose up

# 백그라운드 실행
docker-compose up -d
```

서비스 접속:

- gRPC 서버: `localhost:50051`
- BentoML HTTP API: `http://localhost:3000`
- Swagger UI: `http://localhost:3000`

---

## 5. API 엔드포인트

BentoML 서비스는 자동으로 다음 엔드포인트를 생성합니다:

### 5.1 OCR 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/extract_text` | 단일 이미지 OCR |
| POST | `/extract_text_batch` | 배치 이미지 OCR |
| GET | `/health_check` | 헬스 체크 |

### 5.2 BentoML 기본 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/` | 서비스 정보 |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | OpenAPI 스펙 |
| GET | `/healthz` | Kubernetes 헬스 체크 |
| GET | `/readyz` | Kubernetes Readiness 체크 |
| GET | `/livez` | Kubernetes Liveness 체크 |
| GET | `/metrics` | Prometheus 메트릭 |

---

## 6. 프로덕션 배포

### 6.1 성능 튜닝

**bentofile.yaml 리소스 설정**:

```yaml
@bentoml.service(
    name="ocr_service",
    resources={
        "cpu": "4",           # CPU 코어 수
        "memory": "8Gi",      # 메모리
        "gpu": 1,            # GPU 개수 (선택사항)
    },
    workers=4,               # 워커 프로세스 수
)
```

**실행 시 설정**:

```bash
bentoml serve ml_app.bentoml_services:OCRBentoService \
  --host 0.0.0.0 \
  --port 3000 \
  --workers 4 \
  --timeout 300 \
  --backlog 2048
```

### 6.2 GPU 사용

**bentofile.yaml 업데이트**:

```yaml
docker:
  cuda_version: "12.1"

# requirements-bentoml.txt에서 GPU 버전 사용
# paddlepaddle-gpu>=2.6.2,<3.0.0
```

**Docker Compose에서 GPU 활성화**:

```yaml
bentoml_server:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### 6.3 Kubernetes 배포

BentoML은 자동으로 Kubernetes 매니페스트를 생성합니다:

```bash
# Bento를 BentoCloud에 푸시
bentoml push ocr-service:latest

# 또는 직접 Kubernetes 배포
bentoml deploy ocr-service:latest -n ocr-service-prod

# Kubernetes YAML 생성
bentoml generate kubernetes ocr-service:latest > ocr-deployment.yaml

# 배포
kubectl apply -f ocr-deployment.yaml
```

---

## 7. 모니터링 및 로깅

### 7.1 Prometheus 메트릭

BentoML은 자동으로 Prometheus 메트릭을 제공합니다:

```bash
curl http://localhost:3000/metrics
```

주요 메트릭:

- `bentoml_service_request_total`: 총 요청 수
- `bentoml_service_request_duration_seconds`: 요청 처리 시간
- `bentoml_service_request_in_progress`: 진행 중인 요청 수

### 7.2 로깅

BentoML은 구조화된 로그를 제공합니다:

```python
from shared.core.logging import get_logger

logger = get_logger(__name__)

@bentoml.api
async def extract_text(...):
    logger.info(f"OCR 요청: size={image.size}")
    # ...
    logger.info(f"OCR 완료: {len(result.text_boxes)} 텍스트 박스")
```

---

## 8. 기존 gRPC와 비교

| 특징 | gRPC | BentoML HTTP |
|------|------|--------------|
| 프로토콜 | gRPC (HTTP/2) | HTTP/1.1, HTTP/2 |
| 성능 | 높음 (바이너리) | 중간 (JSON) |
| 브라우저 지원 | 제한적 | 완전 지원 |
| 개발 편의성 | Proto 정의 필요 | 자동 생성 |
| Swagger UI | 별도 도구 필요 | 자동 제공 |
| 모니터링 | 직접 구현 | 내장 |
| 배포 | 직접 구성 | 자동화 도구 |

### 언제 어떤 것을 사용할까?

**gRPC 사용 권장**:

- 마이크로서비스 간 통신
- 높은 성능이 필요한 경우
- 스트리밍이 필요한 경우

**BentoML HTTP 사용 권장**:

- 외부 API 제공
- 웹 애플리케이션 통합
- 빠른 프로토타이핑
- 모니터링 및 관리가 중요한 경우

---

## 9. 트러블슈팅

### 9.1 메모리 부족

```bash
# 워커 수 줄이기
bentoml serve ... --workers 1

# 배치 크기 줄이기 (코드에서 설정)
```

### 9.2 GPU 인식 안 됨

```bash
# NVIDIA 드라이버 확인
nvidia-smi

# Docker에서 GPU 접근 확인
docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi
```

### 9.3 모델 로딩 느림

```python
# 모델 초기화 시 한 번만 로드
@bentoml.service
class OCRBentoService:
    def __init__(self):
        # 초기화 시 모델 로드
        self.model = get_ocr_model()
```

### 9.4 포트 충돌

```bash
# 다른 포트 사용
bentoml serve ... --port 3001
```

---

## 10. 추가 리소스

- [BentoML 공식 문서](https://docs.bentoml.org/)
- [BentoML GitHub](https://github.com/bentoml/BentoML)
- [BentoML 예제](https://github.com/bentoml/BentoML/tree/main/examples)

---

## 11. 다음 단계

1. **성능 벤치마크**: gRPC vs BentoML HTTP 성능 비교
2. **모델 버저닝**: BentoML Model Store 활용
3. **A/B 테스팅**: 여러 모델 버전 동시 배포
4. **자동 스케일링**: Kubernetes HPA 설정
5. **CI/CD 통합**: GitHub Actions로 자동 배포

---

**작성일**: 2025-11-12
**버전**: 1.0.0
**작성자**: AI Assistant
