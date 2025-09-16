
# tests/test_stress_chain.py

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.models.base import Base
from app.services.pipeline_service import PipelineService
from app.services.status_manager import RedisPipelineStatusManager
from app.schemas.pipeline import AIPipelineRequest
from app.crud.async_crud.chain_execution import chain_execution as chain_execution_crud

# 테스트용 비동기 in-memory SQLite 데이터베이스 설정
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="module")
async def async_engine():
    """테스트용 비동기 엔진 생성 (모듈 스코프)"""
    engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(async_engine):
    """비동기 데이터베이스 세션 fixture"""
    AsyncTestingSessionLocal = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncTestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_run_1000_chains_concurrently(db_session: AsyncSession):
    """1000개의 체인을 동시에 실행하는 스트레스 테스트"""
    # given
    num_chains = 1000
    pipeline_service = PipelineService()
    # 실제 Redis를 사용한다고 가정합니다. 테스트 환경에 따라 mock으로 대체할 수 있습니다.
    redis_manager = RedisPipelineStatusManager()

    # when
    requests = [
        AIPipelineRequest(
            text=f"Stress test message {i}",
            options={"param": "value"},
            priority=1,
            callback_url="http://localhost/callback"
        )
        for i in range(num_chains)
    ]

    tasks = [
        pipeline_service.create_ai_pipeline(db=db_session, status_manager=redis_manager, request=req)
        for req in requests
    ]

    # asyncio.gather를 사용하여 모든 파이프라인 생성 작업을 동시에 실행
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # then
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    failure_count = len(results) - success_count

    print(f"Total chains attempted: {num_chains}")
    print(f"Successful creations: {success_count}")
    print(f"Failed creations: {failure_count}")

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error for task {i}: {result}")

    # 모든 요청이 성공적으로 처리되었는지 확인
    assert success_count == num_chains, f"{failure_count} chains failed to create."

    # 데이터베이스에 실제로 레코드가 생성되었는지 확인
    all_chains = await chain_execution_crud.get_all(db=db_session)
    assert len(all_chains) == num_chains
