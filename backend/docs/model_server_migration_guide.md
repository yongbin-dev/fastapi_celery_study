# 모델 서버 분리 마이그레이션 가이드

## 📌 개요

현재 도메인별 컨테이너 분리 구조에서 **독립적인 모델 서버 구조**로 전환하는 가이드입니다.

### 현재 구조
```
nginx → app-ocr-gpu (FastAPI + OCR 모델)
     → app-llm (FastAPI + LLM 모델)
```

### 목표 구조
```
nginx → app-base (FastAPI 비즈니스 로직)
           ↓ HTTP
        ocr-model-server (OCR 모델 전용)
        llm-model-server (LLM 모델 전용)
```

---

## 🎯 마이그레이션 3단계

### 1단계: OCR 모델 서버 생성

#### 디렉토리 구조 생성
```bash
mkdir -p model_servers/ocr_server/{utils,models}
```

```
model_servers/
└── ocr_server/
    ├── server.py           # FastAPI 서버
    ├── Dockerfile          # Docker 이미지
    ├── requirements.txt    # 의존성 (선택)
    ├── utils/
    │   ├── vram_manager.py # VRAM 관리
    │   └── gpu_monitor.py  # GPU 모니터링
    └── models/
        └── ocr_model.py    # 모델 래퍼
```

#### server.py 작성

```python
# model_servers/ocr_server/server.py
from fastapi import FastAPI, File, UploadFile
import sys

# 기존 앱 코드 재사용
sys.path.append('/app')
from app.domains.ocr.services.ocr_model import get_ocr_model

app = FastAPI(title="OCR Model Server", version="1.0.0")

@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    """
    OCR 예측 엔드포인트

    Args:
        image: 이미지 파일

    Returns:
        OCR 결과 (text_boxes, full_text, status)
    """
    image_data = await image.read()

    # 기존 OCR 모델 사용
    model = get_ocr_model()
    result = model.predict(image_data, confidence_threshold=0.5)

    return result


@app.get("/health")
async def health():
    """헬스 체크"""
    model = get_ocr_model()
    return {
        "status": "healthy",
        "model_loaded": model.is_loaded
    }


@app.get("/metrics")
async def metrics():
    """메트릭 조회"""
    # 추후 GPU 메모리 사용량 등 추가 가능
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```

#### Dockerfile 작성

```dockerfile
# model_servers/ocr_server/Dockerfile
FROM backend-ml-gpu-base:latest

WORKDIR /app

# 기존 앱 코드 복사 (모델 로직 재사용)
COPY app ./app

# 모델 서버 코드 복사
COPY model_servers/ocr_server /model_server

# 모델 서버 실행
WORKDIR /model_server
CMD ["python", "server.py"]
```

---

### 2단계: Docker Compose 설정

#### docker-compose.domains.yml 수정

```yaml
services:
  # ==================== 모델 서버 추가 ====================
  ocr-model-server:
    build:
      context: .
      dockerfile: model_servers/ocr_server/Dockerfile
    image: backend-ocr-model-server:latest
    container_name: ocr-model-server
    ports:
      - "8001:8001"
    runtime: nvidia
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - TZ=Asia/Seoul
    volumes:
      - ./app:/app/app
      - ./logs/ocr-model:/logs
      - ~/.paddleocr:/root/.paddleocr  # 모델 캐시
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==================== 기존 앱 서버 수정 ====================
  app-base:
    # ... 기존 설정 유지 ...
    environment:
      - OCR_MODEL_SERVER_URL=http://ocr-model-server:8001
    depends_on:
      - ocr-model-server
      - redis
      - postgres

  # ==================== 이제 불필요 (주석 처리) ====================
  # app-ocr-cpu:
  #   ...

  # app-ocr-gpu:
  #   ...
```

---

### 3단계: 앱 코드 수정

#### 3-1. OCR Client 구현

```python
# app/domains/ocr/clients/__init__.py
from .ocr_client import OCRClient, get_ocr_client

__all__ = ["OCRClient", "get_ocr_client"]
```

