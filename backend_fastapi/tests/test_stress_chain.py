
# tests/test_stress_chain.py

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.core.config import settings
from app.models.base import Base
from app.services.pipeline_service import PipelineService
from app.services.status_manager import RedisPipelineStatusManager
from app.schemas.pipeline import AIPipelineRequest
from app.crud.async_crud.chain_execution import chain_execution as chain_execution_crud

# .env 파일의 DATABASE_URL을 사용하도록 설정
ASYNC_SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL

# 테스트용 비동기 in-memory SQLite 데이터베이스 설정                                                                                                                                                                                                      │
# --- 3. 데이터 삭제 함수 ---

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """테스트용 비동기 엔진 생성 (함수 스코프)"""
    engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # print("--- 모든 테이블의 데이터 삭제 시작 ---")
    yield engine

    async with engine.begin() as conn:
        print("--- 모든 테이블의 데이터 삭제 시작 ---")
        for table in reversed(Base.metadata.sorted_tables):
            print(f"Deleting data from table: {table.name}")
            await conn.execute(table.delete())
        print("--- 모든 테이블의 데이터 삭제 완료 ---")

    await engine.dispose()

@pytest_asyncio.fixture
async def session_maker(async_engine):
    """비동기 데이터베이스 세션 메이커 fixture"""
    return sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.mark.asyncio
async def test_run_1000_chains_concurrently(session_maker):
    """1000개의 체인을 동시에 실행하는 스트레스 테스트"""
    # given
    num_chains = 1000
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

    async def run_single_pipeline(request: AIPipelineRequest):
        """각 파이프라인을 독립적인 세션에서 실행하는 헬퍼 함수"""
        async with session_maker() as session:
            pipeline_service = PipelineService()
            return await pipeline_service.create_ai_pipeline(
                db=session, status_manager=redis_manager, request=request
            )

    tasks = [run_single_pipeline(req) for req in requests]

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
    async with session_maker() as session:
        all_chains = await chain_execution_crud.get_all(db=session)
        assert len(all_chains) == num_chains
