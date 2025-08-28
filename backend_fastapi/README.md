# FastAPI & Celery 프로젝트

이 프로젝트는 FastAPI를 웹 프레임워크로, Celery를 비동기 작업 처리용으로 사용하는 백엔드 서비스입니다. SQLAlchemy를 통해 데이터베이스와 상호작용하며, Docker를 통해 개발 환경을 쉽게 구성할 수 있습니다.

## ✨ 주요 기능

- **FastAPI 기반 API**: 현대적이고 빠른 웹 API 프레임워크 사용
- **Celery 비동기 작업**: Redis를 메시지 브로커로 사용하여 오래 걸리는 작업을 백그라운드에서 처리
- **SQLAlchemy ORM**: PostgreSQL 데이터베이스와의 효율적인 통신
- **Alembic 데이터베이스 마이그레이션**: 데이터베이스 스키마 변경 관리
- **Docker Compose**: 개발에 필요한 서비스(앱, DB, Redis)를 컨테이너화하여 원클릭으로 실행
- **다중 환경 설정**: `.env` 파일을 통해 개발, 스테이징, 운영 환경 분리

## 🛠️ 기술 스택

- **언어**: Python 3.12+
- **웹 프레임워크**: FastAPI
- **비동기 작업**: Celery
- **데이터베이스**: PostgreSQL
- **ORM**: SQLAlchemy
- **메시지 브로커**: Redis
- **서버**: Uvicorn
- **의존성 관리**: Poetry
- **컨테이너**: Docker

## 🚀 시작하기

### 1. 환경 변수 설정

프로젝트 루트의 `.env.development` 파일을 복사하여 `.env` 파일을 생성합니다. 이 파일은 개발 환경의 기본 설정값들을 담고 있습니다.

```bash
cp .env.development .env
```

### 2. 의존성 설치

Poetry를 사용하여 Python 의존성을 설치합니다.

```bash
poetry install
```

### 3. Docker 서비스 실행

개발에 필요한 PostgreSQL 데이터베이스와 Redis를 Docker Compose로 실행합니다.

```bash
docker-compose up -d
```

### 4. 데이터베이스 마이그레이션

Alembic을 사용하여 데이터베이스 스키마를 최신 상태로 업데이트합니다.

```bash
poetry run alembic upgrade head
```

### 5. 애플리케이션 실행

Uvicorn 서버와 Celery 워커를 각각 실행합니다.

**FastAPI 서버 실행:**
```bash
poetry run uvicorn run:app --reload --host 0.0.0.0 --port 8000
```

**Celery 워커 실행:**
```bash
poetry run celery -A celery_worker.worker worker --loglevel=info
```

이제 `http://localhost:8000`에서 API 서버에 접근할 수 있습니다.

## ✅ 테스트

`pytest`를 사용하여 프로젝트의 테스트를 실행할 수 있습니다.

```bash
poetry run pytest
```

## 📁 프로젝트 구조

```
.
├── alembic/              # 데이터베이스 마이그레이션 스크립트
├── app/                  # 애플리케이션 소스 코드
│   ├── api/              # API 엔드포인트 라우터
│   ├── core/             # 핵심 설정 (FastAPI 앱, Celery, DB 등)
│   ├── models/           # SQLAlchemy 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── services/         # 비즈니스 로직
│   └── ...
├── celery_worker.py      # Celery 워커 진입점
├── docker-compose.yml    # Docker 서비스 정의
├── pyproject.toml        # Poetry 의존성 및 프로젝트 설정
└── run.py                # 애플리케이션 실행 스크립트
```