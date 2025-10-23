### 6. DB 진행 상황 추적

**역할**: Celery chain의 진행 상황을 PostgreSQL에 영구 저장하여 추적 및 분석 가능

## DB 모델 정의

**실제 구현 파일 위치:**
- `shared/models/chain_execution.py`
- `shared/models/task_log.py`
- `shared/schemas/enums.py`
- `shared/repository/crud/sync_crud/chain_execution.py`
- `shared/repository/crud/sync_crud/task_log.py`

### ProcessStatus Enum

```python
# shared/schemas/enums.py
from enum import Enum

class ProcessStatus(str, Enum):
    """프로세스 상태 (Chain 및 Task 공통 사용)"""
    PENDING = "PENDING"      # 대기 중
    STARTED = "STARTED"      # 시작됨
    RUNNING = "RUNNING"      # 진행 중
    SUCCESS = "SUCCESS"      # 성공
    FAILURE = "FAILURE"      # 실패
    RETRY = "RETRY"          # 재시도
    REVOKED = "REVOKED"      # 취소됨
```

### ChainExecution 모델

```python
# shared/models/chain_execution.py
from datetime import datetime
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from ..schemas.enums import ProcessStatus
from .base import Base

class ChainExecution(Base):
    """
    Celery Chain 전체 실행 정보
    """
    __tablename__ = "chain_executions"

    # 기본 필드
    id = Column(Integer, primary_key=True)
    chain_id = Column(String(255), nullable=True, index=True, comment="Celery chain root task ID")
    chain_name = Column(String(255), nullable=False, index=True, comment="예: cr_extract_workflow")

    # 상태 관리
    status = Column(String(20), default=ProcessStatus.PENDING, nullable=False, index=True)

    # 작업 통계
    total_tasks = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)
    failed_tasks = Column(Integer, default=0, nullable=False)

    # 타임스탬프
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # 메타 정보
    initiated_by = Column(String(100), nullable=True)
    input_data = Column(JSON, nullable=True)
    final_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # 관계 정의
    task_logs = relationship(
        "TaskLog",
        back_populates="chain_execution",
        cascade="all, delete-orphan",
        order_by="TaskLog.started_at"
    )

    # 인덱스
    __table_args__ = (
        Index("idx_chain_status_started", "status", "started_at"),
        Index("idx_chain_name_status", "chain_name", "status"),
    )

    # 헬퍼 메서드
    def increment_completed_tasks(self):
        """완료된 작업 수 증가 및 자동 완료"""
        self.completed_tasks += 1
        if self.completed_tasks >= self.total_tasks:
            self.complete_execution(success=True)

    def increment_failed_tasks(self):
        """실패한 작업 수 증가"""
        self.failed_tasks += 1

    def start_execution(self):
        """체인 실행 시작"""
        self.status = ProcessStatus.STARTED
        self.started_at = datetime.now()

    def complete_execution(self, success=True, final_result=None, error_message=None):
        """체인 실행 완료"""
        self.status = ProcessStatus.SUCCESS if success else ProcessStatus.FAILURE
        self.finished_at = datetime.now()
        if final_result is not None:
            self.final_result = final_result
        if error_message:
            self.error_message = error_message
```

### TaskLog 모델

```python
# shared/models/task_log.py
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class TaskLog(Base):
    """개별 Celery Task 실행 로그"""
    __tablename__ = "task_logs"

    # 기본 필드
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True, comment="Celery UUID")
    task_name = Column(String(255), nullable=False, index=True, comment="예: pipeline.ocr_stage")
    status = Column(String(50), nullable=False, index=True)

    # 에러 정보
    error = Column(String(512))

    # 시간 추적
    started_at = Column(DateTime, index=True)
    finished_at = Column(DateTime)

    # 재시도
    retries = Column(Integer, default=0)

    # Chain과의 관계
    chain_execution_id = Column(
        Integer,
        ForeignKey("chain_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    chain_execution = relationship(
        "ChainExecution",
        back_populates="task_logs"
    )

    # 인덱스
    __table_args__ = (
        Index("idx_task_logs_name_status", "task_name", "status"),
        Index("idx_task_logs_started_at_desc", started_at.desc()),
        Index("idx_task_logs_chain_execution", "chain_execution_id", "status"),
    )
```

