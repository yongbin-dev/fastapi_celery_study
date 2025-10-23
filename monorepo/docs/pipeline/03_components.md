## 핵심 컴포넌트

### 1. PipelineContext (공유 데이터 구조)

**역할**: 파이프라인 전체의 실행 상태와 각 단계의 결과 데이터를 저장

```python
# shared/pipeline/context.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class PipelineContext:
    """파이프라인 실행 전체의 상태와 데이터를 관리"""

    # 기본 정보
    context_id: str
    input_file_path: str
    options: Dict[str, Any] = field(default_factory=dict)

    # 단계별 결과
    ocr_result: Optional[Dict] = None
    llm_result: Optional[Dict] = None
    layout_result: Optional[Dict] = None
    excel_file_path: Optional[str] = None

    # 상태 관리
    status: str = "pending"  # pending, ocr_in_progress, ocr_completed, ...
    current_stage: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0

    # 타임스탬프
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Redis 저장을 위한 딕셔너리 변환"""
        return {
            "context_id": self.context_id,
            "input_file_path": self.input_file_path,
            "options": self.options,
            "ocr_result": self.ocr_result,
            "llm_result": self.llm_result,
            "layout_result": self.layout_result,
            "excel_file_path": self.excel_file_path,
            "status": self.status,
            "current_stage": self.current_stage,
            "error": self.error,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PipelineContext':
        """Redis에서 로드한 데이터로 객체 생성"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    def update_status(self, status: str, stage: Optional[str] = None):
        """상태 업데이트 헬퍼"""
        self.status = status
        if stage:
            self.current_stage = stage
        self.updated_at = datetime.now()
```

### 2. PipelineStage (추상 기본 클래스)

**역할**: 모든 파이프라인 단계가 구현해야 할 인터페이스 정의

```python
# shared/pipeline/stage.py
from abc import ABC, abstractmethod
from typing import Optional
from .context import PipelineContext

class PipelineStage(ABC):
    """각 파이프라인 단계의 기본 인터페이스"""

    def __init__(self):
        self.stage_name = self.__class__.__name__

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        실제 처리 로직 (서브클래스에서 구현 필수)

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트
        """
        pass

    def validate_input(self, context: PipelineContext) -> None:
        """
        입력 데이터 검증

        Raises:
            ValueError: 입력 데이터가 유효하지 않을 때
        """
        pass

    def validate_output(self, context: PipelineContext) -> None:
        """
        출력 데이터 검증

        Raises:
            ValueError: 출력 데이터가 유효하지 않을 때
        """
        pass

    async def run(self, context: PipelineContext) -> PipelineContext:
        """
        전체 실행 플로우 (템플릿 메서드 패턴)

        1. 입력 검증
        2. 실행
        3. 출력 검증
        4. 상태 업데이트
        """
        try:
            # 1. 입력 검증
            self.validate_input(context)

            # 2. 실행
            context.update_status(
                status=f"{self.stage_name.lower()}_in_progress",
                stage=self.stage_name
            )
            context = await self.execute(context)

            # 3. 출력 검증
            self.validate_output(context)

            # 4. 상태 업데이트
            context.update_status(
                status=f"{self.stage_name.lower()}_completed",
                stage=self.stage_name
            )

            return context

        except Exception as e:
            # 에러 처리
            context.error = str(e)
            context.status = "failed"
            context.current_stage = self.stage_name
            raise
```

### 3. Celery 태스크 구조

**역할**: 각 Stage를 Celery 태스크로 래핑하여 비동기 실행 및 재시도 지원

