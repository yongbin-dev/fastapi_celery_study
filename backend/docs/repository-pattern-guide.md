# Repository 패턴 가이드

## 📋 개요

**Repository 패턴**은 데이터 액세스 로직을 비즈니스 로직으로부터 분리하는 디자인 패턴입니다.

## 🏗️ 기존 구조 vs 개선된 구조

### 기존 구조 (문제점)

```
app/api/v1/crud/          # ❌ API 버전에 종속
├── async_crud/
│   ├── chain_execution.py
│   └── task_log.py
└── sync_crud/
```

**문제점:**
1. ❌ API v2 개발 시 CRUD 중복
2. ❌ 도메인에서 사용 시 API 레이어 의존
3. ❌ DB 접근 레이어가 HTTP 계층에 위치

### 개선된 구조 (Repository 패턴)

```
app/repositories/         # ✅ 독립적인 데이터 액세스 레이어
├── __init__.py
├── base.py              # BaseRepository (공통 CRUD)
├── chain_execution.py   # ChainExecution Repository
└── task_log.py          # TaskLog Repository

app/domains/              # 도메인별 Repository (선택)
└── llm/
    └── repositories/
        └── conversation.py
```

## 📦 Repository 구조

### 1. BaseRepository (`app/repositories/base.py`)

모든 Repository의 기본 클래스:

```python
class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """기본 Repository 클래스"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """ID로 단일 객체 조회"""
        pass

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        """여러 객체 조회 (페이징)"""
        pass

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType):
        """객체 생성"""
        pass

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in):
        """객체 업데이트"""
        pass

    async def delete(self, db: AsyncSession, *, id: int):
        """객체 삭제"""
        pass

    async def count(self, db: AsyncSession) -> int:
        """전체 레코드 수 조회"""
        pass
```

### 2. ChainExecutionRepository

파이프라인 실행 기록 관리:

```python
class AsyncChainExecutionRepository(BaseRepository):
    """ChainExecution 비동기 Repository"""

    async def get_by_chain_id(self, db: AsyncSession, *, chain_id: str):
        """chain_id로 조회"""
        pass

    async def get_with_task_logs(self, db: AsyncSession, *, chain_id: str):
        """TaskLog와 함께 조회 (Join)"""
        pass

    async def increment_completed_tasks(self, db: AsyncSession, *, chain_execution):
        """완료된 작업 수 증가"""
        pass
```

### 3. TaskLogRepository

Celery 태스크 로그 관리:

```python
class AsyncTaskLogRepository(BaseRepository):
    """TaskLog 비동기 Repository"""

    async def get_by_task_id(self, db: AsyncSession, *, task_id: str):
        """task_id로 조회"""
        pass
```

## 🔄 계층 구조

```
┌─────────────────────────────────────┐
│   API Controllers (HTTP Layer)      │  ← 사용자 요청 처리
│   app/api/v1/controllers/          │
│   app/orchestration/controllers/    │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Services (Business Logic)         │  ← 비즈니스 로직
│   app/orchestration/services/       │
│   app/domains/*/services/           │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Repositories (Data Access)        │  ← 데이터 액세스
│   app/repositories/                 │  ✅ 여기로 이동!
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   ORM Models (Database Tables)      │  ← DB 테이블 매핑
│   app/models/                       │
└─────────────────────────────────────┘
```

## 💡 사용 예시

### 예시 1: 오케스트레이션 서비스에서 사용

```python
# app/orchestration/services/pipeline_service.py

from app.repositories import async_chain_execution_repo

class PipelineService:
    async def create_ai_pipeline(self, db: AsyncSession, request):
        # Repository를 통해 DB 접근
        chain_execution = await async_chain_execution_repo.create_chain_execution(
            db,
            chain_id=str(uuid.uuid4()),
            chain_name="ai_processing_pipeline",
            total_tasks=4,
        )

        return chain_execution
```

### 예시 2: 도메인 서비스에서 사용

```python
# app/domains/llm/services/llm_service.py

from app.repositories import async_task_log_repo

class LLMService:
    async def get_task_history(self, db: AsyncSession, task_id: str):
        # Repository를 통해 태스크 로그 조회
        task_log = await async_task_log_repo.get_by_task_id(db, task_id=task_id)
        return task_log
```

### 예시 3: API 컨트롤러에서 사용

