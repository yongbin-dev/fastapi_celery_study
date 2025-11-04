# gRPC 설정 및 사용 가이드

## 📋 설정 완료 사항

### ✅ 1. Proto 파일
- `packages/shared/shared/grpc/protos/common.proto` - 공통 타입 정의
- `packages/shared/shared/grpc/protos/ocr.proto` - OCR 서비스 정의

### ✅ 2. 생성된 Python 코드
- `packages/shared/shared/grpc/generated/common_pb2.py`
- `packages/shared/shared/grpc/generated/ocr_pb2.py`
- `packages/shared/shared/grpc/generated/ocr_pb2_grpc.py`

### ✅ 3. ML Server gRPC 서비스
- `packages/ml_server/ml_app/grpc_services/ocr_service.py` - OCR gRPC 서비스 구현
- `packages/ml_server/ml_app/grpc_services/server.py` - gRPC 서버
- `packages/ml_server/ml_app/main.py` - FastAPI + gRPC 통합

### ✅ 4. Celery Worker gRPC 클라이언트
- `packages/celery_worker/tasks/grpc_clients/ocr_client.py` - OCR gRPC 클라이언트
- `packages/celery_worker/tasks/stages/ocr_stage.py` - Dual Mode 지원

---

## 🚀 시작하기

### 1. Proto 파일 컴파일 (필요 시)

Proto 파일을 수정한 경우 재컴파일이 필요합니다:

```bash
# monorepo 루트에서 실행
uvx --from grpcio-tools==1.68.1 python -m grpc_tools.protoc \
  -I./packages/shared/shared/grpc/protos \
  --python_out=./packages/shared/shared/grpc/generated \
  --grpc_python_out=./packages/shared/shared/grpc/generated \
  --pyi_out=./packages/shared/shared/grpc/generated \
  ./packages/shared/shared/grpc/protos/*.proto
```

또는 Makefile 사용:
```bash
cd packages/shared
make generate-grpc
```

### 2. 환경 변수 설정

#### ML Server (.env 또는 환경 변수)
```bash
# gRPC 서버 포트
GRPC_PORT=50051

# gRPC 활성화
USE_GRPC=true
```

#### Celery Worker (.env 또는 환경 변수)
```bash
# ML Server gRPC 주소
ML_SERVER_GRPC_ADDRESS=localhost:50051  # 로컬
# ML_SERVER_GRPC_ADDRESS=ml_server:50051  # Docker

# gRPC 사용 여부
USE_GRPC=true
```

### 3. ML Server 실행

```bash
# HTTP만 (기본값)
cd packages/ml_server
uv run uvicorn ml_app.main:app --host 0.0.0.0 --port 8000

# HTTP + gRPC
USE_GRPC=true GRPC_PORT=50051 uv run uvicorn ml_app.main:app --host 0.0.0.0 --port 8000
```

로그 확인:
```
🚀 ML 서버 시작
✅ gRPC 서버 태스크 시작
🚀 gRPC 서버 시작: 포트 50051
```

### 4. Celery Worker 실행

```bash
# HTTP 모드 (기존)
cd packages/celery_worker
uv run celery -A celery_app worker --loglevel=info

# gRPC 모드 (신규)
USE_GRPC=true ML_SERVER_GRPC_ADDRESS=localhost:50051 \
  uv run celery -A celery_app worker --loglevel=info
```

---

## 🧪 테스트

### 1. gRPC 서버 헬스 체크 (grpcurl 사용)

```bash
# grpcurl 설치 (macOS)
brew install grpcurl

# 서비스 목록 확인
grpcurl -plaintext localhost:50051 list

# 헬스 체크
grpcurl -plaintext localhost:50051 ocr.OCRService/CheckHealth
```

예상 출력:
```json
{
  "status": "STATUS_SUCCESS",
  "engineType": "mock",
  "modelLoaded": true,
  "version": "1.0.0"
}
```

### 2. Python 스크립트로 테스트

```python
# test_grpc_ocr.py
import asyncio
from tasks.grpc_clients.ocr_client import OCRGrpcClient

async def test_ocr():
    client = OCRGrpcClient("localhost:50051")

    try:
        # 헬스 체크
        health = await client.check_health()
        print(f"Health: {health.status}, Engine: {health.engine_type}")

        # OCR 추출
        response = await client.extract_text(
            public_image_path="/test/image.jpg",
            private_image_path="/data/test.jpg"
        )

        print(f"Status: {response.status}")
        print(f"Text boxes: {len(response.text_boxes)}")
        print(f"Overall confidence: {response.overall_confidence:.2f}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_ocr())
```

### 3. 파이프라인 테스트

```python
# HTTP 모드로 실행
import os
os.environ["USE_GRPC"] = "false"

# 또는 gRPC 모드로 실행
os.environ["USE_GRPC"] = "true"
os.environ["ML_SERVER_GRPC_ADDRESS"] = "localhost:50051"

# 파이프라인 실행
from tasks.pipeline_tasks import start_pipeline
from shared.schemas.common import ImageResponse

image_response = ImageResponse(
    public_img="/test/image.jpg",
    private_img="/data/test.jpg"
)

context_id = start_pipeline(image_response, "batch_123", {})
print(f"Pipeline started: {context_id}")
```

