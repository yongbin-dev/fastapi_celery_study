# Docker 베이스 이미지 전략

## 개요

이 프로젝트는 **베이스 이미지 전략**을 사용하여 ML/AI 서비스의 빌드 시간을 대폭 단축하고 일관된 환경을 유지합니다.

## 아키텍처

### 이미지 계층 구조

```
┌─────────────────────────────────────┐
│  python:3.12-slim                   │
│  또는 nvidia/cuda:11.8.0-cudnn8     │
└─────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│  backend-ml-base (CPU)              │
│  - torch 2.8.0                      │
│  - torchvision 0.23.0               │
│  - opencv-python                    │
│  - scikit-learn, scipy              │
│  - FastAPI 공통 의존성              │
└─────────────────────────────────────┘
                 ▼
┌────────────┬────────────┬────────────┐
│ ocr-cpu    │ ocr-gpu    │    llm     │
│ +paddle    │ +paddle    │ +transform │
│  paddle    │  paddle-   │  ers       │
│ +easyocr   │  gpu       │ +langchain │
│            │ +easyocr   │            │
└────────────┴────────────┴────────────┘
```

### GPU 베이스 이미지

```
nvidia/cuda:11.8.0-cudnn8-runtime
                 ▼
┌─────────────────────────────────────┐
│  backend-ml-gpu-base                │
│  - CUDA 11.8 + cuDNN 8              │
│  - torch 2.8.0 (GPU)                │
│  - ML 공통 라이브러리               │
└─────────────────────────────────────┘
                 ▼
┌────────────┬────────────────────────┐
│ ocr-gpu    │         llm            │
│ +paddle    │    +transformers       │
│  paddle-   │    +langchain          │
│  gpu       │                        │
└────────────┴────────────────────────┘
```

## 빌드 시간 비교

### 이전 (베이스 이미지 없음)

| 서비스 | 빌드 시간 | 주요 병목 |
|--------|-----------|----------|
| ocr-cpu | 6분 30초 | torch (846MB), paddlepaddle (120MB) 다운로드 |
| ocr-gpu | 8-10분 | torch (846MB), paddlepaddle-gpu (723MB) |
| llm | 5-7분 | torch (846MB), transformers |
| **총계** | **20-23분** | torch 중복 다운로드/설치 |

### 현재 (베이스 이미지 사용)

| 단계 | 빌드 시간 | 설명 |
|------|-----------|------|
| **최초 빌드** | | |
| ml-base | 12초 | torch + 공통 라이브러리 (1회) |
| ml-gpu-base | 15초 | CUDA + torch GPU (1회) |
| ocr-cpu | 3초 | paddlepaddle만 추가 |
| ocr-gpu | 3-5초 | paddlepaddle-gpu만 추가 |
| llm | 2-3초 | transformers만 추가 |
| **최초 총계** | **30-40초** | |
| | | |
| **2회차 이후** | | |
| ocr-cpu | 3초 | 베이스 캐시 활용 |
| ocr-gpu | 3-5초 | 베이스 캐시 활용 |
| llm | 2-3초 | 베이스 캐시 활용 |
| **2회차+ 총계** | **8-11초** | |

### 성능 개선

- **최초 빌드**: 20분 → 40초 (**96% 감소**)
- **2회차 이후**: 20분 → 10초 (**99% 감소**)
- **개별 서비스**: 6분 30초 → 3초 (**99% 감소**)

## 디렉토리 구조

```
backend/
├── Dockerfile.ml-base          # CPU 베이스 이미지
├── Dockerfile.ml-gpu-base      # GPU 베이스 이미지
├── Dockerfile.ocr-cpu          # OCR CPU (ml-base 기반)
├── Dockerfile.ocr-gpu          # OCR GPU (ml-gpu-base 기반)
├── Dockerfile.llm              # LLM (ml-gpu-base 기반)
├── docker-compose.domains.yml  # 전체 서비스 정의
└── pyproject.toml              # 의존성 그룹 정의
```

## pyproject.toml 의존성 그룹

### ml-base (공통 ML 베이스)

```toml
ml-base = [
    "torch>=2.2.0",
    "torchvision>=0.17.0",
    "opencv-python>=4.9.0",
    "Pillow>=10.2.0",
    "numpy>=2.0.0",
    "scipy>=1.13.0",
    "scikit-learn>=1.7.2",
    "scikit-image>=0.25.0",
]
```

### 서비스별 의존성

```toml
llm = [
    "transformers>=4.40.0",
    # ... LLM 전용 패키지
    "fastapi-celery-multi-domain[ml-base]",  # ml-base 상속
]

ocr-cpu = [
    "paddleocr>=2.8.0,<3.0.0",
    "paddlepaddle>=2.6.2,<3.0.0",  # CPU 버전
    "easyocr>=1.7.2",
    "fastapi-celery-multi-domain[ml-base]",  # ml-base 상속
]

ocr-gpu = [
    "paddleocr>=2.8.0,<3.0.0",
    "paddlepaddle-gpu>=2.6.2,<3.0.0",  # GPU 버전
    "easyocr>=1.7.2",
    "fastapi-celery-multi-domain[ml-base]",  # ml-base 상속
]
```