```python
# app/domains/ocr/clients/ocr_client.py
import httpx
from typing import Optional

from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)


class OCRClient:
    """OCR 모델 서버 HTTP 클라이언트"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OCR_MODEL_SERVER_URL
        self.timeout = 60.0

    def predict(
        self,
        image_data: bytes,
        confidence_threshold: float = 0.5
    ) -> dict:
        """
        OCR 예측 요청

        Args:
            image_data: 이미지 바이트 데이터
            confidence_threshold: 신뢰도 임계값

        Returns:
            OCR 결과 딕셔너리
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                files = {
                    "image": ("image.png", image_data, "image/png")
                }

                response = client.post(
                    f"{self.base_url}/predict",
                    files=files
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OCR 서버 오류: {response.status_code} - {response.text}")
                    return {
                        "text_boxes": [],
                        "full_text": "",
                        "status": "failed",
                        "error": f"Server error: {response.status_code}"
                    }

        except httpx.TimeoutException:
            logger.error("OCR 서버 타임아웃")
            return {
                "text_boxes": [],
                "full_text": "",
                "status": "failed",
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"OCR 클라이언트 오류: {e}")
            return {
                "text_boxes": [],
                "full_text": "",
                "status": "failed",
                "error": str(e)
            }

    def health_check(self) -> bool:
        """헬스 체크"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False


# 싱글톤 인스턴스
_ocr_client: Optional[OCRClient] = None


def get_ocr_client() -> OCRClient:
    """OCR 클라이언트 싱글톤"""
    global _ocr_client
    if _ocr_client is None:
        _ocr_client = OCRClient()
    return _ocr_client
```

#### 3-2. Celery Task 수정

```python
# app/domains/ocr/tasks/ocr_tasks.py
from app.celery_app import celery_app
from app.core.logging import get_logger

# 기존 import 제거:
# from ..services.ocr_service import get_ocr_service

# 새로운 import 추가:
from ..clients.ocr_client import get_ocr_client

logger = get_logger(__name__)


@celery_app.task(bind=True, name="ocr.extract_text")
def extract_text_task(
    self,
    image_data: bytes,
    language: str = "korean",
    confidence_threshold: float = 0.5,
    use_angle_cls: bool = True,
):
    """
    OCR 텍스트 추출 태스크 (모델 서버 호출)

    Args:
        image_data: 이미지 데이터 (bytes)
        language: 추출할 언어
        confidence_threshold: 신뢰도 임계값
        use_angle_cls: 각도 분류 사용 여부

    Returns:
        추출된 텍스트 결과
    """
    logger.info(f"OCR 태스크 시작 - Task ID: {self.request.id}")

    # 모델 서버 호출
    client = get_ocr_client()
    result = client.predict(
        image_data=image_data,
        confidence_threshold=confidence_threshold
    )

    logger.info(f"OCR 태스크 완료 - Task ID: {self.request.id}")
    return result
```

#### 3-3. Controller 수정 (블로킹 방지)

```python
# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.database import get_db
from app.core.logging import get_logger
from app.domains.common.services.common_service import CommonService, get_common_service
from app.utils.response_builder import ResponseBuilder

# 기존 import 제거:
# from ..services import OCRService, get_ocr_service

# 새로운 import 추가:
from ..clients.ocr_client import get_ocr_client

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# ThreadPoolExecutor 생성 (블로킹 방지)
executor = ThreadPoolExecutor(max_workers=2)


@router.post("/extract/sync")
async def extract_text_sync(
    image_file: UploadFile = File(...),
    language: str = Form("korean"),
    confidence_threshold: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    common_service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):
    """
    OCR 텍스트 추출 API (동기)

    - **image_file**: 이미지 파일 (multipart/form-data)
    - **language**: 추출할 언어 (기본값: korean)
    - **use_angle_cls**: 각도 분류 사용 여부 (기본값: True)
    - **confidence_threshold**: 신뢰도 임계값 (기본값: 0.5)
    """
    image_data = await image_file.read()
    filename = image_file.filename or "unknown.png"

    # 이미지 저장
    image_response = await common_service.save_image(
        image_data, filename, image_file.content_type
    )

    # OCR 모델 서버 호출 (ThreadPoolExecutor로 블로킹 방지)
    client = get_ocr_client()
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        executor,
        client.predict,
        image_data,
        confidence_threshold
    )

    # DB 저장
    ocr_results = await common_service.save_ocr_execution_to_db(
        db=db, image_response=image_response, ocr_result=result
    )

    return ResponseBuilder.success(data=ocr_results, message="OCR 텍스트 추출 완료")


# 기존 다른 엔드포인트들은 유지...
```

#### 3-4. 환경 변수 설정

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... 기존 설정 ...

    # 모델 서버 URL 추가
    OCR_MODEL_SERVER_URL: str = "http://ocr-model-server:8001"
    MODEL_SERVER_TIMEOUT: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True
```

```bash
# .env.development (추가)
OCR_MODEL_SERVER_URL=http://localhost:8001
```

```bash
# .env.production (추가)
OCR_MODEL_SERVER_URL=http://ocr-model-server:8001
```

---

## 🚀 실행 가이드

### 개발 환경 (로컬)

#### 1. 모델 서버만 먼저 테스트

```bash
# 터미널 1: 모델 서버 실행
cd model_servers/ocr_server
python server.py