```python
# celery_worker/tasks/pipeline_tasks.py
from celery import chain
from shared.pipeline.context import PipelineContext
from shared.core.redis_client import redis_client
from .stages.ocr_stage import OCRStage
from .stages.llm_stage import LLMStage
from .stages.layout_stage import LayoutStage
from .stages.excel_stage import ExcelStage
from ..core.celery_app import celery
import json

# Context 저장/로드 헬퍼
def save_context_to_redis(context: PipelineContext, ttl: int = 86400):
    """Context를 Redis에 저장 (24시간 TTL)"""
    key = f"pipeline:context:{context.context_id}"
    redis_client.setex(
        key,
        ttl,
        json.dumps(context.to_dict())
    )

def load_context_from_redis(context_id: str) -> PipelineContext:
    """Redis에서 Context 로드"""
    key = f"pipeline:context:{context_id}"
    data = redis_client.get(key)
    if not data:
        raise ValueError(f"Context {context_id} not found in Redis")
    return PipelineContext.from_dict(json.loads(data))

# 각 단계별 Celery 태스크
@celery.task(
    bind=True,
    name="pipeline.ocr_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def ocr_stage_task(self, context_id: str) -> str:
    """OCR 단계 실행"""
    # Redis에서 context 로드
    context = load_context_from_redis(context_id)

    # OCR 실행
    stage = OCRStage()
    context = await stage.run(context)

    # Redis에 저장
    save_context_to_redis(context)

    return context_id  # 다음 단계로 전달

@celery.task(
    bind=True,
    name="pipeline.llm_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600
)
def llm_stage_task(self, context_id: str) -> str:
    """LLM 분석 단계 실행"""
    context = load_context_from_redis(context_id)
    stage = LLMStage()
    context = await stage.run(context)
    save_context_to_redis(context)
    return context_id

@celery.task(
    bind=True,
    name="pipeline.layout_stage",
    max_retries=2
)
def layout_stage_task(self, context_id: str) -> str:
    """레이아웃 분석 단계 실행"""
    context = load_context_from_redis(context_id)
    stage = LayoutStage()
    context = await stage.run(context)
    save_context_to_redis(context)
    return context_id

@celery.task(
    bind=True,
    name="pipeline.excel_stage",
    max_retries=2
)
def excel_stage_task(self, context_id: str) -> str:
    """Excel 생성 단계 실행"""
    context = load_context_from_redis(context_id)
    stage = ExcelStage()
    context = await stage.run(context)

    # 최종 결과 저장
    save_context_to_redis(context)
    save_final_result_to_db(context)

    return context.excel_file_path

# 파이프라인 시작 함수
def start_extract_pipeline(file_path: str, options: Dict) -> str:
    """
    CR 추출 파이프라인 시작

    Args:
        file_path: 입력 파일 경로
        options: 파이프라인 옵션

    Returns:
        context_id: 파이프라인 실행 추적 ID
    """
    # Context 생성
    context = PipelineContext(
        context_id=generate_unique_id(),
        input_file_path=file_path,
        options=options
    )
    save_context_to_redis(context)

    # Celery chain으로 단계 연결
    workflow = chain(
        ocr_stage_task.s(context.context_id),
        llm_stage_task.s(),
        layout_stage_task.s(),
        excel_stage_task.s()
    )

    # 비동기 실행
    result = workflow.apply_async()

    return context.context_id
```

### 4. Stage 구현 예시

#### OCRStage

```python
# celery_worker/tasks/stages/ocr_stage.py
from shared.pipeline.stage import PipelineStage
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError
import httpx

class OCRStage(PipelineStage):
    """OCR 처리 단계"""

    def __init__(self):
        super().__init__()
        self.ml_server_url = "http://ml-server:8001"

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: 파일 경로가 있는지 확인"""
        if not context.input_file_path:
            raise ValueError("input_file_path is required")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """ML 서버에 OCR 요청"""

        try:
            # ML 서버 호출
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.ml_server_url}/ocr/process",
                    json={
                        "file_path": context.input_file_path,
                        "engine": context.options.get("ocr_engine", "easyocr"),
                        "languages": context.options.get("languages", ["ko", "en"])
                    }
                )
                response.raise_for_status()

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            # 네트워크 오류 → 재시도 가능
            raise RetryableError("OCRStage", f"Network error: {str(e)}")
        except httpx.HTTPStatusError as e:
            # HTTP 오류
            if e.response.status_code >= 500:
                # 서버 오류 → 재시도 가능
                raise RetryableError("OCRStage", f"Server error: {str(e)}")
            else:
                # 클라이언트 오류 → 재시도 불가
                raise ValueError(f"OCR request failed: {str(e)}")

        # 결과 저장
        ocr_data = response.json()
        context.ocr_result = {
            "text": ocr_data.get("text"),
            "confidence": ocr_data.get("confidence"),
            "bounding_boxes": ocr_data.get("bounding_boxes", []),
            "metadata": ocr_data.get("metadata", {})
        }

        return context

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증: OCR 결과에 텍스트가 있는지 확인"""
        if not context.ocr_result:
            raise ValueError("OCR result is empty")

        if not context.ocr_result.get("text"):
            raise ValueError("OCR failed to extract text")

        # 신뢰도 체크 (선택적)
        confidence = context.ocr_result.get("confidence", 0)
        if confidence < context.options.get("min_confidence", 0.5):
            raise ValueError(
                f"OCR confidence too low: {confidence} < "
                f"{context.options.get('min_confidence', 0.5)}"
            )
```

#### LLMStage