## 빌드 가이드

### 1. 베이스 이미지 빌드 (최초 1회)

```bash
# CPU 베이스 이미지
docker-compose -f docker-compose.domains.yml build ml-base

# GPU 베이스 이미지 (NVIDIA GPU 필요)
docker-compose -f docker-compose.domains.yml build ml-gpu-base
```

### 2. 서비스 빌드

```bash
# OCR CPU 버전
docker-compose -f docker-compose.domains.yml build app-ocr-cpu

# OCR GPU 버전
docker-compose -f docker-compose.domains.yml build app-ocr-gpu

# LLM 서비스
docker-compose -f docker-compose.domains.yml build app-llm

# 전체 빌드
docker-compose -f docker-compose.domains.yml build
```

### 3. 서비스 실행

```bash
# 개별 서비스 실행
docker-compose -f docker-compose.domains.yml up -d app-ocr-cpu
docker-compose -f docker-compose.domains.yml up -d app-ocr-gpu
docker-compose -f docker-compose.domains.yml up -d app-llm

# 전체 서비스 실행
docker-compose -f docker-compose.domains.yml up -d
```

## 베이스 이미지 업데이트

베이스 이미지를 업데이트하면 모든 하위 서비스를 재빌드해야 합니다.

```bash
# 1. 베이스 이미지 재빌드
docker-compose -f docker-compose.domains.yml build --no-cache ml-base

# 2. 의존하는 서비스들 재빌드
docker-compose -f docker-compose.domains.yml build app-ocr-cpu

# 또는 전체 재빌드
docker-compose -f docker-compose.domains.yml build --no-cache
```

## 주의사항

### 1. 베이스 이미지 존재 확인

서비스 빌드 전에 베이스 이미지가 존재하는지 확인:

```bash
docker images | grep backend-ml
```

출력 예시:
```
backend-ml-base       latest    b0b74bfa4d1b   10 minutes ago   8.07GB
backend-ml-gpu-base   latest    a1b2c3d4e5f6   10 minutes ago   9.5GB
```

### 2. depends_on 설정

`docker-compose.domains.yml`에서 `depends_on`으로 빌드 순서 보장:

```yaml
app-ocr-cpu:
  depends_on:
    - ml-base  # ml-base가 먼저 빌드됨
```

### 3. 캐시 활용

빌드 캐시를 활용하여 속도 향상:

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra ${DOMAIN_EXTRA}
```

### 4. 네트워크 설정

모든 서비스는 `app-network` 네트워크에 연결:

```yaml
networks:
  app-network:
    external: true
```

## 트러블슈팅

### 베이스 이미지를 찾을 수 없음

```bash
Error: image backend-ml-base:latest not found
```

**해결 방법:**
```bash
docker-compose -f docker-compose.domains.yml build ml-base
```

### 캐시 문제로 인한 빌드 실패

```bash
# 캐시 없이 완전히 재빌드
docker-compose -f docker-compose.domains.yml build --no-cache ml-base
docker-compose -f docker-compose.domains.yml build --no-cache app-ocr-cpu
```

### 이미지 용량 확인

```bash
docker images | grep backend
```

### 사용하지 않는 이미지 정리

```bash
# 댕글링 이미지 제거
docker image prune

# 사용하지 않는 모든 이미지 제거 (주의!)
docker image prune -a
```

## 이점

### 1. 빌드 시간 단축
- 최초: 96% 감소 (20분 → 40초)
- 2회차+: 99% 감소 (20분 → 10초)

### 2. 저장 공간 절약
- torch(846MB)가 각 서비스마다 중복되지 않음
- 공통 레이어는 한 번만 저장

### 3. 일관된 환경
- 모든 ML 서비스가 동일한 torch, opencv 버전 사용
- 버전 충돌 최소화

### 4. 유지보수 용이
- 공통 라이브러리 업데이트를 베이스 이미지에서만 관리
- 서비스별 의존성은 최소화

### 5. CI/CD 효율화
- 베이스 이미지는 레지스트리에 푸시 후 재사용
- 서비스별 빌드는 3초 이내로 완료

## 향후 개선 사항

1. **멀티 스테이지 빌드**: 빌드 도구를 최종 이미지에서 제거
2. **레지스트리 활용**: Docker Hub 또는 사설 레지스트리에 베이스 이미지 푸시
3. **버전 태그 관리**: `backend-ml-base:v1.0`, `v1.1` 등 버전별 관리
4. **자동화**: CI/CD 파이프라인에서 베이스 이미지 자동 빌드