# 터미널 2: 테스트
curl -X POST http://localhost:8001/predict \
  -F "image=@test.png"

# 헬스 체크
curl http://localhost:8001/health
```

#### 2. Docker Compose로 통합 테스트

```bash
# 모델 서버 + 앱 서버 실행
docker-compose -f docker-compose.domains.yml up \
  ocr-model-server \
  app-base \
  celery-worker \
  redis \
  postgres

# 테스트
curl -X POST http://localhost:8000/api/ocr/extract/sync \
  -F "image_file=@test.png"
```

### 프로덕션 환경

```bash
# 전체 빌드
docker-compose -f docker-compose.domains.yml build

# 실행
docker-compose -f docker-compose.domains.yml up -d

# 로그 확인
docker-compose -f docker-compose.domains.yml logs -f ocr-model-server

# 헬스 체크
docker-compose -f docker-compose.domains.yml ps
```

---

## ✅ 마이그레이션 체크리스트

### Phase 1: 준비
- [ ] `model_servers/ocr_server/` 디렉토리 생성
- [ ] `server.py` 작성
- [ ] `Dockerfile` 작성
- [ ] 로컬에서 모델 서버 단독 테스트

### Phase 2: 통합
- [ ] `OCRClient` 구현 (`app/domains/ocr/clients/`)
- [ ] `ocr_tasks.py` 수정 (HTTP 호출)
- [ ] `ocr_controller.py` 수정 (ThreadPoolExecutor)
- [ ] `config.py`에 환경 변수 추가
- [ ] `.env` 파일 업데이트

### Phase 3: Docker
- [ ] `docker-compose.domains.yml`에 `ocr-model-server` 추가
- [ ] Docker 이미지 빌드
- [ ] 통합 테스트

### Phase 4: 정리
- [ ] `app-ocr-cpu`, `app-ocr-gpu` 컨테이너 제거 또는 주석
- [ ] Nginx 설정 업데이트 (필요시)
- [ ] 문서 업데이트
- [ ] 모니터링 설정

---

## 📊 아키텍처 비교

### 마이그레이션 전
```
Client
  ↓
Nginx (8000)
  ↓
app-ocr-gpu (FastAPI + OCR 모델)
  - 직접 모델 로드
  - FastAPI 블로킹
  - VRAM 관리 어려움
```

### 마이그레이션 후
```
Client
  ↓
Nginx (8000)
  ↓
app-base (FastAPI)
  ↓ HTTP (8001)
ocr-model-server (OCR 모델 전용)
  - 독립적 모델 관리
  - 독립적 스케일링
  - VRAM 중앙 관리
```

---

## 🔧 트러블슈팅

### 문제 1: 모델 서버 연결 실패
```bash
# 헬스 체크
curl http://ocr-model-server:8001/health

# 네트워크 확인
docker network inspect app-network

# 로그 확인
docker logs ocr-model-server
```

### 문제 2: GPU 인식 안 됨
```bash
# GPU 상태 확인
nvidia-smi

# 컨테이너 내부 GPU 확인
docker exec ocr-model-server nvidia-smi

# runtime: nvidia 설정 확인
docker-compose -f docker-compose.domains.yml config | grep runtime
```

### 문제 3: 타임아웃
```python
# timeout 설정 조정
class OCRClient:
    def __init__(self):
        self.timeout = 120.0  # 60 → 120초
```

---

## 🎯 다음 단계

### 단기 (1-2주)
- [ ] VRAM 관리 추가 (`VRAMManager`, `GPUMonitor`)
- [ ] 메트릭 수집 (Prometheus)
- [ ] 알림 설정 (VRAM 임계치)

### 중기 (1개월)
- [ ] LLM 모델 서버 분리 (OCR과 동일한 패턴)
- [ ] 로드 밸런싱 (여러 GPU 활용)
- [ ] 배치 처리 최적화

### 장기 (3개월)
- [ ] 모델 버전 관리
- [ ] A/B 테스트 인프라
- [ ] 자동 스케일링 (Kubernetes)

---

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Docker Compose GPU 지원](https://docs.docker.com/compose/gpu-support/)
- [PaddleOCR 문서](https://github.com/PaddlePaddle/PaddleOCR)
- [HTTPX 문서](https://www.python-httpx.org/)

---

**작성일**: 2025-10-14
**버전**: 1.0.0
**작성자**: Claude Code Assistant
