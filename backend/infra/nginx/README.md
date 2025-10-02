# Nginx API Gateway 설정 가이드

## 개요

Nginx를 사용한 API Gateway로 도메인별 마이크로서비스를 단일 엔드포인트로 통합합니다.

## 아키텍처

```
클라이언트
    ↓
Nginx Gateway (localhost:8000)
    ├─→ /api/v1/ocr/*      → OCR 서비스 (app-ocr-cpu:5050, app-ocr-gpu:5050)
    ├─→ /api/v1/llm/*      → LLM 서비스 (app-llm:5050)
    ├─→ /api/v1/pipeline/* → Pipeline 서비스 (app-base:5050)
    ├─→ /api/v1/common/*   → Common 서비스 (app-base:5050)
    └─→ /*                 → Base 서비스 (app-base:5050)
```

## 서비스 시작

### 1. 네트워크 생성 (최초 1회)
```bash
docker network create app-network
```

### 2. 서비스 시작
```bash
# 전체 서비스 시작
cd /home/yb/dev/fastapi_celery_study/backend
docker-compose -f docker-compose.domains.yml up -d

# Gateway만 재시작
docker-compose -f docker-compose.domains.yml restart nginx-gateway

# 특정 서비스만 시작
docker-compose -f docker-compose.domains.yml up -d nginx-gateway app-base
```

### 3. 상태 확인
```bash
# 서비스 상태
docker-compose -f docker-compose.domains.yml ps

# Gateway 로그
docker logs api-gateway -f

# 헬스체크
curl http://localhost:8000/health
```

## 엔드포인트 테스트

### 기본 엔드포인트
```bash
# 루트
curl http://localhost:8000/

# 헬스체크
curl http://localhost:8000/health

# 버전 정보
curl http://localhost:8000/version
```

### OCR 도메인 (로드 밸런싱: CPU + GPU)
```bash
# OCR 엔드포인트
curl http://localhost:8000/api/v1/ocr/predict

# 이미지 업로드 (예시)
curl -X POST http://localhost:8000/api/v1/ocr/predict \
  -F "file=@test.jpg"
```

### LLM 도메인
```bash
# LLM 엔드포인트
curl http://localhost:8000/api/v1/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

### Pipeline (Orchestration)
```bash
# 파이프라인 실행
curl http://localhost:8000/api/v1/pipeline/execute
```

## 로그 확인

로그는 `logs/nginx/` 디렉토리에 저장됩니다:

```bash
# Access 로그
tail -f logs/nginx/access.log

# Error 로그
tail -f logs/nginx/error.log
```

## Nginx 설정 변경

`infra/nginx/nginx.conf` 파일을 수정한 후:

```bash
# 설정 테스트
docker exec api-gateway nginx -t

# 재시작 (다운타임 없음)
docker exec api-gateway nginx -s reload

# 또는 컨테이너 재시작
docker-compose -f docker-compose.domains.yml restart nginx-gateway
```

## 포트 매핑

| 서비스 | 내부 포트 | 외부 포트 (직접 접근) | Gateway 경로 |
|--------|----------|---------------------|-------------|
| Base | 5050 | 35050 | `/` |
| OCR-CPU | 5050 | 35052 | `/api/v1/ocr/*` |
| OCR-GPU | 5050 | 35053 | `/api/v1/ocr/*` |
| LLM | 5050 | 35051 | `/api/v1/llm/*` |
| Gateway | 8000 | 8000 | - |

**권장:** Gateway를 통한 접근 (localhost:8000)을 사용하세요.

## 주요 설정

### 타임아웃 설정
- 기본: 300초 (5분)
- LLM: 600초 (10분) - 긴 처리 시간 고려

### 파일 업로드
- 최대 크기: 100MB
- 버퍼링: OFF (스트리밍 방식)

### 로드 밸런싱
OCR 서비스는 CPU와 GPU 서버 간 자동 로드 밸런싱됩니다.

## 모니터링

### Nginx 상태
```bash
curl http://localhost:8000/nginx-status
```

### 서비스 상태
```bash
# Base 서비스
curl http://localhost:8000/health

# OCR 서비스 (직접)
curl http://localhost:35052/health
curl http://localhost:35053/health

# LLM 서비스 (직접)
curl http://localhost:35051/health
```

## 트러블슈팅

### Gateway가 시작되지 않는 경우
```bash
# 네트워크 확인
docker network ls | grep app-network

# 네트워크 생성
docker network create app-network

# 설정 파일 문법 확인
docker run --rm -v $(pwd)/infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:alpine nginx -t
```

### 502 Bad Gateway 에러
```bash
# 백엔드 서비스 상태 확인
docker-compose -f docker-compose.domains.yml ps

# 백엔드 서비스 로그 확인
docker logs fastapi-app-base
docker logs fastapi-app-ocr-cpu
docker logs fastapi-app-llm

# 네트워크 연결 확인
docker exec api-gateway ping app-base -c 2
```

### 로그가 쌓이지 않는 경우
```bash
# 로그 디렉토리 생성
mkdir -p logs/nginx

# 권한 확인
chmod 755 logs/nginx
```

## 개발 vs 프로덕션

### 개발 환경
직접 포트 접근으로 빠른 디버깅:
```bash
# OCR 직접 접근
curl http://localhost:35052/api/v1/ocr/predict
```

### 프로덕션 환경
Gateway를 통한 접근만 허용:
```yaml
# docker-compose.domains.yml에서 외부 포트 제거
app-ocr-cpu:
  # ports:
  #   - "35052:5050"  # 주석 처리
```

## 참고

- Nginx 공식 문서: https://nginx.org/en/docs/
- 로드 밸런싱: https://nginx.org/en/docs/http/load_balancing.html
- 프록시 설정: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