## CRUD 함수

### ChainExecution CRUD

```python
# shared/repository/crud/sync_crud/chain_execution.py
from datetime import datetime
from sqlalchemy.orm import Session
from shared.models.chain_execution import ChainExecution
from shared.schemas.enums import ProcessStatus

class CRUDChainExecution:
    """ChainExecution CRUD 작업"""

    def get_by_chain_id(self, db: Session, *, chain_id: str) -> ChainExecution | None:
        """chain_id로 조회"""
        return db.query(ChainExecution).filter(
            ChainExecution.chain_id == chain_id
        ).first()

    def create_chain_execution(
        self,
        db: Session,
        *,
        chain_id: str,
        chain_name: str,
        total_tasks: int = 4,
        initiated_by: str = None,
        input_data: dict = None
    ) -> ChainExecution:
        """새 체인 실행 생성"""
        chain_exec = ChainExecution(
            chain_id=chain_id,
            chain_name=chain_name,
            total_tasks=total_tasks,
            status=ProcessStatus.PENDING.value,
            initiated_by=initiated_by,
            input_data=input_data
        )
        db.add(chain_exec)
        db.commit()
        db.refresh(chain_exec)
        return chain_exec

    def increment_completed_tasks(
        self,
        db: Session,
        *,
        chain_execution: ChainExecution
    ) -> ChainExecution:
        """완료된 작업 수 증가"""
        chain_execution.increment_completed_tasks()
        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution

    def increment_failed_tasks(
        self,
        db: Session,
        *,
        chain_execution: ChainExecution
    ) -> ChainExecution:
        """실패한 작업 수 증가"""
        chain_execution.increment_failed_tasks()
        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution

    def update_status(
        self,
        db: Session,
        *,
        chain_execution: ChainExecution,
        status: ProcessStatus
    ) -> ChainExecution:
        """상태 업데이트"""
        chain_execution.status = status

        if status == ProcessStatus.STARTED.value:
            chain_execution.started_at = datetime.now()
        elif status in [ProcessStatus.SUCCESS.value, ProcessStatus.FAILURE.value]:
            chain_execution.finished_at = datetime.now()

        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution

# 인스턴스
chain_execution_crud = CRUDChainExecution()
```

### TaskLog CRUD

```python
# shared/repository/crud/sync_crud/task_log.py
from datetime import datetime
from sqlalchemy.orm import Session
from shared.models.task_log import TaskLog

class CRUDTaskLog:
    """TaskLog CRUD 작업"""

    def get_by_task_id(self, db: Session, *, task_id: str) -> TaskLog | None:
        """task_id로 조회"""
        return db.query(TaskLog).filter(TaskLog.task_id == task_id).first()

    def create_task_log(
        self,
        db: Session,
        *,
        task_id: str,
        task_name: str,
        status: str = "PENDING",
        chain_execution_id: int = None
    ) -> TaskLog:
        """새 작업 로그 생성"""
        task_log = TaskLog(
            task_id=task_id,
            task_name=task_name,
            status=status,
            chain_execution_id=chain_execution_id
        )
        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        return task_log

    def update_status(
        self,
        db: Session,
        *,
        task_log: TaskLog,
        status: str,
        error: str = None
    ) -> TaskLog:
        """작업 상태 업데이트"""
        task_log.status = status

        if error is not None:
            task_log.error = error

        # 시작 시간 설정
        if status == "STARTED" and task_log.started_at is None:
            task_log.started_at = datetime.now()

        # 완료 시간 설정
        if status in ["SUCCESS", "FAILURE", "REVOKED"]:
            task_log.finished_at = datetime.now()

        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        return task_log

# 인스턴스
task_log_crud = CRUDTaskLog()
```

## Celery Signals 통합

**Celery Signals 활용 (자동화) - ✅ 추천**

Celery의 signals를 사용하여 모든 task에 자동으로 DB 업데이트 적용.

