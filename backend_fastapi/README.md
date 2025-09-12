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

## 🚀 빠른 시작하기

### 🔥 **자동 설정 (추천)**

```bash
# 1단계: 프로젝트 클론
git clone <repository-url>
cd backend_fastapi

# 2단계: 자동 환경 설정 실행
./scripts/setup-dev.sh
```

위 스크립트가 자동으로 다음을 수행합니다:
- ✅ direnv 설치 및 설정
- ✅ Poetry 설치 및 의존성 설치  
- ✅ 가상환경 자동 활성화 설정
- ✅ 개발 도구 통합

### 🛠️ **수동 설정**

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

## 💻 **개발 서버 실행**

가상환경이 자동 활성화된 상태에서 다음 명령어들을 사용하세요:

### 🚀 **빠른 명령어 (direnv 설정 완료 후)**
```bash
# FastAPI 개발 서버 시작
dev

# Celery Worker 시작  
worker

# Flower 모니터링 시작
flower

# 테스트 실행
test

# 코드 포맷팅
format

# 도움말 확인
help
```

### 🛠️ **일반 명령어**
```bash
# FastAPI 서버
uvicorn app.main:app --reload --host 0.0.0.0 --port 5050

# Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Flower (Celery 모니터링)
celery -A app.core.celery_app flower --port=5555
```

### 📱 **서비스 접속**
- **FastAPI API**: http://localhost:5050
- **API 문서**: http://localhost:5050/docs  
- **ReDoc**: http://localhost:5050/redoc
- **Flower 모니터링**: http://localhost:5555

## ✅ 테스트

`pytest`를 사용하여 프로젝트의 테스트를 실행할 수 있습니다.

```bash
poetry run pytest
```

## 📁 프로젝트 구조

```
backend_fastapi/
├── app/                           # 📱 애플리케이션 소스 코드
│   ├── api/                       # 🚀 API 라우터
│   │   ├── deps.py                # 의존성 및 예외 핸들러
│   │   └── v1/                    # API v1 버전
│   ├── core/                      # ⚙️ 핵심 설정
│   │   ├── config.py              # 환경 설정
│   │   ├── database.py            # 데이터베이스 연결
│   │   ├── celery_app.py          # Celery 설정
│   │   ├── logging.py             # 로깅 시스템
│   │   └── exceptions.py          # 예외 처리
│   ├── crud/                      # 🗄️ CRUD 연산
│   ├── models/                    # 🏗️ SQLAlchemy 모델
│   ├── schemas/                   # 📋 Pydantic 스키마
│   ├── services/                  # 💼 비즈니스 로직
│   ├── security/                  # 🔐 보안 (JWT, 인증, Rate Limit)
│   ├── middleware/                # 🔄 미들웨어
│   └── utils/                     # 🛠️ 유틸리티
├── tests/                         # 🧪 테스트
│   ├── conftest.py                # 테스트 설정
│   ├── test_api/                  # API 테스트
│   ├── test_core/                 # 코어 모듈 테스트
│   └── test_utils/                # 유틸리티 테스트
├── scripts/                       # 📜 개발 스크립트
│   └── setup-dev.sh               # 개발환경 자동 설정
├── .vscode/                       # 🎨 VS Code 설정
├── migrations/                    # 📊 데이터베이스 마이그레이션
├── .envrc                         # 🔧 direnv 자동 환경 설정
├── .env.development               # 🌱 개발환경 변수
├── .env.production                # 🚀 운영환경 변수
├── .env.staging                   # 🧪 스테이징환경 변수
├── pyproject.toml                 # 📦 Poetry 의존성 관리
├── docker-compose.yml             # 🐳 Docker 서비스 정의
├── README.md                      # 📖 프로젝트 문서
└── DEVELOPMENT_SETUP.md           # 🛠️ 개발환경 설정 가이드
```

### 🏗️ **아키텍처 특징**

- ✅ **계층화 아키텍처**: API → Service → CRUD → Model
- ✅ **의존성 주입**: FastAPI의 DI 시스템 활용  
- ✅ **환경별 설정**: development/staging/production 분리
- ✅ **자동 환경 관리**: direnv로 가상환경 자동 활성화
- ✅ **통합 로깅**: 구조화된 로깅 시스템
- ✅ **보안 내장**: JWT, Rate Limiting, 인증/권한
- ✅ **테스트 완비**: 단위/통합 테스트 구조