```python
# app/api/v1/controllers/history_controller.py

from app.repositories import async_chain_execution_repo

@router.get("/history/{chain_id}")
async def get_history(chain_id: str, db: AsyncSession = Depends(get_db)):
    # Repository를 통해 파이프라인 히스토리 조회
    chain = await async_chain_execution_repo.get_with_task_logs(
        db, chain_id=chain_id
    )
    return ResponseBuilder.success(data=chain)
```

## 🔧 마이그레이션 가이드

### 단계 1: Import 경로 변경

**Before (기존):**
```python
from app.api.v1.crud import async_chain_execution
```

**After (개선):**
```python
from app.repositories import async_chain_execution_repo
```

### 단계 2: 메서드 호출 변경 (동일)

```python
# 사용법은 동일합니다
chain = await async_chain_execution_repo.get_by_chain_id(db, chain_id=chain_id)
```

### 단계 3: 하위 호환성

기존 코드와의 호환성을 위해 별칭을 제공합니다:

```python
# app/repositories/__init__.py

# 하위 호환성을 위한 별칭
from .chain_execution import async_chain_execution_repo as async_chain_execution
```

## 📝 도메인별 Repository 추가

### 도메인 전용 Repository 생성

LLM 도메인에서 대화 기록을 관리하는 경우:

```python
# app/domains/llm/repositories/conversation.py

from app.repositories.base import BaseRepository
from app.domains.llm.models.conversation import Conversation

class ConversationRepository(BaseRepository):
    """LLM 대화 기록 Repository"""

    async def get_by_user_id(self, db: AsyncSession, *, user_id: str):
        """사용자별 대화 기록 조회"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

# 인스턴스 생성
conversation_repo = ConversationRepository(Conversation)
```

### 도메인 서비스에서 사용

```python
# app/domains/llm/services/llm_service.py

from ..repositories.conversation import conversation_repo

class LLMService:
    async def get_user_conversations(self, db: AsyncSession, user_id: str):
        return await conversation_repo.get_by_user_id(db, user_id=user_id)
```

## 🆚 CRUD vs Repository 비교

| 항목 | CRUD (기존) | Repository (개선) |
|------|------------|------------------|
| **위치** | `app/api/v1/crud/` | `app/repositories/` |
| **의존성** | API 버전에 종속 | 독립적 |
| **명명** | `async_chain_execution` | `async_chain_execution_repo` |
| **목적** | 데이터 CRUD | 데이터 액세스 추상화 |
| **패턴** | 단순 CRUD | Repository Pattern |

## ✅ Repository 패턴의 장점

1. **관심사 분리**
   - 비즈니스 로직과 데이터 액세스 로직 분리
   - 각 레이어의 책임이 명확함

2. **테스트 용이성**
   - Repository를 Mock으로 대체하여 테스트 가능
   - DB 없이 비즈니스 로직 테스트

3. **유지보수성**
   - DB 변경 시 Repository만 수정
   - 비즈니스 로직 영향 최소화

4. **재사용성**
   - 여러 서비스에서 동일한 Repository 사용
   - API 버전과 무관하게 재사용

5. **확장성**
   - 캐싱, 로깅 등 추가 기능 쉽게 통합
   - 다른 데이터 소스로 전환 용이

## 🚨 주의사항

### 1. Repository는 순수 데이터 액세스만

❌ **잘못된 예**: Repository에 비즈니스 로직 포함
```python
class ChainExecutionRepository:
    async def create_and_notify(self, db, chain_id):
        # 생성
        chain = await self.create(...)

        # ❌ 비즈니스 로직 (알림 전송)
        await send_notification(chain.user_id)
```

✅ **올바른 예**: 비즈니스 로직은 Service에
```python
class PipelineService:
    async def create_pipeline(self, db, chain_id):
        # Repository: 데이터 저장만
        chain = await async_chain_execution_repo.create(...)

        # Service: 비즈니스 로직
        await self.notify_user(chain.user_id)
```

### 2. 트랜잭션 관리

Repository는 트랜잭션을 시작하지 않고, Service에서 관리:

```python
class PipelineService:
    async def create_complex_pipeline(self, db: AsyncSession):
        try:
            # 여러 Repository 호출을 하나의 트랜잭션으로
            chain = await chain_repo.create(...)
            task = await task_log_repo.create(...)

            await db.commit()  # Service에서 커밋
        except Exception:
            await db.rollback()  # Service에서 롤백
            raise
```

## 📚 추가 참고자료

- [아키텍처 개선 제안](./architecture-improvement.md)
- [오케스트레이션 레이어 가이드](./orchestration-layer-guide.md)
- [도메인 개발 가이드](./domain-setup-guide.md)