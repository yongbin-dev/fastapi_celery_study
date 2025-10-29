# FastAPI + Celery + ML Server Monorepo

uv 워크스페이스 기반 Python 모노레포 프로젝트

## 패키지 구조

```
packages/
├── shared/          # 공통 라이브러리
├── api_server/      # FastAPI REST API 서버
├── celery_worker/   # Celery 백그라운드 작업 워커
└── ml_server/       # AI/ML 모델 서버
```

## 설치

```bash
make install
```

## 실행

```bash
# API 서버 실행
make run-api

# Celery 워커 실행
make run-worker

# ML 서버 실행
make run-ml
```

## 개발 도구

```bash
# 코드 포맷팅
make format

# 린트
make lint

# 타입 체크
make typecheck

# 테스트
make test
```

## 데이터 관리

### 전체 데이터 삭제

**주의**: 이 명령은 Supabase Storage와 PostgreSQL Database의 모든 데이터를 삭제합니다.

```bash
make clear-data
# 또는
make clean-data
```

또는 직접 스크립트 실행:

```bash
uv run python scripts/clear_all.py

# 디버그 모드 (상세 로그 출력)
uv run python scripts/clear_all.py --debug
```

**필수 요구사항**:
- `.env.development`에 `SUPABASE_SERVICE_ROLE_KEY` 설정 필요
- SERVICE_ROLE_KEY가 없으면 ANON_KEY로 시도하지만 권한 부족으로 실패할 수 있습니다

**삭제되는 데이터**:
- Supabase Storage (uploads 버킷의 모든 파일)
- PostgreSQL Database (모든 테이블 데이터)
  - ocr_text_boxes
  - ocr_executions
  - task_logs
  - chain_executions
  - batch_executions

**안전 장치**:
- 개발 환경에서만 실행 가능
- 실행 전 사용자 확인 필요 (yes 입력)

## 정리

```bash
# 캐시 파일 정리
make clean
```

## 도움말

```bash
make help
```
