# gRPC Generated 파일 완벽 가이드

> gRPC를 처음 사용하는 개발자를 위한 generated 폴더 파일 설명서

---

## 📚 목차
1. [gRPC 기본 개념](#grpc-기본-개념)
2. [Proto 파일과 Generated 파일의 관계](#proto-파일과-generated-파일의-관계)
3. [각 파일의 역할 상세 설명](#각-파일의-역할-상세-설명)
4. [실제 사용 예제](#실제-사용-예제)
5. [문제 해결 가이드](#문제-해결-가이드)

---

## gRPC 기본 개념

### gRPC란?
gRPC는 Google이 만든 **고성능 RPC(Remote Procedure Call) 프레임워크**입니다.

**일반 HTTP API vs gRPC 비교:**

```python
# HTTP REST API 방식
response = requests.post("http://ml-server/api/ocr",
    json={"image_path": "/data/test.jpg"})
result = response.json()

# gRPC 방식
response = await stub.ExtractText(
    OCRRequest(private_image_path="/data/test.jpg")
)
# 타입 안전성과 성능이 뛰어남!
```

**gRPC의 장점:**
- ✅ **타입 안전성**: 컴파일 시점에 타입 체크
- ✅ **고성능**: HTTP/2 기반, 바이너리 프로토콜 사용
- ✅ **양방향 스트리밍**: 실시간 데이터 전송 가능
- ✅ **다양한 언어 지원**: Python, Go, Java 등

---

## Proto 파일과 Generated 파일의 관계

### 전체 흐름

```
┌─────────────────┐
│  .proto 파일    │  ← 사람이 작성 (서비스 정의)
│  (IDL: 인터페이스│
│   정의 언어)     │
└────────┬────────┘
         │
         │ protoc 컴파일러
         │ (코드 생성)
         ▼
┌─────────────────┐
│ generated/      │  ← 자동 생성 (수정 금지!)
│  *_pb2.py       │     Python 코드
│  *_pb2.pyi      │     타입 힌트
│  *_pb2_grpc.py  │     gRPC 서비스
└─────────────────┘
```

### Proto 파일 예제

**packages/shared/shared/grpc/protos/ocr.proto:**
```protobuf
// 서비스 정의 (사람이 작성)
service OCRService {
  rpc ExtractText(OCRRequest) returns (OCRResponse);
  rpc CheckHealth(HealthCheckRequest) returns (HealthCheckResponse);
}

// 메시지 정의 (데이터 구조)
message OCRRequest {
  string private_image_path = 1;
  string language = 2;
  float confidence_threshold = 3;
}
```

**컴파일 명령:**
```bash
python -m grpc_tools.protoc \
  -I packages/shared/shared/grpc/protos \
  --python_out=packages/shared/shared/grpc/generated \
  --grpc_python_out=packages/shared/shared/grpc/generated \
  --pyi_out=packages/shared/shared/grpc/generated \
  ocr.proto common.proto
```

---

## 각 파일의 역할 상세 설명

### 📁 packages/shared/shared/grpc/generated/

```
generated/
├── __init__.py              # 모듈 초기화
├── common_pb2.py           # 공통 메시지 정의 (Python 클래스)
├── common_pb2.pyi          # 공통 메시지 타입 힌트
├── common_pb2_grpc.py      # 공통 gRPC 서비스 (비어있음)
├── ocr_pb2.py              # OCR 메시지 정의 (Python 클래스)
├── ocr_pb2.pyi             # OCR 메시지 타입 힌트
└── ocr_pb2_grpc.py         # OCR gRPC 서비스 (Stub & Servicer)
```

---

### 1️⃣ `*_pb2.py` - 메시지 클래스 정의

**역할:** Proto 파일의 `message`를 Python 클래스로 변환

**예시: ocr_pb2.py**
```python
# Proto 정의
message OCRRequest {
  string private_image_path = 1;
  string language = 2;
}

# ↓ 자동 생성된 Python 클래스 ↓
class OCRRequest:
    private_image_path: str
    language: str

    def __init__(self,
                 private_image_path: str = "",
                 language: str = ""):
        ...
```

**사용 예제:**
```python
from shared.grpc.generated import ocr_pb2

# 요청 객체 생성
request = ocr_pb2.OCRRequest(
    private_image_path="/data/test.jpg",
    language="korean",
    confidence_threshold=0.5
)

# 속성 접근
print(request.private_image_path)  # "/data/test.jpg"
```

**주요 메시지 타입:**

#### common_pb2.py
- `Status` (Enum): `STATUS_SUCCESS`, `STATUS_FAILURE` 등
- `BoundingBox`: OCR 텍스트 박스 좌표
- `Metadata`: 키-값 메타데이터
- `ErrorInfo`: 에러 정보

#### ocr_pb2.py
- `OCRRequest`: OCR 요청 데이터
- `OCRResponse`: OCR 응답 데이터
- `TextBox`: 개별 텍스트 박스
- `OCRBatchRequest`: 배치 OCR 요청
- `HealthCheckRequest/Response`: 헬스 체크

---

### 2️⃣ `*_pb2.pyi` - 타입 힌트 파일

**역할:** IDE와 타입 체커(mypy, pylance)를 위한 타입 정보 제공

**왜 필요한가?**
- `*_pb2.py`는 자동 생성되어 타입 정보가 불완전
- `.pyi` 파일이 정확한 타입 정보를 제공

**예시: ocr_pb2.pyi**
```python
from typing import Iterable

class OCRRequest:
    private_image_path: str
    language: str
    confidence_threshold: float

    def __init__(self, *,
                 private_image_path: str = ...,
                 language: str = ...,
                 confidence_threshold: float = ...) -> None: ...

class OCRResponse:
    status: int  # common_pb2.Status enum
    text: str
    overall_confidence: float
    text_boxes: list[TextBox]

    def __init__(self, *,
                 status: int = ...,
                 text: str = ...,
                 text_boxes: Iterable[TextBox] = ...) -> None: ...
```

**효과:**
```python
# IDE에서 자동완성 지원
request = ocr_pb2.OCRRequest(
    private_image_path="/test.jpg",  # ← 자동완성!
    # language=  ← 여기서도 자동완성!
)

# 타입 체크
request.private_image_path = 123  # ❌ 타입 에러! (str 필요)
```

---

### 3️⃣ `*_pb2_grpc.py` - gRPC 서비스 구현

**역할:** 클라이언트(Stub)와 서버(Servicer) 인터페이스 제공

#### A. 클라이언트용: `OCRServiceStub`

**역할:** 서버에 요청을 보내는 클라이언트 클래스

```python
class OCRServiceStub:
    """클라이언트가 사용하는 스텁"""

    def __init__(self, channel):
        # ExtractText 메서드 초기화
        self.ExtractText = channel.unary_unary(
            '/ocr.OCRService/ExtractText',
            request_serializer=ocr_pb2.OCRRequest.SerializeToString,
            response_deserializer=ocr_pb2.OCRResponse.FromString,
        )

        # CheckHealth 메서드 초기화
        self.CheckHealth = channel.unary_unary(
            '/ocr.OCRService/CheckHealth',
            ...
        )
```

**클라이언트 사용 예제:**
```python
import grpc
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc

async def call_ocr_service():
    # 1. gRPC 채널 생성 (서버 연결)
    channel = grpc.aio.insecure_channel('localhost:50051')

    # 2. Stub 생성 (클라이언트 객체)
    stub = ocr_pb2_grpc.OCRServiceStub(channel)

    # 3. 요청 객체 생성
    request = ocr_pb2.OCRRequest(
        private_image_path="/data/test.jpg",
        language="korean"
    )

    # 4. 서버 호출 (마치 로컬 함수처럼!)
    response = await stub.ExtractText(request)

    # 5. 응답 사용
    print(f"추출된 텍스트: {response.text}")
    print(f"신뢰도: {response.overall_confidence}")

    await channel.close()
```

#### B. 서버용: `OCRServiceServicer`

**역할:** 서버가 구현해야 할 인터페이스 정의

```python
class OCRServiceServicer:
    """서버가 구현해야 할 기본 클래스"""

    def ExtractText(self, request, context):
        """기본 구현 (NotImplementedError 발생)"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        raise NotImplementedError('Method not implemented!')

    def CheckHealth(self, request, context):
        """기본 구현 (NotImplementedError 발생)"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        raise NotImplementedError('Method not implemented!')
```

**서버 구현 예제:**
```python
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc, common_pb2

class OCRServiceServicer(ocr_pb2_grpc.OCRServiceServicer):
    """실제 서버 구현"""

    async def extract_text(self, request, context):
        """ExtractText 메서드 구현"""
        # 1. 요청 데이터 사용
        image_path = request.private_image_path

        # 2. OCR 처리 (실제 비즈니스 로직)
        result = await process_ocr(image_path)

        # 3. 응답 객체 생성
        response = ocr_pb2.OCRResponse(
            status=common_pb2.STATUS_SUCCESS,
            text=result.text,
            overall_confidence=result.confidence
        )

        return response

    async def check_health(self, request, context):
        """CheckHealth 메서드 구현"""
        return ocr_pb2.HealthCheckResponse(
            status=common_pb2.STATUS_SUCCESS,
            engine_type="easyocr",
            model_loaded=True,
            version="1.0.0"
        )
```

#### C. 서버 등록 함수: `add_OCRServiceServicer_to_server`

**역할:** 서버에 구현한 Servicer를 등록

```python
def add_OCRServiceServicer_to_server(servicer, server):
    """서버에 OCR 서비스 등록"""
    rpc_method_handlers = {
        'ExtractText': grpc.unary_unary_rpc_method_handler(
            servicer.extract_text,  # ← 실제 구현 메서드
            request_deserializer=ocr_pb2.OCRRequest.FromString,
            response_serializer=ocr_pb2.OCRResponse.SerializeToString,
        ),
        'CheckHealth': grpc.unary_unary_rpc_method_handler(
            servicer.check_health,
            ...
        ),
    }

    # 서버에 핸들러 등록
    generic_handler = grpc.method_handlers_generic_handler(
        'ocr.OCRService', rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
```

**서버 시작 예제:**
```python
import grpc
from shared.grpc.generated import ocr_pb2_grpc

async def serve():
    # 1. gRPC 서버 생성
    server = grpc.aio.server()

    # 2. Servicer 등록
    ocr_pb2_grpc.add_OCRServiceServicer_to_server(
        OCRServiceServicer(),  # ← 우리가 구현한 클래스
        server
    )

    # 3. 포트 바인딩
    server.add_insecure_port('[::]:50051')

    # 4. 서버 시작
    await server.start()
    await server.wait_for_termination()
```

---

### 4️⃣ `__init__.py` - 모듈 초기화

**역할:** generated 폴더를 Python 패키지로 만들고 편리한 import 제공

```python
"""gRPC generated code for OCR service."""
from . import common_pb2
from . import ocr_pb2
from . import ocr_pb2_grpc

__all__ = [
    "common_pb2",
    "ocr_pb2",
    "ocr_pb2_grpc",
]
```

**효과:**
```python
# __init__.py 덕분에 이렇게 import 가능
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc

# 없다면 이렇게 해야 함
from shared.grpc.generated.ocr_pb2 import OCRRequest
from shared.grpc.generated.ocr_pb2_grpc import OCRServiceStub
```

---

## 실제 사용 예제

### 전체 플로우: 클라이언트 → 서버

```python
# ==========================================
# 서버 측 (ML Server)
# ==========================================
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc, common_pb2

class OCRServiceServicer(ocr_pb2_grpc.OCRServiceServicer):
    async def extract_text(self, request, context):
        # 1. 요청에서 데이터 추출
        image_path = request.private_image_path
        language = request.language

        # 2. OCR 처리
        ocr_model = get_ocr_model(lang=language)
        result = ocr_model.predict(image_path)

        # 3. 응답 생성
        response = ocr_pb2.OCRResponse(
            status=common_pb2.STATUS_SUCCESS,
            text=result.full_text,
            overall_confidence=result.avg_confidence
        )

        # 4. 텍스트 박스 추가
        for box in result.boxes:
            text_box = ocr_pb2.TextBox(
                text=box.text,
                confidence=box.confidence,
                bbox=common_pb2.BoundingBox(
                    coordinates=box.coordinates
                )
            )
            response.text_boxes.append(text_box)

        return response

# 서버 시작
async def serve():
    server = grpc.aio.server()
    ocr_pb2_grpc.add_OCRServiceServicer_to_server(
        OCRServiceServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()

# ==========================================
# 클라이언트 측 (Celery Worker)
# ==========================================
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc

async def call_ml_server():
    # 1. 서버 연결
    channel = grpc.aio.insecure_channel('localhost:50051')
    stub = ocr_pb2_grpc.OCRServiceStub(channel)

    # 2. 요청 생성
    request = ocr_pb2.OCRRequest(
        private_image_path="/data/invoice.jpg",
        language="korean",
        confidence_threshold=0.7
    )

    # 3. gRPC 호출
    response = await stub.ExtractText(request)

    # 4. 응답 처리
    if response.status == common_pb2.STATUS_SUCCESS:
        print(f"✅ OCR 성공!")
        print(f"텍스트: {response.text}")
        print(f"신뢰도: {response.overall_confidence:.2%}")

        for i, box in enumerate(response.text_boxes):
            print(f"  [{i+1}] {box.text} (신뢰도: {box.confidence:.2f})")
    else:
        print(f"❌ OCR 실패: {response.error.message}")

    await channel.close()
```

---

## 문제 해결 가이드

### 1. "Module not found" 에러

```python
# ❌ 에러
ModuleNotFoundError: No module named 'shared.grpc.generated'
```

**해결책:**
```bash
# Proto 파일 재컴파일
cd packages/shared
python -m grpc_tools.protoc \
  -I shared/grpc/protos \
  --python_out=shared/grpc/generated \
  --grpc_python_out=shared/grpc/generated \
  --pyi_out=shared/grpc/generated \
  ocr.proto common.proto
```

### 2. "Method not implemented" 에러

```python
# ❌ 에러
grpc.RpcError: StatusCode.UNIMPLEMENTED
```

**원인:** Servicer 클래스에서 메서드를 구현하지 않음

**해결책:**
```python
# ✅ 올바른 구현
class OCRServiceServicer(ocr_pb2_grpc.OCRServiceServicer):
    async def extract_text(self, request, context):  # ← 구현 필수!
        return ocr_pb2.OCRResponse(...)
```

### 3. Pylance/타입 체크 에러

**증상:** IDE에서 빨간 줄 표시, 하지만 코드는 정상 작동

**해결책 1: pyrightconfig.json에 제외 추가**
```json
{
  "exclude": [
    "**/grpc/generated/**"
  ]
}
```

**해결책 2: type: ignore 주석**
```python
from shared.grpc.generated import ocr_pb2  # type: ignore
```

### 4. Import 순환 참조 에러

```python
# ❌ 에러
ImportError: cannot import name 'common_pb2'
```

**해결책:** generated 폴더의 상대 import 확인
```python
# ocr_pb2.py에서
from . import common_pb2  # ← 상대 import 사용
```

### 5. AttributeError: 'Server' object has no attribute 'add_registered_method_handlers'

**원인:** grpcio 버전 불일치

**해결책:**
```python
# ocr_pb2_grpc.py에서 해당 줄 주석 처리
def add_OCRServiceServicer_to_server(servicer, server):
    ...
    server.add_generic_rpc_handlers((generic_handler,))
    # server.add_registered_method_handlers(...)  # ← 주석 처리
```

---

## 요약

### 각 파일의 핵심 역할

| 파일 | 역할 | 사용자 |
|------|------|--------|
| `*_pb2.py` | 메시지 클래스 (데이터 구조) | 클라이언트 & 서버 |
| `*_pb2.pyi` | 타입 힌트 (IDE 지원) | 개발자 (IDE) |
| `*_pb2_grpc.py` | 서비스 인터페이스 | 클라이언트 & 서버 |
| `__init__.py` | 패키지 초기화 | 모두 |

### 개발 워크플로우

```
1. Proto 파일 작성 (.proto)
   ↓
2. 코드 생성 (protoc 컴파일)
   ↓
3. 서버 구현 (Servicer 상속)
   ↓
4. 클라이언트 구현 (Stub 사용)
   ↓
5. 테스트 및 디버깅
```

### 주의사항

⚠️ **절대 수정하지 말 것:**
- `*_pb2.py`
- `*_pb2.pyi`
- `*_pb2_grpc.py` (특별한 이유가 없으면)

✅ **수정 가능:**
- `__init__.py` (import 추가 등)
- 서버 구현 클래스 (별도 파일)

🔄 **Proto 수정 시:**
1. `.proto` 파일 수정
2. `protoc` 재컴파일
3. 서버/클라이언트 코드 업데이트

---

## 추가 학습 자료

- [gRPC Python 공식 문서](https://grpc.io/docs/languages/python/)
- [Protocol Buffers 가이드](https://protobuf.dev/getting-started/pythontutorial/)
- [프로젝트 내 gRPC 설정 가이드](./grpc-setup-guide.md)
- [gRPC 마이그레이션 가이드](./grpc-migration-guide.md)

---

**문서 작성일:** 2025-11-08
**작성자:** Claude Code
