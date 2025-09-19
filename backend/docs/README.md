# 프로젝트 구조 가이드

이 문서는 FastAPI 프로젝트의 각 폴더와 파일의 역할을 설명합니다.

## 📁 프로젝트 구조

```
study/
├── app/                          # 메인 애플리케이션 패키지
│   ├── api/                      # API 레이어
│   │   └── v1/                   # API 버전 관리
│   │       ├── endpoints/        # 엔드포인트별 라우터
│   │       └── router.py         # API v1 메인 라우터
│   ├── core/                     # 핵심 설정 및 공통 모듈
│   │   ├── celery_app.py         # Celery 앱 설정
│   │   ├── config.py             # 환경 변수 및 설정
│   │   └── exceptions.py         # 커스텀 예외 정의
│   ├── handlers/                 # 예외 및 이벤트 핸들러
│   │   └── exception_handlers.py # 전역 예외 처리
│   ├── middleware/               # 미들웨어
│   │   ├── request_middleware.py # 요청 처리 미들웨어
│   │   └── response_middleware.py# 응답 처리 미들웨어
│   ├── schemas/                  # Pydantic 데이터 모델
│   │   └── response.py           # API 응답 스키마
│   ├── services/                 # 비즈니스 로직 레이어
│   │   ├── ai/                   # AI 모델 관련 서비스
│   │   │   ├── base_model.py     # AI 모델 추상 클래스
│   │   │   └── llm_model.py      # LLM 모델 구현체
│   │   └── model_service.py      # 모델 관리 서비스
│   ├── utils/                    # 유틸리티 함수
│   │   └── response_builder.py   # 응답 생성 도우미
│   ├── dependencies.py           # FastAPI 의존성 주입
│   ├── main.py                   # FastAPI 앱 진입점
│   └── tasks.py                  # Celery 태스크 정의
├── docs/                         # 프로젝트 문서
├── logs/                         # 로그 파일
├── celery_worker.py              # Celery 워커 실행
├── docker-compose.yml            # Docker 컨테이너 설정
├── Dockerfile                    # Docker 이미지 빌드
└── pyproject.toml                # Poetry 의존성 관리
```

## 📂 각 폴더별 상세 설명

### 🔌 **app/api/**
- **역할**: REST API 엔드포인트 관리
- **구조**: 버전별로 분리 (v1, v2...)
- **내용**: 
  - `endpoints/`: 기능별 라우터 파일 (users.py, tasks.py 등)
  - `router.py`: 버전별 메인 라우터

### ⚙️ **app/core/**
- **역할**: 애플리케이션 핵심 설정 및 공통 모듈
- **내용**:
  - `config.py`: 환경변수, 데이터베이스 설정 등
  - `celery_app.py`: Celery 비동기 작업 설정
  - `exceptions.py`: 커스텀 예외 클래스

### 🛡️ **app/handlers/**
- **역할**: 전역 예외 처리 및 이벤트 핸들링
- **내용**: HTTP 예외, 검증 오류 등의 통일된 처리

### 🔄 **app/middleware/**
- **역할**: HTTP 요청/응답 중간 처리
- **내용**:
  - 로깅, 인증, CORS 처리
  - 요청/응답 데이터 변환

### 📋 **app/schemas/**
- **역할**: Pydantic 모델 정의
- **내용**: 
  - API 요청/응답 데이터 구조
  - 데이터 검증 및 직렬화

### 🏢 **app/services/**
- **역할**: 비즈니스 로직 레이어
- **구조**:
  - `ai/`: AI 모델 관련 서비스
  - 도메인별 서비스 클래스
- **특징**: 데이터 접근과 비즈니스 로직 분리

### 🛠️ **app/utils/**
- **역할**: 재사용 가능한 유틸리티 함수
- **내용**: 응답 생성, 데이터 변환, 헬퍼 함수

### 💉 **app/dependencies.py**
- **역할**: FastAPI 의존성 주입 관리
- **내용**: 데이터베이스 세션, 인증, 서비스 인스턴스 주입

### 🎯 **app/main.py**
- **역할**: FastAPI 애플리케이션 진입점
- **내용**: 앱 설정, 미들웨어 등록, 라우터 연결

## 🔄 데이터 플로우

```
HTTP Request
    ↓
Middleware (요청 전처리)
    ↓
API Router (app/api/)
    ↓
Dependencies (의존성 주입)
    ↓
Services (비즈니스 로직)
    ↓
Schemas (데이터 검증)
    ↓
Utils (응답 생성)
    ↓
Middleware (응답 후처리)
    ↓
HTTP Response
```

## 📏 설계 원칙

### 1. **관심사의 분리 (Separation of Concerns)**
- API 레이어: HTTP 요청/응답 처리
- Service 레이어: 비즈니스 로직
- Schema 레이어: 데이터 검증 및 직렬화

### 2. **의존성 주입 (Dependency Injection)**
- `dependencies.py`를 통한 중앙집중식 의존성 관리
- 테스트 용이성 및 결합도 감소

### 3. **계층형 아키텍처 (Layered Architecture)**
- 명확한 레이어 구분
- 단방향 의존성 (상위 → 하위)

### 4. **도메인 주도 설계 (Domain-Driven Design)**
- 서비스별 폴더 분리
- 비즈니스 로직의 응집성

## 🚀 확장 가이드

### 새로운 API 추가시:
1. `app/schemas/`에 요청/응답 모델 정의
2. `app/services/`에 비즈니스 로직 구현
3. `app/api/v1/endpoints/`에 라우터 추가
4. `app/api/v1/router.py`에 라우터 등록

### 새로운 서비스 추가시:
1. `app/services/`에 서비스 클래스 생성
2. `app/dependencies.py`에 의존성 함수 추가
3. 필요시 `app/schemas/`에 관련 모델 추가

이 구조는 FastAPI 커뮤니티의 베스트 프랙티스를 따르며, 확장성과 유지보수성을 고려하여 설계되었습니다.