```python
# celery_worker/core/celery_signals.py
from celery import signals
from shared.core.database import get_db
from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud
from shared.repository.crud.sync_crud.task_log import task_log_crud
from shared.schemas.enums import ProcessStatus

# Task 이름 → Stage 매핑
TASK_STAGE_MAP = {
    "pipeline.ocr_stage": "OCRStage",
    "pipeline.llm_stage": "LLMStage",
    "pipeline.layout_stage": "LayoutStage",
    "pipeline.excel_stage": "ExcelStage",
}

@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, **kwargs):
    """Task 시작 전 - TaskLog 생성"""

    # Pipeline task인지 확인
    if task.name not in TASK_STAGE_MAP:
        return

    # chain_id 추출 (첫 번째 인자)
    if not args or len(args) == 0:
        return
    chain_id = args[0]

    # DB 업데이트
    db = next(get_db())
    try:
        # ChainExecution 조회
        chain_exec = chain_execution_crud.get_by_chain_id(db, chain_id=chain_id)

        if chain_exec:
            # TaskLog 생성
            task_log_crud.create_task_log(
                db=db,
                task_id=task_id,
                task_name=task.name,
                status=ProcessStatus.STARTED.value,
                chain_execution_id=chain_exec.id
            )

            # Chain 상태 업데이트 (첫 task라면 STARTED로)
            if chain_exec.status == ProcessStatus.PENDING.value:
                chain_exec.start_execution()
                db.commit()

    finally:
        db.close()

@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Task 완료 후 - TaskLog 업데이트"""

    # Pipeline task인지 확인
    if task.name not in TASK_STAGE_MAP:
        return

    # DB 업데이트
    db = next(get_db())
    try:
        # TaskLog 조회 및 업데이트
        task_log = task_log_crud.get_by_task_id(db, task_id=task_id)

        if task_log:
            task_log_crud.update_status(
                db=db,
                task_log=task_log,
                status=ProcessStatus.SUCCESS.value
            )

            # ChainExecution 완료 카운트 증가
            if task_log.chain_execution:
                chain_execution_crud.increment_completed_tasks(
                    db=db,
                    chain_execution=task_log.chain_execution
                )

    finally:
        db.close()

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Task 실패 시 - 에러 기록"""

    # Pipeline task인지 확인
    if sender.name not in TASK_STAGE_MAP:
        return

    # DB 업데이트
    db = next(get_db())
    try:
        # TaskLog 조회 및 업데이트
        task_log = task_log_crud.get_by_task_id(db, task_id=task_id)

        if task_log:
            task_log_crud.update_status(
                db=db,
                task_log=task_log,
                status=ProcessStatus.FAILURE.value,
                error=str(exception)[:500]  # 500자 제한
            )

            # ChainExecution 실패 카운트 증가
            if task_log.chain_execution:
                chain_execution_crud.increment_failed_tasks(
                    db=db,
                    chain_execution=task_log.chain_execution
                )

                # Chain 전체를 실패로 마킹
                task_log.chain_execution.complete_execution(
                    success=False,
                    error_message=f"Task {sender.name} failed: {str(exception)}"
                )
                db.commit()

    finally:
        db.close()

@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, **kwargs):
    """Task 재시도 시 - 재시도 카운트 증가"""

    # Pipeline task인지 확인
    if sender.name not in TASK_STAGE_MAP:
        return

    # DB 업데이트
    db = next(get_db())
    try:
        task_log = task_log_crud.get_by_task_id(db, task_id=task_id)

        if task_log:
            task_log.retries += 1
            task_log.status = ProcessStatus.RETRY.value
            db.commit()

    finally:
        db.close()
```

**Celery App에 Signals 연결**

```python
# celery_worker/core/celery_app.py
from celery import Celery

celery = Celery("celery_worker")
celery.config_from_object("celery_worker.core.celery_config")

# Signals 임포트하여 자동 등록
from celery_worker.core import celery_signals  # noqa
```

## Pipeline 시작 시 ChainExecution 생성

