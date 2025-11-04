# gRPC 마이그레이션 가이드
## ML Server ↔ Celery Worker 통신 개선

---

## 📋 목차
1. [현재 아키텍처 분석](#현재-아키텍처-분석)
2. [gRPC 도입 배경 및 장점](#grpc-도입-배경-및-장점)
3. [마이그레이션 전략](#마이그레이션-전략)
4. [구현 단계](#구현-단계)
5. [Proto 파일 정의](#proto-파일-정의)
6. [ML Server 구현](#ml-server-구현)
7. [Celery Worker 구현](#celery-worker-구현)
8. [배포 및 전환 전략](#배포-및-전환-전략)
9. [성능 벤치마크](#성능-벤치마크)
10. [문제 해결 가이드](#문제-해결-가이드)

---

## 현재 아키텍처 분석

### 🔍 현재 통신 방식 (HTTP/REST)

```python
# celery_worker/tasks/stages/ocr_stage.py:58
async with httpx.AsyncClient(timeout=300.0) as client:
    response = await client.post(
        f"{self.ml_server_url}/ocr/extract",
        json={
            "public_image_path": context.public_file_path,
            "private_image_path": context.input_file_path,
        }
    )
```

### 📊 현재 통신 흐름

```
[Celery Worker - OCRStage]
    ↓ HTTP POST /ocr/extract
    ↓ JSON payload (image paths)
    ↓ httpx.AsyncClient (timeout 300s)

[ML Server - FastAPI]
    ↓ FastAPI Router
    ↓ OCRModel.predict()
    ↓ OCR Engine (EasyOCR/PaddleOCR)
    ↓ JSON response

[Celery Worker]
    ↓ Parse JSON
    ↓ Create OCRResult
    ↓ Save to Redis
```

### ⚠️ 현재 문제점

1. **JSON 직렬화 오버헤드**
   - 이미지 경로, 메타데이터를 JSON으로 변환
   - 대량 처리 시 직렬화 비용 증가

2. **HTTP 프로토콜 오버헤드**
   - HTTP/1.1 헤더 오버헤드
   - 커넥션 수립 비용
   - Keep-alive 관리 복잡성

3. **타입 안정성 부족**
   - 런타임에만 스키마 검증
   - Pydantic으로 검증하지만 통신 레벨에서 보장 안 됨

4. **스트리밍 지원 부족**
   - 대용량 이미지 배치 처리 시 제한적
   - 진행 상황 스트리밍 불가

---

## gRPC 도입 배경 및 장점

### ✅ gRPC 장점

#### 1. **성능 향상**
- **HTTP/2 기반**: 멀티플렉싱, 헤더 압축
- **Protobuf 직렬화**: JSON 대비 3-10배 빠름, 크기 20-30% 감소
- **바이너리 프로토콜**: 파싱 오버헤드 최소화

```
JSON vs Protobuf (예상)
┌─────────────────┬──────────┬──────────┐
│     Metric      │   JSON   │ Protobuf │
├─────────────────┼──────────┼──────────┤
│ 직렬화 시간      │  100ms   │   30ms   │
│ 메시지 크기      │  1.5KB   │   1KB    │
│ 파싱 시간        │   80ms   │   20ms   │
└─────────────────┴──────────┴──────────┘
```

#### 2. **타입 안전성**
- Proto 파일로 계약 명시
- 컴파일 타임 타입 검증
- IDE 자동완성 지원

#### 3. **스트리밍 지원**
- Server Streaming: ML 서버 → 워커 (진행 상황)
- Client Streaming: 워커 → ML 서버 (배치 이미지)
- Bidirectional: 양방향 실시간 통신

#### 4. **언어 중립성**
- Proto 파일로 Python, Go, Java 등 자동 생성
- 향후 다른 언어로 확장 용이

---

## 마이그레이션 전략

### 🎯 단계별 마이그레이션 (Strangler Fig Pattern)

```
Phase 1: gRPC 인프라 구축 (1주)
    ↓
Phase 2: Dual Mode 운영 (2주)
    ├─ HTTP (기존)
    └─ gRPC (신규) - Feature Flag
    ↓
Phase 3: gRPC 기본 모드 (1주)
    ├─ gRPC (기본)
    └─ HTTP (폴백)
    ↓
Phase 4: HTTP 제거 (1주)
    └─ gRPC only
```

### 🔧 하위 호환성 유지 전략

```python
# 환경 변수로 통신 방식 선택
USE_GRPC = os.getenv("USE_GRPC", "false").lower() == "true"

if USE_GRPC:
    result = await grpc_client.extract_ocr(request)
else:
    result = await http_client.post("/ocr/extract", json=request)
```

---

## 구현 단계

### Step 1: 프로젝트 구조 준비

```bash
monorepo/
├── packages/
│   ├── shared/
│   │   └── shared/
│   │       └── grpc/
│   │           ├── protos/           # Proto 파일
│   │           │   ├── ocr.proto
│   │           │   ├── llm.proto
│   │           │   └── common.proto
│   │           ├── generated/        # 생성된 Python 코드
│   │           │   ├── ocr_pb2.py
│   │           │   ├── ocr_pb2_grpc.py
│   │           │   └── __init__.py
│   │           └── utils/           # gRPC 헬퍼
│   │               ├── server.py
│   │               └── client.py
│   │
│   ├── ml_server/
│   │   └── ml_app/
│   │       └── grpc_services/      # gRPC 서비스 구현
│   │           ├── __init__.py
│   │           ├── ocr_service.py
│   │           └── server.py
│   │
│   └── celery_worker/
│       └── tasks/
│           └── grpc_clients/       # gRPC 클라이언트
│               ├── __init__.py
│               └── ocr_client.py
```

### Step 2: 의존성 추가

```toml
# packages/shared/pyproject.toml
[project]
dependencies = [
    # ... 기존 의존성
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "protobuf>=4.25.0",
]

# packages/ml_server/pyproject.toml
[project]
dependencies = [
    # ... 기존 의존성
    "grpcio-reflection>=1.60.0",  # 서버 리플렉션
]
```

---

## Proto 파일 정의

### 📝 common.proto (공통 타입)

```protobuf
// packages/shared/shared/grpc/protos/common.proto
syntax = "proto3";

package common;

// 타임스탬프
message Timestamp {
    int64 seconds = 1;
    int32 nanos = 2;
}

// 바운딩 박스
message BoundingBox {
    repeated float coordinates = 1;  // [x1, y1, x2, y2, x3, y3, x4, y4]
}

// 메타데이터
message Metadata {
    map<string, string> data = 1;
}

// 에러 정보
message ErrorInfo {
    string code = 1;
    string message = 2;
    string details = 3;
}

// 상태 코드
enum Status {
    STATUS_UNKNOWN = 0;
    STATUS_SUCCESS = 1;
    STATUS_FAILURE = 2;
    STATUS_PENDING = 3;
    STATUS_IN_PROGRESS = 4;
}
```

### 📝 ocr.proto (OCR 서비스)

```protobuf
// packages/shared/shared/grpc/protos/ocr.proto
syntax = "proto3";

package ocr;

import "common.proto";

// ============================================
// OCR 추출 서비스
// ============================================

service OCRService {
    // 단일 이미지 OCR 추출
    rpc ExtractText(OCRRequest) returns (OCRResponse);

    // 배치 이미지 OCR 추출 (Server Streaming)
    rpc ExtractTextBatch(OCRBatchRequest) returns (stream OCRBatchProgress);

    // 상태 확인
    rpc CheckHealth(HealthCheckRequest) returns (HealthCheckResponse);
}

// ============================================
// 요청/응답 메시지
// ============================================

// OCR 요청
message OCRRequest {
    string public_image_path = 1;
    string private_image_path = 2;
    string language = 3;                    // 기본값: "korean"
    float confidence_threshold = 4;         // 기본값: 0.5
    bool use_angle_cls = 5;                 // 기본값: true
    common.Metadata options = 6;            // 추가 옵션
}

// OCR 응답
message OCRResponse {
    common.Status status = 1;
    string text = 2;                        // 추출된 전체 텍스트
    float overall_confidence = 3;           // 전체 신뢰도
    repeated TextBox text_boxes = 4;        // 텍스트 박스 리스트
    common.Metadata metadata = 5;           // 엔진 정보, 처리 시간 등
    common.ErrorInfo error = 6;             // 에러 정보 (실패 시)
}

// 텍스트 박스
message TextBox {
    string text = 1;
    float confidence = 2;
    common.BoundingBox bbox = 3;
}

// ============================================
// 배치 처리
// ============================================

// 배치 요청
message OCRBatchRequest {
    repeated ImagePath image_paths = 1;
    string language = 2;
    float confidence_threshold = 3;
    bool use_angle_cls = 4;
}

// 이미지 경로
message ImagePath {
    string public_path = 1;
    string private_path = 2;
}

// 배치 진행 상황 (스트리밍)
message OCRBatchProgress {
    string batch_id = 1;
    int32 total_images = 2;
    int32 processed_images = 3;
    OCRResponse current_result = 4;         // 현재 처리 결과
    float progress_percentage = 5;
}

// ============================================
// 헬스 체크
// ============================================

message HealthCheckRequest {
    string service_name = 1;
}

message HealthCheckResponse {
    common.Status status = 1;
    string engine_type = 2;                 // "easyocr" | "paddleocr" | "mock"
    bool model_loaded = 3;
    string version = 4;
}
```

### 📝 llm.proto (LLM 서비스)

```protobuf
// packages/shared/shared/grpc/protos/llm.proto
syntax = "proto3";

package llm;

import "common.proto";

service LLMService {
    // 텍스트 분석
    rpc AnalyzeText(LLMRequest) returns (LLMResponse);

    // 스트리밍 분석 (토큰별 반환)
    rpc AnalyzeTextStream(LLMRequest) returns (stream LLMStreamResponse);
}

message LLMRequest {
    string text = 1;
    string prompt = 2;
    common.Metadata options = 3;
}

message LLMResponse {
    common.Status status = 1;
    string analysis = 2;
    float confidence = 3;
    map<string, string> entities = 4;
    common.Metadata metadata = 5;
    common.ErrorInfo error = 6;
}

message LLMStreamResponse {
    string token = 1;
    bool is_complete = 2;
}
```

---

## ML Server 구현

### 📦 gRPC 서비스 구현

```python
# packages/ml_server/ml_app/grpc_services/ocr_service.py
"""OCR gRPC 서비스 구현"""

import grpc
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc, common_pb2
from shared.core.logging import get_logger
from ml_app.models.ocr_model import get_ocr_model
from shared.service.common_service import CommonService

logger = get_logger(__name__)


class OCRServiceServicer(ocr_pb2_grpc.OCRServiceServicer):
    """OCR gRPC 서비스"""

    def __init__(self):
        self.common_service = CommonService()
        logger.info("OCR gRPC 서비스 초기화 완료")

    async def ExtractText(
        self,
        request: ocr_pb2.OCRRequest,
        context: grpc.aio.ServicerContext
    ) -> ocr_pb2.OCRResponse:
        """단일 이미지 OCR 추출

        Args:
            request: OCR 요청
            context: gRPC 컨텍스트

        Returns:
            OCR 응답
        """
        try:
            logger.info(f"OCR 요청: {request.private_image_path}")

            # 1. 이미지 로드
            image_data = await self.common_service.load_image(
                request.private_image_path
            )

            # 2. OCR 모델 실행
            model = get_ocr_model(
                use_angle_cls=request.use_angle_cls,
                lang=request.language or "korean"
            )

            result = model.predict(
                image_data,
                confidence_threshold=request.confidence_threshold or 0.5
            )

            # 3. Protobuf 응답 생성
            response = ocr_pb2.OCRResponse(
                status=common_pb2.STATUS_SUCCESS,
                text=result.text,
                overall_confidence=result.confidence
            )

            # 4. 텍스트 박스 변환
            for box in result.text_boxes:
                text_box = ocr_pb2.TextBox(
                    text=box.text,
                    confidence=box.confidence,
                    bbox=common_pb2.BoundingBox(
                        coordinates=box.bbox  # [x1, y1, x2, y2, ...]
                    )
                )
                response.text_boxes.append(text_box)

            # 5. 메타데이터
            for key, value in result.metadata.items():
                response.metadata.data[key] = str(value)

            logger.info(f"OCR 완료: {len(response.text_boxes)} 텍스트 박스")
            return response

        except Exception as e:
            logger.error(f"OCR 실패: {str(e)}")

            # 에러 응답
            return ocr_pb2.OCRResponse(
                status=common_pb2.STATUS_FAILURE,
                error=common_pb2.ErrorInfo(
                    code="OCR_ERROR",
                    message=str(e),
                    details=type(e).__name__
                )
            )

    async def ExtractTextBatch(
        self,
        request: ocr_pb2.OCRBatchRequest,
        context: grpc.aio.ServicerContext
    ):
        """배치 이미지 OCR 추출 (Server Streaming)

        Args:
            request: 배치 요청
            context: gRPC 컨텍스트

        Yields:
            진행 상황 스트림
        """
        import uuid

        batch_id = str(uuid.uuid4())
        total = len(request.image_paths)

        logger.info(f"배치 OCR 시작: {batch_id}, {total}개 이미지")

        for idx, image_path in enumerate(request.image_paths):
            # 개별 OCR 요청 생성
            ocr_request = ocr_pb2.OCRRequest(
                public_image_path=image_path.public_path,
                private_image_path=image_path.private_path,
                language=request.language,
                confidence_threshold=request.confidence_threshold,
                use_angle_cls=request.use_angle_cls
            )

            # OCR 실행
            result = await self.ExtractText(ocr_request, context)

            # 진행 상황 전송
            progress = ocr_pb2.OCRBatchProgress(
                batch_id=batch_id,
                total_images=total,
                processed_images=idx + 1,
                current_result=result,
                progress_percentage=(idx + 1) / total * 100
            )

            yield progress

        logger.info(f"배치 OCR 완료: {batch_id}")

    async def CheckHealth(
        self,
        request: ocr_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext
    ) -> ocr_pb2.HealthCheckResponse:
        """헬스 체크

        Args:
            request: 헬스 체크 요청
            context: gRPC 컨텍스트

        Returns:
            헬스 체크 응답
        """
        from shared.config import settings

        model = get_ocr_model()

        return ocr_pb2.HealthCheckResponse(
            status=common_pb2.STATUS_SUCCESS if model.is_loaded else common_pb2.STATUS_FAILURE,
            engine_type=settings.OCR_ENGINE,
            model_loaded=model.is_loaded,
            version="1.0.0"
        )
```

### 🚀 gRPC 서버 시작

```python
# packages/ml_server/ml_app/grpc_services/server.py
"""gRPC 서버 관리"""

import asyncio
import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection

from shared.grpc.generated import ocr_pb2_grpc
from shared.core.logging import get_logger
from shared.config import settings
from .ocr_service import OCRServiceServicer

logger = get_logger(__name__)


async def serve():
    """gRPC 서버 시작"""

    # 1. 서버 생성
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
        ]
    )

    # 2. 서비스 등록
    ocr_pb2_grpc.add_OCRServiceServicer_to_server(
        OCRServiceServicer(),
        server
    )

    # 3. 리플렉션 활성화 (grpcurl 등 디버깅 도구 지원)
    SERVICE_NAMES = (
        ocr_pb2.DESCRIPTOR.services_by_name['OCRService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    # 4. 포트 바인딩
    grpc_port = settings.GRPC_PORT or 50051
    server.add_insecure_port(f'[::]:{grpc_port}')

    # 5. 서버 시작
    await server.start()
    logger.info(f"🚀 gRPC 서버 시작: 포트 {grpc_port}")

    # 6. 종료 대기
    await server.wait_for_termination()


def start_grpc_server():
    """gRPC 서버 시작 (블로킹)"""
    asyncio.run(serve())
```

### 🔗 FastAPI와 통합

```python
# packages/ml_server/ml_app/main.py
"""ML 서버 메인 애플리케이션"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from shared.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""

    # 시작 시
    logger.info("ML 서버 시작")

    # gRPC 서버를 별도 태스크로 시작
    from ml_app.grpc_services.server import serve
    grpc_task = asyncio.create_task(serve())

    yield

    # 종료 시
    logger.info("ML 서버 종료")
    grpc_task.cancel()
    try:
        await grpc_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

# REST API 라우터 등록 (기존 유지)
from ml_app.domains.ocr.controllers import ocr_controller
app.include_router(ocr_controller.router)
```

---

## Celery Worker 구현

### 📡 gRPC 클라이언트

```python
# packages/celery_worker/tasks/grpc_clients/ocr_client.py
"""OCR gRPC 클라이언트"""

import grpc
from typing import Optional
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc
from shared.core.logging import get_logger
from shared.config import settings

logger = get_logger(__name__)


class OCRGrpcClient:
    """OCR gRPC 클라이언트 (싱글톤)"""

    def __init__(self, server_address: Optional[str] = None):
        self.server_address = server_address or settings.ML_SERVER_GRPC_ADDRESS
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[ocr_pb2_grpc.OCRServiceStub] = None

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.close()

    async def connect(self):
        """채널 연결"""
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(
                self.server_address,
                options=[
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 10000),
                ]
            )
            self._stub = ocr_pb2_grpc.OCRServiceStub(self._channel)
            logger.info(f"gRPC 채널 연결: {self.server_address}")

    async def close(self):
        """채널 종료"""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("gRPC 채널 종료")

    async def extract_text(
        self,
        public_image_path: str,
        private_image_path: str,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
        timeout: float = 300.0
    ) -> ocr_pb2.OCRResponse:
        """OCR 텍스트 추출

        Args:
            public_image_path: 공개 이미지 경로
            private_image_path: 비공개 이미지 경로
            language: 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 각도 분류 사용 여부
            timeout: 타임아웃 (초)

        Returns:
            OCR 응답

        Raises:
            grpc.RpcError: gRPC 통신 오류
        """
        if not self._stub:
            await self.connect()

        # 요청 생성
        request = ocr_pb2.OCRRequest(
            public_image_path=public_image_path,
            private_image_path=private_image_path,
            language=language,
            confidence_threshold=confidence_threshold,
            use_angle_cls=use_angle_cls
        )

        # gRPC 호출
        try:
            response = await self._stub.ExtractText(
                request,
                timeout=timeout
            )

            logger.info(
                f"gRPC OCR 완료: {len(response.text_boxes)} 텍스트 박스, "
                f"신뢰도: {response.overall_confidence:.2f}"
            )

            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC 오류: {e.code()}, {e.details()}")
            raise

    async def check_health(self) -> ocr_pb2.HealthCheckResponse:
        """헬스 체크

        Returns:
            헬스 체크 응답
        """
        if not self._stub:
            await self.connect()

        request = ocr_pb2.HealthCheckRequest(service_name="OCRService")
        return await self._stub.CheckHealth(request)


# 싱글톤 인스턴스
_grpc_client: Optional[OCRGrpcClient] = None


def get_ocr_grpc_client() -> OCRGrpcClient:
    """OCR gRPC 클라이언트 가져오기 (싱글톤)"""
    global _grpc_client
    if _grpc_client is None:
        _grpc_client = OCRGrpcClient()
    return _grpc_client
```

### 🔄 OCRStage 수정 (Dual Mode)

```python
# packages/celery_worker/tasks/stages/ocr_stage.py
"""OCR 처리 스테이지 (HTTP + gRPC 지원)"""

import os
import httpx
import grpc
from shared.core.logging import get_logger
from shared.pipeline.context import OCRResult, PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.pipeline.stage import PipelineStage
from shared.grpc.generated import common_pb2

logger = get_logger(__name__)

# Feature Flag
USE_GRPC = os.getenv("USE_GRPC", "false").lower() == "true"


class OCRStage(PipelineStage):
    """OCR 처리 스테이지 (HTTP/gRPC 듀얼 모드)"""

    def __init__(self):
        super().__init__()
        self.ml_server_url = settings.MODEL_SERVER_URL

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """ML 서버에 OCR 요청 (HTTP 또는 gRPC)"""

        if USE_GRPC:
            return await self._execute_grpc(context)
        else:
            return await self._execute_http(context)

    async def _execute_http(self, context: PipelineContext) -> PipelineContext:
        """HTTP로 OCR 실행 (기존 방식)"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.ml_server_url}/ocr/extract",
                    json={
                        "public_image_path": context.public_file_path,
                        "private_image_path": context.input_file_path,
                    },
                )
                response.raise_for_status()

            ocr_data = response.json()

            context.ocr_result = OCRResult(
                text=ocr_data.get("text", ""),
                confidence=ocr_data.get("confidence", 0.0),
                bbox=ocr_data.get("text_boxes"),
                metadata=ocr_data.get("metadata", {}),
            )

            logger.info("HTTP OCR 완료")
            return context

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise RetryableError("OCRStage", f"HTTP error: {str(e)}") from e

    async def _execute_grpc(self, context: PipelineContext) -> PipelineContext:
        """gRPC로 OCR 실행 (신규 방식)"""
        from tasks.grpc_clients.ocr_client import get_ocr_grpc_client

        try:
            # gRPC 클라이언트 가져오기
            client = get_ocr_grpc_client()

            # gRPC 호출
            response = await client.extract_text(
                public_image_path=context.public_file_path,
                private_image_path=context.input_file_path,
                language="korean",
                confidence_threshold=0.5,
                use_angle_cls=True
            )

            # 성공 여부 확인
            if response.status != common_pb2.STATUS_SUCCESS:
                error_msg = response.error.message if response.error else "Unknown error"
                raise ValueError(f"OCR failed: {error_msg}")

            # Protobuf → OCRResult 변환
            text_boxes = [
                {
                    "text": box.text,
                    "confidence": box.confidence,
                    "bbox": list(box.bbox.coordinates)
                }
                for box in response.text_boxes
            ]

            context.ocr_result = OCRResult(
                text=response.text,
                confidence=response.overall_confidence,
                bbox=text_boxes,
                metadata=dict(response.metadata.data)
            )

            logger.info("gRPC OCR 완료")
            return context

        except grpc.RpcError as e:
            # gRPC 오류 처리
            if e.code() in [grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED]:
                # 재시도 가능한 오류
                raise RetryableError("OCRStage", f"gRPC error: {e.details()}") from e
            else:
                # 재시도 불가능한 오류
                raise ValueError(f"gRPC OCR failed: {e.details()}") from e
```

---

## 배포 및 전환 전략

### 📋 Proto 파일 컴파일

```bash
# packages/shared/Makefile
.PHONY: generate-grpc
generate-grpc:
	python -m grpc_tools.protoc \
		-I./shared/grpc/protos \
		--python_out=./shared/grpc/generated \
		--grpc_python_out=./shared/grpc/generated \
		--pyi_out=./shared/grpc/generated \
		./shared/grpc/protos/*.proto

	# __init__.py 생성
	touch ./shared/grpc/generated/__init__.py

	echo "✅ gRPC 코드 생성 완료"
```

```bash
# 실행
cd packages/shared
make generate-grpc
```

### 🚀 환경 변수 설정

```bash
# .env
# ML Server
GRPC_PORT=50051

# Celery Worker
ML_SERVER_GRPC_ADDRESS=ml_server:50051  # Docker 환경
USE_GRPC=true  # gRPC 활성화
```

### 🐳 Docker Compose 수정

```yaml
# docker-compose.yml
services:
  ml_server:
    ports:
      - "8001:8000"  # FastAPI (HTTP)
      - "50051:50051"  # gRPC
    environment:
      - GRPC_PORT=50051

  celery_worker:
    environment:
      - ML_SERVER_GRPC_ADDRESS=ml_server:50051
      - USE_GRPC=true
    depends_on:
      - ml_server
```

### 📊 단계별 전환

#### Phase 1: 개발 환경에서 테스트
```bash
# gRPC 활성화
export USE_GRPC=true

# 테스트 실행
pytest tests/test_grpc_ocr.py -v
```

#### Phase 2: 카나리 배포 (10% 트래픽)
```python
# 확률 기반 분기
import random

USE_GRPC = random.random() < 0.1  # 10% 트래픽만 gRPC
```

#### Phase 3: 점진적 증가
```
Week 1: 10% gRPC
Week 2: 50% gRPC
Week 3: 90% gRPC
Week 4: 100% gRPC (HTTP는 폴백만)
```

---

## 성능 벤치마크

### 🎯 측정 지표

```python
# packages/shared/shared/utils/benchmark.py
"""성능 벤치마크 유틸리티"""

import time
import asyncio
from typing import Callable
from shared.core.logging import get_logger

logger = get_logger(__name__)


async def benchmark_ocr(
    method: str,  # "http" or "grpc"
    iterations: int = 100,
    image_path: str = "test.jpg"
):
    """OCR 성능 벤치마크

    Args:
        method: 통신 방식
        iterations: 반복 횟수
        image_path: 테스트 이미지 경로
    """

    latencies = []

    for i in range(iterations):
        start = time.time()

        if method == "http":
            # HTTP 호출
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://ml_server:8000/ocr/extract",
                    json={"private_image_path": image_path}
                )
        else:
            # gRPC 호출
            from tasks.grpc_clients.ocr_client import get_ocr_grpc_client
            client = get_ocr_grpc_client()
            await client.extract_text(
                public_image_path=image_path,
                private_image_path=image_path
            )

        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)

        if (i + 1) % 10 == 0:
            logger.info(f"진행: {i + 1}/{iterations}")

    # 통계
    avg_latency = sum(latencies) / len(latencies)
    p50 = sorted(latencies)[len(latencies) // 2]
    p95 = sorted(latencies)[int(len(latencies) * 0.95)]
    p99 = sorted(latencies)[int(len(latencies) * 0.99)]

    logger.info(f"""
    === {method.upper()} 벤치마크 결과 ===
    반복: {iterations}
    평균 지연: {avg_latency:.2f}ms
    P50: {p50:.2f}ms
    P95: {p95:.2f}ms
    P99: {p99:.2f}ms
    """)

    return {
        "method": method,
        "avg": avg_latency,
        "p50": p50,
        "p95": p95,
        "p99": p99
    }
```

### 📈 예상 성능 개선

```
┌─────────────────┬──────────┬──────────┬─────────┐
│     Metric      │   HTTP   │   gRPC   │ 개선율   │
├─────────────────┼──────────┼──────────┼─────────┤
│ 평균 지연 (ms)   │   150    │    90    │  -40%   │
│ P95 지연 (ms)    │   250    │   140    │  -44%   │
│ 처리량 (req/s)   │   200    │   350    │  +75%   │
│ 메시지 크기 (KB) │    2.5   │    1.8   │  -28%   │
│ CPU 사용률 (%)   │    45    │    35    │  -22%   │
└─────────────────┴──────────┴──────────┴─────────┘
```

---

## 문제 해결 가이드

### ❌ 문제 1: Proto 컴파일 오류

**증상**:
```
ModuleNotFoundError: No module named 'shared.grpc.generated.ocr_pb2'
```

**해결**:
```bash
# Proto 재컴파일
cd packages/shared
make generate-grpc

# 생성 확인
ls shared/grpc/generated/
# → ocr_pb2.py, ocr_pb2_grpc.py 존재해야 함
```

### ❌ 문제 2: gRPC 채널 연결 실패

**증상**:
```
grpc.RpcError: StatusCode.UNAVAILABLE, failed to connect to all addresses
```

**해결**:
```python
# 1. ML Server gRPC 서버 확인
curl http://ml_server:8000/healthy  # FastAPI는 작동하는지

# 2. 포트 확인
docker ps | grep ml_server
# → 50051 포트 노출 확인

# 3. 주소 확인
# ml_server:50051 (Docker)
# localhost:50051 (로컬)
```

### ❌ 문제 3: 메시지 크기 초과

**증상**:
```
grpc.RpcError: StatusCode.RESOURCE_EXHAUSTED, Received message larger than max
```

**해결**:
```python
# 클라이언트/서버 모두 메시지 크기 증가
options=[
    ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
]
```

### ❌ 문제 4: 타임아웃

**증상**:
```
grpc.RpcError: StatusCode.DEADLINE_EXCEEDED
```

**해결**:
```python
# 타임아웃 증가
await stub.ExtractText(request, timeout=600.0)  # 10분

# Keep-alive 설정
options=[
    ('grpc.keepalive_time_ms', 10000),
    ('grpc.keepalive_timeout_ms', 5000),
]
```

---

## 테스트 전략

### 🧪 단위 테스트

```python
# tests/test_grpc_ocr.py
"""gRPC OCR 테스트"""

import pytest
from shared.grpc.generated import ocr_pb2, common_pb2
from ml_app.grpc_services.ocr_service import OCRServiceServicer


@pytest.mark.asyncio
async def test_extract_text_success():
    """OCR 추출 성공 테스트"""

    # Given
    servicer = OCRServiceServicer()
    request = ocr_pb2.OCRRequest(
        public_image_path="test.jpg",
        private_image_path="/data/test.jpg",
        language="korean",
        confidence_threshold=0.5,
        use_angle_cls=True
    )

    # When
    response = await servicer.ExtractText(request, None)

    # Then
    assert response.status == common_pb2.STATUS_SUCCESS
    assert len(response.text) > 0
    assert response.overall_confidence > 0


@pytest.mark.asyncio
async def test_extract_text_failure():
    """OCR 추출 실패 테스트 (잘못된 경로)"""

    # Given
    servicer = OCRServiceServicer()
    request = ocr_pb2.OCRRequest(
        private_image_path="/invalid/path.jpg"
    )

    # When
    response = await servicer.ExtractText(request, None)

    # Then
    assert response.status == common_pb2.STATUS_FAILURE
    assert response.error.code == "OCR_ERROR"
```

### 🔬 통합 테스트

```python
# tests/integration/test_grpc_integration.py
"""gRPC 통합 테스트"""

import pytest
import grpc
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc


@pytest.mark.asyncio
async def test_end_to_end_grpc():
    """End-to-End gRPC 테스트"""

    # Given: gRPC 채널 연결
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = ocr_pb2_grpc.OCRServiceStub(channel)

        request = ocr_pb2.OCRRequest(
            private_image_path="/data/sample.jpg"
        )

        # When: OCR 실행
        response = await stub.ExtractText(request)

        # Then: 결과 검증
        assert response.status == ocr_pb2.STATUS_SUCCESS
        assert len(response.text_boxes) > 0
```

---

## 마이그레이션 체크리스트

### ✅ Phase 1: 준비 (1주)
- [ ] Proto 파일 정의 완료
- [ ] `grpcio`, `grpcio-tools` 설치
- [ ] Proto 컴파일 스크립트 작성
- [ ] gRPC 서비스 스켈레톤 구현
- [ ] 단위 테스트 작성

### ✅ Phase 2: 구현 (2주)
- [ ] ML Server gRPC 서비스 구현
- [ ] Celery Worker gRPC 클라이언트 구현
- [ ] Dual Mode 지원 (Feature Flag)
- [ ] 에러 핸들링 및 재시도 로직
- [ ] 로깅 및 모니터링 추가

### ✅ Phase 3: 테스트 (1주)
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 성능 벤치마크 완료
- [ ] 부하 테스트 (100+ 동시 요청)
- [ ] 장애 시나리오 테스트

### ✅ Phase 4: 배포 (1주)
- [ ] 개발 환경 배포
- [ ] 스테이징 환경 테스트
- [ ] 카나리 배포 (10% 트래픽)
- [ ] 점진적 증가 (50% → 90% → 100%)
- [ ] HTTP 폴백 제거

---

## 참고 자료

### 📚 공식 문서
- [gRPC Python Quickstart](https://grpc.io/docs/languages/python/quickstart/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers/docs/pythontutorial)
- [gRPC Performance Best Practices](https://grpc.io/docs/guides/performance/)

### 🛠️ 디버깅 도구
```bash
# grpcurl 설치 (macOS)
brew install grpcurl

# 서비스 목록 확인
grpcurl -plaintext localhost:50051 list

# 메서드 호출
grpcurl -plaintext -d '{"private_image_path": "/data/test.jpg"}' \
    localhost:50051 ocr.OCRService/ExtractText
```

### 📊 모니터링
```python
# Prometheus 메트릭 추가
from prometheus_client import Counter, Histogram

grpc_requests_total = Counter(
    'grpc_requests_total',
    'Total gRPC requests',
    ['method', 'status']
)

grpc_request_duration = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request duration',
    ['method']
)
```

---

## 결론

gRPC 마이그레이션을 통해 다음과 같은 개선을 기대할 수 있습니다:

1. **성능**: 40-50% 지연 시간 감소
2. **처리량**: 70-100% 증가
3. **타입 안전성**: 컴파일 타임 검증
4. **확장성**: 스트리밍, 양방향 통신 지원

단계적 마이그레이션(Strangler Fig Pattern)을 통해 **리스크를 최소화**하면서 안정적으로 전환할 수 있습니다.
