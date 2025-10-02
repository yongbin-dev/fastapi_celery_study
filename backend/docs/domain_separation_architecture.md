# 도메인 기반 서비스 분리 아키텍처 설명

## 1. 개요

이 문서는 기존의 단일 서비스(모놀리식) Docker 컨테이너 구조에서, 각 AI 도메인(`LLM`, `OCR` 등)이 독립적인 서비스로 실행될 수 있도록 전환한 아키텍처의 작동 원리를 설명합니다.

**목표**: 각 서비스가 필요한 자원만 사용하도록 경량화하고, 도메인별로 독립적인 배포, 확장, 관리가 가능하도록 하여 개발 및 운영 효율성을 극대화하는 것입니다.

---

## 2. 핵심 구성 요소

도메인 분리는 4가지 핵심 요소의 유기적인 상호작용을 통해 이루어집니다.

### 1) `pyproject.toml` : 의존성 분리의 시작

- **역할**: 각 도메인이 필요로 하는 Python 라이브러리를 그룹화하여 정의합니다.
- **설정**: `[project.optional-dependencies]` 섹션에 `llm`, `ocr` 등 도메인별 의존성 그룹을 만듭니다.

```toml
[project.optional-dependencies]
llm = [
    "torch>=2.2.0",
    "transformers>=4.40.0",
    # ...
]

ocr = [
    "paddleocr>=2.8.0,<3.0.0",
    "paddlepaddle-gpu>=2.6.2,<3.0.0",
    # ...
]
```

- **원리**: 이 설정을 통해 `uv sync --extra llm` 같은 명령어로 특정 도메인에 필요한 라이브러리만 선택적으로 설치할 수 있는 기반을 마련합니다.

### 2) `Dockerfile` : 동적 빌드를 통한 맞춤형 이미지 생성

- **역할**: Docker 이미지를 빌드할 때, 어떤 도메인의 의존성을 설치할지 외부에서 주입받아 맞춤형 이미지를 생성합니다.
- **설정**:
  - `ARG DOMAIN_EXTRA=prod`: 빌드 시점에 외부에서 값을 받을 수 있는 `ARG` 변수를 선언합니다. (기본값: `prod`)
  - `RUN uv sync --no-cache --extra ${DOMAIN_EXTRA}`: `uv sync` 명령어가 `ARG`로 받은 값을 사용하여 해당 도메인의 의존성을 설치합니다.

- **원리**: 동일한 `Dockerfile` 하나를 가지고 `docker build --build-arg DOMAIN_EXTRA=llm` 과 같이 빌드 인수를 다르게 전달함으로써, 내부에 설치된 라이브러리가 다른 여러 종류의 이미지를 생성할 수 있습니다.

### 3) `docker-compose.domains.yml` : 서비스 정의 및 환경 주입

- **역할**: 각 도메인을 실제 컨테이너 서비스로 정의하고, 빌드 및 실행 시 필요한 환경을 구성합니다.
- **설정**:

```yaml
services:
  app-llm:
    build:
      context: .
      dockerfile: Dockerfile.gpu
      args:
        - DOMAIN_EXTRA=llm  # 1. Dockerfile에 빌드 인수를 전달
    ports:
      - "35051:5050"
    environment:
      - DOMAIN=llm          # 2. 컨테이너 내부에 런타임 환경 변수를 주입
```

- **원리**:
  1.  **빌드 시점**: `build.args`를 통해 `Dockerfile`의 `DOMAIN_EXTRA`에 `llm` 값을 전달하여 **LLM 전용 이미지**를 빌드합니다.
  2.  **실행 시점**: `environment`를 통해 컨테이너 내부에 `DOMAIN=llm`이라는 **환경 변수**를 설정합니다. 이 변수는 애플리케이션이 자신의 "역할"을 인지하는 데 사용됩니다.

### 4) `app/core/router.py` : 동적 라우팅을 통한 기능 분기

- **역할**: FastAPI 애플리케이션이 시작될 때, 컨테이너의 환경 변수를 읽어 현재 도메인에 맞는 API 라우터(엔드포인트)만 동적으로 활성화합니다.
- **설정**:

```python
import os

# 컨테이너의 환경 변수를 읽음
current_domain = os.getenv("DOMAIN", "base")
allowed_domains = {"base", current_domain}

# app/domains 폴더를 순회하며...
for _, domain_name, _ in pkgutil.iter_modules(app.domains.__path__):
    # 허용된 도메인일 경우에만 라우터를 로드
    if domain_name in allowed_domains:
        # ... import_module 및 app.include_router 로직 ...
```

- **원리**: `app-llm` 컨테이너는 `DOMAIN=llm` 환경 변수를 가지고 시작되므로, 위 코드는 `allowed_domains`를 `{"base", "llm"}`으로 설정합니다. 결과적으로 `common`, `llm` 도메인의 API는 활성화되지만, `ocr` 도메인의 API는 로드조차 되지 않아 완벽한 기능 분리가 이루어집니다.

---

## 3. 전체 동작 흐름 (예: `app-llm`)

1.  **명령 실행**: 사용자가 `docker-compose -f docker-compose.domains.yml up app-llm` 명령을 실행합니다.
2.  **서비스 정의 확인**: Docker Compose는 `app-llm` 서비스의 정의를 읽습니다.
3.  **이미지 빌드**: `build.args`의 `DOMAIN_EXTRA=llm` 값을 `Dockerfile`에 전달하여 이미지를 빌드합니다. `uv sync --extra llm`이 실행되어 `llm` 관련 라이브러리만 설치됩니다.
4.  **컨테이너 생성 및 실행**: 빌드된 이미지로 컨테이너를 생성하며, 내부에 `DOMAIN=llm` 환경 변수를 설정합니다.
5.  **애플리케이션 시작**: FastAPI 앱이 실행되면서 `app/core/router.py`가 로드됩니다.
6.  **라우터 동적 로드**: `router.py`는 `DOMAIN=llm` 값을 읽어 `llm`과 `base` 도메인에 해당하는 컨트롤러(API 엔드포인트)만 메모리에 로드하고 활성화합니다.
7.  **서비스 시작 완료**: 최종적으로 `app-llm` 컨테이너는 LLM 관련 기능만 수행하는 경량화된 상태로 서비스 요청을 대기하게 됩니다.

---

## 4. 기대 효과

- **자원 효율성**: 각 서비스는 필요한 라이브러리만 포함하므로 이미지 크기가 작고 메모리 사용량이 적습니다.
- **독립적인 확장/배포**: 특정 도메인(예: OCR)에 트래픽이 몰릴 경우, 해당 서비스만 독립적으로 확장(Scale-out)할 수 있습니다.
- **안정성 및 격리**: 한 도메인의 오류가 다른 도메인 서비스에 영향을 주지 않아 전체 시스템의 안정성이 향상됩니다.
- **명확한 소유권**: 도메인별로 코드와 실행 환경이 분리되어 팀별 책임과 소유권이 명확해집니다.
