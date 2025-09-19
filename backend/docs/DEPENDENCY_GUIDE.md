# 프로젝트 의존성 가이드

이 문서는 `pyproject.toml`에 정의된 프로젝트의 의존성에 대한 개요를 제공합니다.

## 핵심 의존성 (Core Dependencies)

애플리케이션 실행에 필요한 주요 라이브러리입니다.

### 웹 프레임워크 및 서버
- **fastapi**: API 빌드를 위한 현대적이고 빠른(고성능) 웹 프레임워크입니다.
- **uvicorn**: FastAPI 애플리케이션을 실행하는 데 사용되는 ASGI(Asynchronous Server Gateway Interface) 서버입니다.
- **gunicorn**: UNIX용 WSGI HTTP 서버로, 프로덕션 환경에서 Uvicorn 워커를 관리하고 실행하는 데 자주 사용됩니다.

### 데이터베이스 및 ORM
- **sqlalchemy**: PostgreSQL 데이터베이스와 비동기적으로 상호 작용하는 데 사용되는 SQL 툴킷 및 객체 관계형 매퍼(ORM)입니다.
- **asyncpg**: SQLAlchemy를 사용하여 PostgreSQL과 비동기적으로 통신하기 위한 드라이버입니다.
- **psycopg2-binary** / **psycopg**: Python용 PostgreSQL 어댑터로, 데이터베이스와의 통신을 가능하게 합니다.
- **alembic**: SQLAlchemy를 위한 데이터베이스 마이그레이션 도구로, 데이터베이스 스키마 변경을 관리하고 적용하는 데 사용됩니다.
- **sqlacodegen**: 기존 데이터베이스 스키마에서 SQLAlchemy 모델 코드를 자동으로 생성하는 도구입니다.

### 비동기 작업 및 메시징
- **celery**: 메인 애플리케이션 흐름과 별개로 백그라운드 작업을 비동기적으로 실행하기 위한 분산 작업 큐입니다.
- **redis**: Redis용 Python 클라이언트입니다. 이 프로젝트에서는 Celery의 메시지 브로커 및 결과 백엔드로 사용됩니다.
- **flower**: Celery 클러스터를 모니터링하고 관리하기 위한 웹 기반 도구입니다.
- **aiokafka**: 메시지 처리에 사용되는 Apache Kafka용 비동기 클라이언트입니다.
- **greenlet**: 경량 동시성 모델을 제공하며, 고급 비동기 라이브러리의 의존성으로 자주 사용됩니다.

### AI 및 머신러닝
- **transformers**: 다양한 작업을 위한 수천 개의 사전 학습된 모델을 제공하는 Hugging Face 라이브러리입니다.
- **huggingface-hub**: Hugging Face Hub와 상호 작용하기 위한 클라이언트 라이브러리로, 모델 및 데이터셋 다운로드를 지원합니다.
- **numpy**: Python의 과학 컴퓨팅을 위한 기본 패키지로, 많은 AI/ML 라이브러리의 핵심 의존성입니다.

### 유틸리티
- **pydantic** / **pydantic-settings**: 데이터 유효성 검사, 파싱 및 설정 관리를 위한 라이브러리입니다. FastAPI에서 광범위하게 사용됩니다.

## 개발 의존성 (Development Dependencies)

개발, 테스트 및 코드 품질 보증에 사용되는 라이브러리입니다. 프로덕션 환경에는 필요하지 않습니다.

- **pytest**: 테스트 작성을 위한 강력한 프레임워크입니다.
- **pytest-asyncio**: asyncio 코드를 테스트하기 위한 pytest 플러그인입니다.
- **black**: 일관된 코드 스타일을 보장하는 코드 포맷터입니다.
- **flake8**: PEP8 스타일 가이드, 프로그래밍 오류 및 코드 복잡성에 대해 코드를 검사하는 도구입니다.
- **mypy**: Python용 정적 타입 검사기로, 런타임 전에 타입 관련 버그를 찾는 데 도움을 줍니다.
- **pre-commit**: 커밋 전에 코드 품질을 보장하기 위해 다국어 pre-commit 훅을 관리하고 유지하는 프레임워크입니다.