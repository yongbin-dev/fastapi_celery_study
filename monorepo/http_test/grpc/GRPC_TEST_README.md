# gRPC 테스트 가이드

OCR gRPC 서비스를 테스트하는 여러 방법을 제공합니다.

---

## 📋 준비 사항

### 1. gRPC 서버 실행

```bash
cd packages/ml_server
USE_GRPC=true GRPC_PORT=50051 uv run uvicorn ml_app.main:app --reload
```

서버가 정상 실행되면 다음 로그가 표시됩니다:
```
🚀 ML 서버 시작
✅ gRPC 서버 태스크 시작
🚀 gRPC 서버 시작: 포트 50051
```

---

## 🧪 테스트 방법

### 방법 1: Python 스크립트 (추천 ⭐)

가장 간편하고 상세한 출력을 제공합니다.

```bash
# 헬스 체크
python grpc_test.py health

# OCR 텍스트 추출
python grpc_test.py extract

# 배치 OCR (스트리밍)
python grpc_test.py batch

# 전체 테스트
python grpc_test.py all

# 커스텀 서버 주소
python grpc_test.py health --server localhost:50051

# 커스텀 이미지 경로
python grpc_test.py extract --image /path/to/image.jpg
```

**출력 예시**:
```
✅ 연결됨: localhost:50051

=== 헬스 체크 테스트 ===
📊 상태: STATUS_SUCCESS
🔧 엔진: mock
✓ 모델 로드: True
📌 버전: 1.0.0

🔌 연결 종료
```

---

### 방법 2: grpcurl (CLI 도구)

#### 설치

```bash
# macOS
brew install grpcurl

# Linux
wget https://github.com/fullstorydev/grpcurl/releases/download/v1.8.9/grpcurl_1.8.9_linux_x86_64.tar.gz
tar -xvf grpcurl_1.8.9_linux_x86_64.tar.gz
sudo mv grpcurl /usr/local/bin/
```

#### 사용법

```bash
# 1. 서비스 목록 확인
grpcurl -plaintext localhost:50051 list

# 2. OCRService 메서드 확인
grpcurl -plaintext localhost:50051 list ocr.OCRService

# 3. 헬스 체크
grpcurl -plaintext -d '{}' localhost:50051 ocr.OCRService/CheckHealth

# 4. OCR 텍스트 추출
grpcurl -plaintext -d '{
  "public_image_path": "/test/sample.jpg",
  "private_image_path": "/data/sample.jpg",
  "language": "korean",
  "confidence_threshold": 0.5,
  "use_angle_cls": true
}' localhost:50051 ocr.OCRService/ExtractText

# 5. Proto 정의 보기
grpcurl -plaintext localhost:50051 describe ocr.OCRService
grpcurl -plaintext localhost:50051 describe ocr.OCRRequest

# 6. 자동 테스트 스크립트 실행
./grpc_commands.sh
```

---

### 방법 3: Postman (GUI)

Postman v9.0 이상에서 gRPC를 지원합니다.

#### 설정 방법

1. **Postman 열기** → New → gRPC Request
2. **URL 입력**: `localhost:50051`
3. **Proto 파일 임포트**:
   - Method Definition → Use .proto file
   - `packages/shared/shared/grpc/protos/ocr.proto` 선택
   - `packages/shared/shared/grpc/protos/common.proto` 선택
4. **Service 선택**: `ocr.OCRService`
5. **Method 선택**: `CheckHealth`, `ExtractText`, 또는 `ExtractTextBatch`

#### 또는 컬렉션 임포트

```bash
# Postman에서 Import → Upload Files
# grpc_test.postman_collection.json 선택
```

---

### 방법 4: BloomRPC (GUI, 추천)

직관적인 GUI 기반 gRPC 클라이언트입니다.

#### 설치

```bash
# macOS
brew install --cask bloomrpc

# 또는 https://github.com/bloomrpc/bloomrpc/releases
```

#### 사용법

1. BloomRPC 실행
2. **Import Paths** → `packages/shared/shared/grpc/protos` 추가
3. **Import Proto** → `ocr.proto` 선택
4. **URL**: `localhost:50051` 입력
5. 왼쪽에서 메서드 선택 → 오른쪽에서 요청 편집 → Send

---

### 방법 5: Python 직접 코드

```python
import asyncio
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc
import grpc

async def test_ocr():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = ocr_pb2_grpc.OCRServiceStub(channel)

        # 헬스 체크
        request = ocr_pb2.HealthCheckRequest(service_name="OCRService")
        response = await stub.CheckHealth(request)
        print(f"Status: {response.status}")
        print(f"Engine: {response.engine_type}")
        print(f"Model loaded: {response.model_loaded}")

if __name__ == "__main__":
    asyncio.run(test_ocr())
```

---

## 📊 테스트 케이스

### 1. 헬스 체크