```python
# celery_worker/tasks/stages/llm_stage.py
from shared.pipeline.stage import PipelineStage
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError
import openai
from typing import Dict, Any

class LLMStage(PipelineStage):
    """LLM 분석 단계"""

    def __init__(self):
        super().__init__()
        self.client = openai.AsyncOpenAI()

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: OCR 결과가 있는지 확인"""
        if not context.ocr_result:
            raise ValueError("OCR result is required for LLM analysis")

        if not context.ocr_result.get("text"):
            raise ValueError("OCR text is empty")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """LLM으로 텍스트 구조화"""

        # OCR 텍스트 추출
        ocr_text = context.ocr_result["text"]

        # LLM 프롬프트 생성
        prompt = self._build_prompt(ocr_text, context.options)

        try:
            # LLM API 호출
            response = await self.client.chat.completions.create(
                model=context.options.get("llm_model", "gpt-4"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from CR documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

        except openai.RateLimitError as e:
            # Rate limit → 재시도
            raise RetryableError("LLMStage", f"Rate limit exceeded: {str(e)}")
        except openai.APIError as e:
            # API 오류 → 재시도
            raise RetryableError("LLMStage", f"API error: {str(e)}")

        # 응답 파싱
        llm_output = response.choices[0].message.content
        structured_data = self._parse_llm_response(llm_output)

        # 결과 저장
        context.llm_result = {
            "structured_data": structured_data,
            "model": response.model,
            "tokens_used": response.usage.total_tokens
        }

        return context

    def _build_prompt(self, text: str, options: Dict[str, Any]) -> str:
        """LLM 프롬프트 생성"""
        return f"""
Extract the following information from this CR document:

{text}

Extract:
- CR Number
- Title
- Description
- Requester
- Date
- Priority
- Status
- Changes requested

Return as JSON.
"""

    def _parse_llm_response(self, response: str) -> Dict:
        """LLM 응답 파싱"""
        import json
        return json.loads(response)

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증: 필수 필드가 있는지 확인"""
        if not context.llm_result:
            raise ValueError("LLM result is empty")

        structured_data = context.llm_result.get("structured_data", {})
        required_fields = ["cr_number", "title", "description"]

        missing_fields = [
            field for field in required_fields
            if field not in structured_data
        ]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
```

#### LayoutStage

```python
# celery_worker/tasks/stages/layout_stage.py
from shared.pipeline.stage import PipelineStage
from shared.pipeline.context import PipelineContext
from typing import List, Dict

class LayoutStage(PipelineStage):
    """레이아웃 분석 단계"""

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증"""
        if not context.ocr_result:
            raise ValueError("OCR result is required")

        if not context.llm_result:
            raise ValueError("LLM result is required")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """레이아웃 분석 및 테이블 구조 파악"""

        # OCR의 bounding box 정보 활용
        bounding_boxes = context.ocr_result.get("bounding_boxes", [])

        # 테이블 영역 감지
        table_regions = self._detect_table_regions(bounding_boxes)

        # 테이블 구조 분석
        tables = []
        for region in table_regions:
            table_structure = self._analyze_table_structure(region, bounding_boxes)
            tables.append(table_structure)

        # 결과 저장
        context.layout_result = {
            "tables": tables,
            "table_count": len(tables),
            "metadata": {
                "total_regions": len(table_regions)
            }
        }

        return context

    def _detect_table_regions(self, bounding_boxes: List[Dict]) -> List[Dict]:
        """테이블 영역 감지 (간단한 휴리스틱)"""
        # 실제로는 더 복잡한 알고리즘 사용 (예: table detection 모델)
        regions = []

        # 정렬된 bounding box들을 분석하여 테이블 형태 감지
        # 여기서는 간단히 구현
        return regions

    def _analyze_table_structure(
        self,
        region: Dict,
        bounding_boxes: List[Dict]
    ) -> Dict:
        """테이블 구조 분석 (행/열 파악)"""
        # 테이블 내의 셀 감지 및 행/열 구조 파악
        return {
            "region": region,
            "rows": [],
            "columns": []
        }

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증"""
        if not context.layout_result:
            raise ValueError("Layout result is empty")
```

#### ExcelStage

