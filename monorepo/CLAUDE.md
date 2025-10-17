# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 언어 설정

**중요**: 이 프로젝트에서는 모든 커뮤니케이션을 한국어로 진행합니다. 질문, 답변, 설명, 주석 등 모든 텍스트는 한국어를 사용해 주세요.

## 프로젝트 개요

이 프로젝트는 **uv 워크스페이스 기반 Python 모노레포**로, FastAPI + Celery + ML 서버로 구성된 마이크로서비스 아키텍처입니다.

### 패키지 구조

```
packages/
├── shared/          # 공통 라이브러리 (모든 패키지가 의존)
├── api_server/      # FastAPI 기반 REST API 서버
├── celery_worker/   # Celery 백그라운드 작업 워커
└── ml_server/       # AI/ML 모델 서버 (OCR 등)
```

### 패키지 의존성

- **shared**: 공통 유틸리티, 모델, CRUD, 설정, 미들웨어
  - `config/`: 환경 설정 (settings.py)
  - `models/`: SQLAlchemy 모델
  - `schemas/`: Pydantic 스키마
  - `repository/crud/`: 동기/비동기 CRUD 작업
  - `core/`: 데이터베이스, Redis, Supabase, 로깅
  - `middleware/`: 요청/응답 로깅
  - `exceptions/`: 예외 처리

- **api_server**: REST API 서버 (shared 의존)
  - 도메인 중심 아키텍처: `app/domains/{ocr,llm,pipeline,common}/`
  - 각 도메인: `controllers/`, `services/`, `schemas/`
  - Repository 패턴: `app/repository/crud/`

- **celery_worker**: 백그라운드 작업 워커 (shared 의존)
  - `core/`: Celery 설정 및 태스크 데코레이터
  - `tasks/`: 실제 작업 정의 (pipeline_tasks.py)

- **ml_server**: ML 모델 추론 서버 (독립 실행)
  - OCR 엔진: EasyOCR, PaddleOCR, Mock 엔진 지원
  - Factory 패턴으로 엔진 선택