```python
# celery_worker/tasks/pipeline_tasks.py
from celery import chain
from shared.core.database import get_db
from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud

def start_cr_extract_pipeline(file_path: str, options: dict) -> str:
    """CR 추출 파이프라인 시작"""

    # 1. Chain ID 생성 (UUID)
    import uuid
    chain_id = str(uuid.uuid4())

    # 2. DB에 ChainExecution 생성
    db = next(get_db())
    try:
        chain_exec = chain_execution_crud.create_chain_execution(
            db=db,
            chain_id=chain_id,
            chain_name="cr_extract_workflow",
            total_tasks=4,  # OCR, LLM, Layout, Excel
            initiated_by="api_server",
            input_data={
                "file_path": file_path,
                "options": options
            }
        )
    finally:
        db.close()

    # 3. Celery chain 시작
    workflow = chain(
        ocr_stage_task.s(chain_id),
        llm_stage_task.s(),
        layout_stage_task.s(),
        excel_stage_task.s()
    )

    result = workflow.apply_async()

    return chain_id
```

## API 엔드포인트

```python
# api_server/domains/pipeline/controllers/pipeline_controller.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.core.database import get_db
from shared.models.chain_execution import ChainExecution
from shared.models.task_log import TaskLog

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.get("/status/{chain_id}")
async def get_pipeline_status(chain_id: str, db: Session = Depends(get_db)):
    """파이프라인 상태 조회"""

    # ChainExecution 조회
    chain_exec = db.query(ChainExecution).filter(
        ChainExecution.chain_id == chain_id
    ).first()

    if not chain_exec:
        raise HTTPException(status_code=404, detail="Chain not found")

    # TaskLog 조회
    task_logs = db.query(TaskLog).filter(
        TaskLog.chain_execution_id == chain_exec.id
    ).order_by(TaskLog.started_at).all()

    return {
        "chain_id": chain_id,
        "chain_name": chain_exec.chain_name,
        "status": chain_exec.status,
        "progress": chain_exec.completed_tasks / chain_exec.total_tasks if chain_exec.total_tasks > 0 else 0,
        "total_tasks": chain_exec.total_tasks,
        "completed_tasks": chain_exec.completed_tasks,
        "failed_tasks": chain_exec.failed_tasks,
        "started_at": chain_exec.started_at,
        "finished_at": chain_exec.finished_at,
        "error_message": chain_exec.error_message,
        "tasks": [
            {
                "task_id": log.task_id,
                "task_name": log.task_name,
                "status": log.status,
                "retries": log.retries,
                "error": log.error,
                "started_at": log.started_at,
                "finished_at": log.finished_at
            }
            for log in task_logs
        ]
    }

@router.get("/history")
async def get_pipeline_history(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """파이프라인 실행 이력 조회"""

    chain_execs = db.query(ChainExecution).order_by(
        ChainExecution.started_at.desc()
    ).limit(limit).offset(offset).all()

    return [
        {
            "chain_id": chain.chain_id,
            "chain_name": chain.chain_name,
            "status": chain.status,
            "completed_tasks": chain.completed_tasks,
            "total_tasks": chain.total_tasks,
            "started_at": chain.started_at,
            "finished_at": chain.finished_at
        }
        for chain in chain_execs
    ]
```

## 장점

1. **영구 저장**: PostgreSQL에 모든 실행 이력 보관
2. **상세 추적**: Task별 실행 시간, 재시도, 에러 완벽 기록
3. **자동화**: Celery Signals로 모든 task에 자동 적용
4. **관계 관리**: ChainExecution ↔ TaskLog 관계로 쉬운 조회
5. **성능 분석**: SQL 쿼리로 성능/실패율 분석 가능
6. **디버깅**: 에러 발생 시점과 원인 정확히 파악

## 데이터 흐름

```
1. API 요청
   ↓
2. ChainExecution 생성 (DB)
   - chain_id, chain_name, total_tasks
   ↓
3. Celery Chain 시작
   ↓
4. 각 Task 실행
   - task_prerun → TaskLog 생성 (DB)
   - task 실행
   - task_postrun → TaskLog 완료 + ChainExecution.completed_tasks++
   - task_failure → TaskLog 실패 + ChainExecution.failed_tasks++
   ↓
5. Chain 완료
   - ChainExecution.status = SUCCESS/FAILURE
   - ChainExecution.finished_at 기록
```
