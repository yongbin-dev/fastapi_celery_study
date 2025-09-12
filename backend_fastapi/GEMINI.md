**GEMINI.md**

### 프로젝트 개요

이 프로젝트는 FastAPI를 웹 프레임워크로, Celery를 비동기 작업 처리용으로 사용하는 백엔드 서비스입니다. PostgreSQL 데이터베이스와 SQLAlchemy ORM을 사용하여 데이터 지속성을 관리하며, Redis를 메시지 브로커로 활용합니다. Docker Compose를 통해 개발 환경을 쉽게 구축하고 실행할 수 있도록 컨테이너화되어 있습니다.

**주요 기술 스택:**

*   **언어**: Python 3.12+
*   **웹 프레임워크**: FastAPI
*   **비동기 작업**: Celery
*   **데이터베이스**: PostgreSQL
*   **ORM**: SQLAlchemy
*   **메시지 브로커**: Redis
*   **서버**: Uvicorn
*   **의존성 관리**: Poetry
*   **컨테이너**: Docker

### 빌드 및 실행

프로젝트를 빌드하고 실행하기 위한 주요 명령어는 다음과 같습니다.

1.  **환경 변수 설정**:
    개발 환경 설정을 위해 `.env.development` 파일을 복사하여 `.env` 파일을 생성합니다.
    ```bash
    cp .env.development .env
    ```

2.  **의존성 설치**:
    Poetry를 사용하여 Python 의존성을 설치합니다.
    ```bash
    poetry install
    ```

3.  **Docker 서비스 실행**:
    PostgreSQL 데이터베이스와 Redis를 Docker Compose로 실행합니다.
    ```bash
    docker-compose up -d
    ```

4.  **데이터베이스 마이그레이션**:
    Alembic을 사용하여 데이터베이스 스키마를 최신 상태로 업데이트합니다.
    ```bash
    poetry run alembic upgrade head
    ```

5.  **애플리케이션 실행**:
    FastAPI 서버와 Celery 워커를 각각 실행합니다.

    *   **FastAPI 서버 실행**:
        ```bash
        poetry run uvicorn run:app --reload --host 0.0.0.0 --port 8000
        ```
    *   **Celery 워커 실행**:
        ```bash
        poetry run celery -A celery_worker.worker worker --loglevel=info
        ```

### 테스트

`pytest`를 사용하여 프로젝트의 테스트를 실행할 수 있습니다.

```bash
poetry run pytest
```

### 개발 컨벤션

*   **의존성 관리**: Poetry를 사용하여 프로젝트 의존성을 관리합니다. 새로운 패키지를 추가하거나 기존 패키지를 업데이트할 때는 `poetry add` 또는 `poetry update` 명령어를 사용합니다.
*   **테스트**: `pytest` 프레임워크를 사용하여 단위 및 통합 테스트를 작성하고 실행합니다.
*   **환경 설정**: `.env` 파일을 통해 개발, 스테이징, 운영 환경별 설정을 분리하여 관리합니다.
*   **데이터베이스 마이그레이션**: Alembic을 사용하여 데이터베이스 스키마 변경 이력을 관리하고 적용합니다.

---

### 주요 디렉토리 구조 

```
/Users/aipim/yb/python/fastapi_celery_study/backend_fastapi/
├───app/              # 애플리케이션 소스 코드
│   ├───api/          # API 엔드포인트 라우터
│   │   └───v1/
│   │       └───endpoints/
│   ├───core/         # 핵심 설정 (FastAPI 앱, Celery, DB 등)
│   ├───exceptions/   # 사용자 정의 예외
│   ├───handlers/     # 예외 핸들러
│   ├───middleware/   # 미들웨어
│   ├───models/       # SQLAlchemy 모델
│   ├───schemas/      # Pydantic 스키마
│   ├───services/     # 비즈니스 로직
│   │   └───ai/
│   └───utils/        # 유틸리티 함수
├───docs/             # 프로젝트 문서
├───infra/            # 인프라 관련 설정 (Docker, Prometheus 등)
│   └───prometheus/
├───migrations/       # 데이터베이스 마이그레이션 스크립트
│   └───versions/
├───tests/            # 테스트 코드
```