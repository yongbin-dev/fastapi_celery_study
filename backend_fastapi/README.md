# FastAPI & Celery 백엔드 프로젝트

이 프로젝트는 FastAPI를 웹 프레임워크로, Celery를 비동기 작업 처리용으로 사용하는 백엔드 서비스입니다. SQLAlchemy를 통해 데이터베이스와 상호작용하며, Docker를 통해 개발 환경을 쉽게 구성할 수 있습니다.

## ✨ 주요 기능

- **FastAPI 기반 API**: 현대적이고 빠른 웹 API 프레임워크 사용
- **Celery 비동기 작업**: Redis를 메시지 브로커로 사용하여 오래 걸리는 작업을 백그라운드에서 처리
- **SQLAlchemy ORM**: PostgreSQL 데이터베이스와의 효율적인 통신
- **Alembic 데이터베이스 마이그레이션**: 데이터베이스 스키마 변경 관리
- **Docker Compose**: 개발에 필요한 서비스(PostgreSQL, Redis)를 컨테이너화하여 실행
- **환경 변수 기반 설정**: `.env` 파일을 통해 주요 설정 관리

## 🛠️ 기술 스택

- **언어**: Python 3.12+
- **웹 프레임워크**: FastAPI
- **비동기 작업**: Celery
- **데이터베이스**: PostgreSQL
- **ORM**: SQLAlchemy, Alembic
- **메시지 브로커**: Redis
- **서버**: Uvicorn
- **의존성 관리**: Poetry
- **컨테이너**: Docker

## 🚀 시작하기

### 1. 환경 변수 설정

`.env.development` 파일을 복사하여 `.env` 파일을 생성합니다. 이 파일에는 데이터베이스 연결 정보 등 주요 환경 변수가 포함되어 있습니다.

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

Uvicorn을 사용하여 FastAPI 개발 서버를 실행하고, 별도의 터미널에서 Celery 워커를 실행합니다.

- **FastAPI 서버 실행:**
  ```bash
  poetry run uvicorn run:app --reload --host 0.0.0.0 --port 8000
  ```

- **Celery 워커 실행:**
  ```bash
  poetry run celery -A celery_worker.worker worker --loglevel=info
  ```

이제 다음 주소에서 API 서버에 접속할 수 있습니다:
- **API 문서 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **대체 API 문서 (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## ✅ 테스트

`pytest`를 사용하여 프로젝트의 테스트를 실행할 수 있습니다.

```bash
poetry run pytest
```

## 📁 프로젝트 구조

```
backend_fastapi/
├── app/                      # 📱 애플리케이션 소스 코드
│   ├── api/                  # 🚀 API 엔드포인트 라우터
│   ├── core/                 # ⚙️ 핵심 설정 (FastAPI, Celery, DB 등)
│   ├── crud/                 # 🗄️ 데이터베이스 CRUD 연산
│   ├── exceptions/           # 🚨 사용자 정의 예외
│   ├── handlers/             # ✋ 예외 핸들러
│   ├── middleware/           # 🔄 미들웨어
│   ├── models/               # 🏗️ SQLAlchemy 모델
│   ├── schemas/              # 📋 Pydantic 스키마
│   ├── security/             # 🔐 보안 관련 로직
│   ├── services/             # 💼 비즈니스 로직
│   └── utils/                # 🛠️ 유틸리티 함수
├── tests/                    # 🧪 테스트 코드
├── migrations/               # 📊 데이터베이스 마이그레이션 (Alembic)
├── .env.development          # 🌱 개발 환경 변수 예시
├── celery_worker.py          # 👷 Celery 워커 엔트리포인트
├── docker-compose.yml        # 🐳 Docker 서비스 정의
├── poetry.lock               # 🔒 의존성 잠금 파일
├── pyproject.toml            # 📦 Poetry 의존성 및 프로젝트 설정
└── README.md                 # 📖 이 파일
```