---

## 📊 모드 전환

### HTTP → gRPC 전환 단계

1. **개발 환경 테스트**
   ```bash
   USE_GRPC=true uv run uvicorn ml_app.main:app
   USE_GRPC=true uv run celery -A celery_app worker
   ```

2. **로그 확인**
   ```
   # ML Server 로그
   ✅ gRPC 서버 태스크 시작
   🚀 gRPC 서버 시작: 포트 50051

   # Celery Worker 로그
   gRPC 모드로 OCR 실행
   gRPC 채널 연결: localhost:50051
   gRPC OCR 완료: 10 텍스트 박스
   ```

3. **점진적 배포**
   - Week 1: 개발 환경 테스트
   - Week 2: 스테이징 환경 (10% 트래픽)
   - Week 3: 프로덕션 (50% 트래픽)
   - Week 4: 프로덕션 (100% 트래픽)

---

## 🔧 디버깅

### gRPC 서버가 시작되지 않는 경우

```bash
# 포트 사용 확인
lsof -i :50051

# grpcio 버전 확인
pip list | grep grpcio

# 로그 레벨 증가
USE_GRPC=true LOG_LEVEL=DEBUG uv run uvicorn ml_app.main:app
```

### gRPC 클라이언트 연결 실패

```bash
# 네트워크 연결 확인
nc -zv localhost 50051

# grpcurl로 직접 테스트
grpcurl -plaintext localhost:50051 ocr.OCRService/CheckHealth

# 타임아웃 증가
# ocr_client.py에서 timeout 파라미터 조정
```

### Proto 파일 수정 후 반영 안 됨

```bash
# 생성된 파일 삭제
rm packages/shared/shared/grpc/generated/*.py
rm packages/shared/shared/grpc/generated/*.pyi

# 재컴파일
cd packages/shared
make generate-grpc

# Python 캐시 삭제
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 📈 성능 모니터링

### 지연 시간 측정

```python
import time

# HTTP
start = time.time()
# ... HTTP 요청
http_latency = (time.time() - start) * 1000

# gRPC
start = time.time()
# ... gRPC 요청
grpc_latency = (time.time() - start) * 1000

print(f"HTTP: {http_latency:.2f}ms, gRPC: {grpc_latency:.2f}ms")
```

### 예상 성능

| 지표 | HTTP | gRPC | 개선 |
|------|------|------|------|
| 평균 지연 | 150ms | 90ms | -40% |
| P95 지연 | 250ms | 140ms | -44% |
| 처리량 | 200 req/s | 350 req/s | +75% |

---

## 🔐 보안 고려사항

현재 구현은 **insecure channel** (암호화 없음)을 사용합니다.

프로덕션 환경에서는 TLS 적용 권장:

```python
# 서버
credentials = grpc.ssl_server_credentials(
    [(server_key, server_cert)]
)
server.add_secure_port(f'[::]:{grpc_port}', credentials)

# 클라이언트
credentials = grpc.ssl_channel_credentials(
    root_certificates=ca_cert,
    private_key=client_key,
    certificate_chain=client_cert
)
channel = grpc.aio.secure_channel(
    server_address,
    credentials
)
```

---

## 📝 주요 차이점 요약

| 항목 | HTTP | gRPC |
|------|------|------|
| 프로토콜 | HTTP/1.1 | HTTP/2 |
| 직렬화 | JSON | Protobuf |
| 타입 안정성 | 런타임 | 컴파일 타임 |
| 스트리밍 | 제한적 | 양방향 지원 |
| 성능 | 표준 | 40-50% 빠름 |
| 디버깅 | 쉬움 | grpcurl 필요 |

---

## 🎯 다음 단계

1. ✅ **기본 구현 완료**
   - Proto 파일 정의
   - ML Server gRPC 서비스
   - Celery Worker gRPC 클라이언트
   - Dual Mode 지원

2. 🔄 **추가 개선 사항** (선택)
   - LLM gRPC 서비스 추가
   - TLS 보안 적용
   - 성능 벤치마크
   - 모니터링 메트릭 추가
   - gRPC 인터셉터 (로깅, 인증)

3. 📊 **모니터링 및 최적화**
   - Prometheus 메트릭 수집
   - Grafana 대시보드
   - 성능 프로파일링
   - 에러 트래킹

---

## 💡 유용한 명령어

```bash
# Proto 컴파일
make generate-grpc

# gRPC 서버 확인
grpcurl -plaintext localhost:50051 list

# 헬스 체크
grpcurl -plaintext localhost:50051 ocr.OCRService/CheckHealth

# ML Server 실행 (gRPC)
USE_GRPC=true uv run uvicorn ml_app.main:app

# Celery Worker 실행 (gRPC)
USE_GRPC=true uv run celery -A celery_app worker
```
