# Quick Start Guide - Docker 빌드 및 실행

## 🚀 빠른 시작

### 전체 프로세스 (3분 이내)

```bash
# 1. 베이스 이미지 빌드 (최초 1회, 15초)
docker-compose -f docker-compose.domains.yml build ml-base ml-gpu-base

# 2. 서비스 빌드 (3-5초)
docker-compose -f docker-compose.domains.yml build app-ocr-cpu app-ocr-gpu app-llm

# 3. 실행
docker-compose -f docker-compose.domains.yml up -d
```

## 📋 서비스별 가이드

### OCR CPU 버전

```bash
# 빌드 (3초)
docker-compose -f docker-compose.domains.yml build app-ocr-cpu

# 실행
docker-compose -f docker-compose.domains.yml up -d app-ocr-cpu

# 로그 확인
docker logs -f fastapi-app-ocr-cpu

# 접속
curl http://localhost:35052/health
# 브라우저: http://localhost:35052/docs
```

### OCR GPU 버전 (NVIDIA GPU 필요)

```bash
# 빌드 (3-5초)
docker-compose -f docker-compose.domains.yml build app-ocr-gpu

# 실행
docker-compose -f docker-compose.domains.yml up -d app-ocr-gpu

# 로그 확인
docker logs -f fastapi-app-ocr-gpu

# 접속
curl http://localhost:35053/health
# 브라우저: http://localhost:35053/docs
```

### LLM 서비스 (NVIDIA GPU 필요)

```bash
# 빌드 (2-3초)
docker-compose -f docker-compose.domains.yml build app-llm

# 실행
docker-compose -f docker-compose.domains.yml up -d app-llm

# 로그 확인
docker logs -f fastapi-app-llm

# 접속
curl http://localhost:35051/health
# 브라우저: http://localhost:35051/docs
```

## 🔧 유용한 명령어

### 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 (중지된 것 포함)
docker ps -a

# 이미지 목록
docker images | grep backend

# 네트워크 확인
docker network ls
```

### 재시작

```bash
# 특정 서비스 재시작
docker-compose -f docker-compose.domains.yml restart app-ocr-cpu

# 전체 재시작
docker-compose -f docker-compose.domains.yml restart
```

### 중지 및 제거

```bash
# 특정 서비스 중지
docker-compose -f docker-compose.domains.yml stop app-ocr-cpu

# 특정 서비스 제거
docker-compose -f docker-compose.domains.yml down app-ocr-cpu

# 전체 중지 및 제거
docker-compose -f docker-compose.domains.yml down
```

### 로그 확인

```bash
# 실시간 로그
docker logs -f fastapi-app-ocr-cpu

# 최근 100줄
docker logs --tail 100 fastapi-app-ocr-cpu

# 타임스탬프 포함
docker logs -t fastapi-app-ocr-cpu
```

### 컨테이너 내부 접속

```bash
# bash 쉘 실행
docker exec -it fastapi-app-ocr-cpu bash

# Python 실행
docker exec -it fastapi-app-ocr-cpu python

# 환경변수 확인
docker exec fastapi-app-ocr-cpu env
```

## 🐛 트러블슈팅

### 베이스 이미지 오류

```bash
# 문제
Error: image backend-ml-base:latest not found

# 해결
docker-compose -f docker-compose.domains.yml build ml-base
```

### 포트 충돌

```bash
# 문제
Error: port 35052 is already in use

# 해결 1: 기존 컨테이너 확인 및 중지
docker ps | grep 35052
docker stop <container_id>

# 해결 2: docker-compose.domains.yml에서 포트 변경
ports:
  - "35060:5050"  # 35052 → 35060
```

### DB 연결 실패

```bash
# 문제
Connection refused to postgres-server

# 해결 1: PostgreSQL 서비스 확인
docker ps | grep postgres

# 해결 2: 네트워크 확인
docker network inspect app-network

# 해결 3: .env.production 확인
cat .env.production | grep DATABASE_URL
```

### 빌드 캐시 문제

```bash
# 완전히 새로 빌드
docker-compose -f docker-compose.domains.yml build --no-cache app-ocr-cpu
```

### 이미지 용량 부족

```bash
# 사용하지 않는 이미지 정리
docker image prune

# 댕글링 이미지 모두 제거
docker image prune -a

# 디스크 사용량 확인
docker system df
```

## 📊 서비스 포트 목록

| 서비스 | 포트 | 설명 |
|--------|------|------|
| app-base | 35050 | 기본 FastAPI 서비스 |
| app-llm | 35051 | LLM 서비스 (GPU) |
| app-ocr-cpu | 35052 | OCR CPU 버전 |
| app-ocr-gpu | 35053 | OCR GPU 버전 |
| postgres | 15432 | PostgreSQL |
| redis | 6379 | Redis |

## 🔍 헬스체크

모든 서비스는 `/health` 엔드포인트를 제공합니다:

```bash
# 기본 헬스체크
curl http://localhost:35052/health

# 상세 정보
curl http://localhost:35052/health | jq .

# 응답 예시
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

## 🎯 개발 워크플로우

### 1. 코드 수정 후 재시작

```bash
# 소스 코드는 볼륨 마운트되어 있어 재빌드 불필요
docker-compose -f docker-compose.domains.yml restart app-ocr-cpu
```

### 2. 의존성 추가 후

```bash
# pyproject.toml 수정 후 재빌드 필요
docker-compose -f docker-compose.domains.yml build app-ocr-cpu
docker-compose -f docker-compose.domains.yml up -d app-ocr-cpu
```

### 3. 베이스 이미지 업데이트 후

```bash
# 1. 베이스 재빌드
docker-compose -f docker-compose.domains.yml build --no-cache ml-base

# 2. 모든 서비스 재빌드
docker-compose -f docker-compose.domains.yml build app-ocr-cpu app-ocr-gpu app-llm

# 3. 재시작
docker-compose -f docker-compose.domains.yml up -d
```

## 📚 추가 문서

- [베이스 이미지 전략 상세](./DOCKER_BASE_IMAGE_STRATEGY.md)
- [프로젝트 CLAUDE.md](../CLAUDE.md)