```python
# celery_worker/tasks/stages/excel_stage.py
from shared.pipeline.stage import PipelineStage
from shared.pipeline.context import PipelineContext
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import os

class ExcelStage(PipelineStage):
    """Excel 생성 단계"""

    def __init__(self):
        super().__init__()
        self.output_dir = "/tmp/pipeline_output"
        os.makedirs(self.output_dir, exist_ok=True)

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증"""
        if not context.llm_result:
            raise ValueError("LLM result is required")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """구조화된 데이터를 Excel 파일로 변환"""

        # Excel 워크북 생성
        wb = Workbook()

        # 메인 정보 시트
        ws_main = wb.active
        ws_main.title = "CR 정보"
        self._write_cr_info(ws_main, context.llm_result["structured_data"])

        # 테이블 데이터 시트 (있는 경우)
        if context.layout_result and context.layout_result.get("tables"):
            ws_tables = wb.create_sheet("테이블 데이터")
            self._write_tables(ws_tables, context.layout_result["tables"])

        # 파일 저장
        file_name = f"{context.context_id}.xlsx"
        file_path = os.path.join(self.output_dir, file_name)
        wb.save(file_path)

        # Supabase에 업로드 (선택적)
        remote_url = await self._upload_to_supabase(file_path, file_name)

        # 결과 저장
        context.excel_file_path = remote_url or file_path

        return context

    def _write_cr_info(self, ws, data: Dict):
        """CR 정보를 시트에 작성"""
        # 헤더 스타일
        header_fill = PatternFill(start_color="4F81BD", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        # 데이터 작성
        headers = [
            ("CR 번호", "cr_number"),
            ("제목", "title"),
            ("설명", "description"),
            ("요청자", "requester"),
            ("날짜", "date"),
            ("우선순위", "priority"),
            ("상태", "status")
        ]

        for idx, (header, key) in enumerate(headers, start=1):
            # 헤더
            cell_header = ws.cell(row=idx, column=1, value=header)
            cell_header.fill = header_fill
            cell_header.font = header_font

            # 값
            ws.cell(row=idx, column=2, value=data.get(key, "N/A"))

    def _write_tables(self, ws, tables: List[Dict]):
        """테이블 데이터를 시트에 작성"""
        # 테이블 데이터 작성 로직
        pass

    async def _upload_to_supabase(self, file_path: str, file_name: str) -> str:
        """Supabase Storage에 파일 업로드"""
        # Supabase 업로드 로직
        # return remote_url
        return None

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증"""
        if not context.excel_file_path:
            raise ValueError("Excel file was not created")

        # 파일 존재 확인
        if context.excel_file_path.startswith("/"):
            if not os.path.exists(context.excel_file_path):
                raise ValueError(f"Excel file not found: {context.excel_file_path}")
```

### 5. API 엔드포인트

```python
# api_server/domains/pipeline/controllers/pipeline_controller.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from ..schemas.pipeline_schemas import (
    CRExtractOptions,
    PipelineStartResponse,
    PipelineStatusResponse
)
from celery_worker.tasks.pipeline_tasks import (
    start_cr_extract_pipeline,
    load_context_from_redis
)
import shutil
import os

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.post("/cr-extract", response_model=PipelineStartResponse)
async def create_cr_extract_job(
    file: UploadFile = File(...),
    ocr_engine: str = "easyocr",
    llm_model: str = "gpt-4",
    min_confidence: float = 0.5
):
    """
    CR 추출 파이프라인 시작

    - **file**: 처리할 이미지 또는 PDF 파일
    - **ocr_engine**: OCR 엔진 (easyocr, paddleocr)
    - **llm_model**: LLM 모델 (gpt-4, gpt-3.5-turbo)
    - **min_confidence**: 최소 OCR 신뢰도 (0.0-1.0)
    """

    try:
        # 파일 저장
        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 파이프라인 시작
        options = {
            "ocr_engine": ocr_engine,
            "llm_model": llm_model,
            "min_confidence": min_confidence
        }

        context_id = start_cr_extract_pipeline(
            file_path=file_path,
            options=options
        )

        return PipelineStartResponse(
            context_id=context_id,
            status="started",
            message="CR extraction pipeline started successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{context_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(context_id: str):
    """
    파이프라인 실행 상태 조회

    - **context_id**: 파이프라인 실행 ID
    """

    try:
        context = load_context_from_redis(context_id)

        return PipelineStatusResponse(
            context_id=context_id,
            status=context.status,
            current_stage=context.current_stage,
            error=context.error,
            progress=_calculate_progress(context.status),
            result={
                "excel_file_path": context.excel_file_path
            } if context.status == "completed" else None,
            created_at=context.created_at,
            updated_at=context.updated_at
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_progress(status: str) -> float:
    """상태에 따른 진행률 계산"""
    progress_map = {
        "pending": 0.0,
        "ocr_in_progress": 0.1,
        "ocr_completed": 0.25,
        "llm_in_progress": 0.35,
        "llm_completed": 0.5,
        "layout_in_progress": 0.6,
        "layout_completed": 0.75,
        "excel_in_progress": 0.85,
        "completed": 1.0,
        "failed": 0.0
    }
    return progress_map.get(status, 0.0)
```