**요청**:
```json
{
  "service_name": "OCRService"
}
```

**응답**:
```json
{
  "status": "STATUS_SUCCESS",
  "engine_type": "mock",
  "model_loaded": true,
  "version": "1.0.0"
}
```

---

### 2. OCR 텍스트 추출

**요청**:
```json
{
  "public_image_path": "/test/sample.jpg",
  "private_image_path": "/data/sample.jpg",
  "language": "korean",
  "confidence_threshold": 0.5,
  "use_angle_cls": true
}
```

**응답**:
```json
{
  "status": "STATUS_SUCCESS",
  "text": "추출된 텍스트 내용...",
  "overall_confidence": 0.95,
  "text_boxes": [
    {
      "text": "Hello",
      "confidence": 0.98,
      "bbox": {
        "coordinates": [10.5, 20.3, 100.2, 20.3, 100.2, 50.1, 10.5, 50.1]
      }
    }
  ],
  "metadata": {
    "data": {
      "status": "success"
    }
  }
}
```

---

### 3. 배치 OCR (스트리밍)

**요청**:
```json
{
  "image_paths": [
    {
      "public_path": "/test/1.jpg",
      "private_path": "/data/1.jpg"
    },
    {
      "public_path": "/test/2.jpg",
      "private_path": "/data/2.jpg"
    }
  ],
  "language": "korean",
  "confidence_threshold": 0.5,
  "use_angle_cls": true
}
```

**응답 (스트림)**:
```json
// Progress 1
{
  "batch_id": "abc-123",
  "total_images": 2,
  "processed_images": 1,
  "current_result": { /* OCRResponse */ },
  "progress_percentage": 50.0
}

// Progress 2
{
  "batch_id": "abc-123",
  "total_images": 2,
  "processed_images": 2,
  "current_result": { /* OCRResponse */ },
  "progress_percentage": 100.0
}
```

---

## 🔧 문제 해결

### 1. "failed to connect to all addresses" 오류

```bash
# 서버가 실행 중인지 확인
lsof -i :50051

# 포트가 이미 사용 중이라면
kill -9 $(lsof -t -i:50051)
```

### 2. "unimplemented" 오류

Proto 파일이 컴파일되지 않았거나, 서버에서 메서드가 구현되지 않았습니다.

```bash
# Proto 재컴파일
cd packages/shared
make generate-grpc

# 서버 재시작
USE_GRPC=true uv run uvicorn ml_app.main:app --reload
```

### 3. Python 스크립트 실행 오류

```bash
# 경로 확인
python grpc_test.py health

# 만약 import 오류가 발생하면
export PYTHONPATH="$PWD/packages/shared:$PWD/packages/celery_worker"
python grpc_test.py health
```

---

## 📈 성능 테스트

### 동시 요청 테스트

```python
# concurrent_test.py
import asyncio
from grpc_test import GrpcTester

async def concurrent_test(num_requests: int = 100):
    tester = GrpcTester()
    await tester.connect()

    tasks = [
        tester.test_extract_text()
        for _ in range(num_requests)
    ]

    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    elapsed = asyncio.get_event_loop().time() - start

    print(f"총 요청: {num_requests}")
    print(f"성공: {sum(results)}")
    print(f"실패: {num_requests - sum(results)}")
    print(f"소요 시간: {elapsed:.2f}초")
    print(f"RPS: {num_requests / elapsed:.2f}")

    await tester.close()

# 실행
asyncio.run(concurrent_test(100))
```

---

## 🎯 다음 단계

1. ✅ **기본 테스트** - 헬스 체크, 단일 OCR 확인
2. ✅ **기능 테스트** - 다양한 이미지 형식, 언어 테스트
3. ✅ **성능 테스트** - 동시 요청, 처리량 측정
4. ⬜ **부하 테스트** - ghz, k6 등 도구 사용
5. ⬜ **통합 테스트** - Celery Worker와 통합 확인

---

## 📚 추가 도구

### ghz (gRPC 부하 테스트)

```bash
# 설치
brew install ghz

# 부하 테스트
ghz --insecure \
  --proto packages/shared/shared/grpc/protos/ocr.proto \
  --call ocr.OCRService/ExtractText \
  -d '{"private_image_path":"/data/test.jpg"}' \
  -n 1000 \
  -c 50 \
  localhost:50051
```

### grpcui (웹 UI)

```bash
# 설치
brew install grpcui

# 실행
grpcui -plaintext localhost:50051
# 브라우저에서 http://localhost:xxxx 열림
```

---

## 💡 유용한 팁

1. **로그 확인**: ML Server 로그에서 gRPC 요청 확인
2. **타임아웃 조정**: 큰 이미지는 타임아웃 증가 필요
3. **병렬 테스트**: Python asyncio로 동시 요청 테스트
4. **메트릭 수집**: Prometheus + Grafana 연동 고려
