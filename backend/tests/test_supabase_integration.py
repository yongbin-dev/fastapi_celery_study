# tests/test_supabase_integration.py
"""
Supabase 통합 테스트

실행 방법:
    pytest tests/test_supabase_integration.py -v
"""

import uuid

import pytest
from supabase import create_client

from app.config import settings
from app.orchestration.schemas.enums import ProcessStatus
from app.repository.crud.supabase_crud import supabase_chain_execution


@pytest.fixture
def supabase_client():
    """Supabase 클라이언트 픽스처"""
    client = create_client(
        settings.NEXT_PUBLIC_SUPABASE_URL, settings.NEXT_PUBLIC_SUPABASE_ANON_KEY
    )
    return client


@pytest.fixture
def sample_chain_id():
    """테스트용 chain_id 생성"""
    return str(uuid.uuid4())


@pytest.mark.asyncio
async def test_create_chain_execution(supabase_client, sample_chain_id):
    """ChainExecution 생성 테스트"""
    chain_execution = await supabase_chain_execution.create_chain_execution(
        supabase_client,
        chain_id=sample_chain_id,
        chain_name="test_pipeline",
        total_tasks=3,
        initiated_by="test_user",
        input_data={"test": "data"},
    )

    assert chain_execution is not None
    assert chain_execution.get("chain_id") == sample_chain_id
    assert chain_execution.get("chain_name") == "test_pipeline"
    assert chain_execution.get("status") == ProcessStatus.PENDING.value
    assert chain_execution.get("total_tasks") == 3
    assert chain_execution.get("completed_tasks") == 0


@pytest.mark.asyncio
async def test_get_by_chain_id(supabase_client, sample_chain_id):
    """chain_id로 조회 테스트"""
    # 먼저 생성
    await supabase_chain_execution.create_chain_execution(
        supabase_client,
        chain_id=sample_chain_id,
        chain_name="test_pipeline",
        total_tasks=3,
    )

    # 조회
    result = await supabase_chain_execution.get_by_chain_id(
        supabase_client, chain_id=sample_chain_id
    )

    assert result is not None
    assert result.get("chain_id") == sample_chain_id


@pytest.mark.asyncio
async def test_increment_completed_tasks(supabase_client, sample_chain_id):
    """완료 작업 수 증가 테스트"""
    # 생성
    await supabase_chain_execution.create_chain_execution(
        supabase_client,
        chain_id=sample_chain_id,
        chain_name="test_pipeline",
        total_tasks=3,
    )

    # 완료 작업 수 증가
    updated = await supabase_chain_execution.increment_completed_tasks(
        supabase_client, chain_id=sample_chain_id
    )

    assert updated is not None
    assert updated.get("completed_tasks") == 1


@pytest.mark.asyncio
async def test_increment_failed_tasks(supabase_client, sample_chain_id):
    """실패 작업 수 증가 테스트"""
    # 생성
    await supabase_chain_execution.create_chain_execution(
        supabase_client,
        chain_id=sample_chain_id,
        chain_name="test_pipeline",
        total_tasks=3,
    )

    # 실패 작업 수 증가
    updated = await supabase_chain_execution.increment_failed_tasks(
        supabase_client, chain_id=sample_chain_id
    )

    assert updated is not None
    assert updated.get("failed_tasks") == 1


@pytest.mark.asyncio
async def test_update_status(supabase_client, sample_chain_id):
    """상태 업데이트 테스트"""
    # 생성
    await supabase_chain_execution.create_chain_execution(
        supabase_client,
        chain_id=sample_chain_id,
        chain_name="test_pipeline",
        total_tasks=3,
    )

    # 상태 업데이트
    updated = await supabase_chain_execution.update_status(
        supabase_client, chain_id=sample_chain_id, status=ProcessStatus.STARTED
    )

    assert updated is not None
    assert updated.get("status") == ProcessStatus.STARTED.value
    assert updated.get("started_at") is not None


@pytest.mark.asyncio
async def test_complete_workflow(supabase_client, sample_chain_id):
    """전체 워크플로우 테스트"""
    # 1. 생성
    chain = await supabase_chain_execution.create_chain_execution(
        supabase_client,
        chain_id=sample_chain_id,
        chain_name="complete_workflow_test",
        total_tasks=3,
        initiated_by="test_system",
    )
    assert chain.get("status") == ProcessStatus.PENDING.value

    # 2. 시작 상태로 변경
    await supabase_chain_execution.update_status(
        supabase_client, chain_id=sample_chain_id, status=ProcessStatus.STARTED
    )

    # 3. 작업 완료 (3개)
    for i in range(3):
        await supabase_chain_execution.increment_completed_tasks(
            supabase_client, chain_id=sample_chain_id
        )

    # 4. 최종 확인
    final = await supabase_chain_execution.get_by_chain_id(
        supabase_client, chain_id=sample_chain_id
    )

    assert final.get("completed_tasks") == 3
    assert final.get("status") == ProcessStatus.SUCCESS.value
    assert final.get("finished_at") is not None


@pytest.mark.asyncio
async def test_get_all_chain_executions(supabase_client):
    """전체 체인 실행 조회 테스트"""
    # 여러 체인 생성
    chain_ids = [str(uuid.uuid4()) for _ in range(3)]

    for chain_id in chain_ids:
        await supabase_chain_execution.create_chain_execution(
            supabase_client,
            chain_id=chain_id,
            chain_name=f"test_pipeline_{chain_id}",
            total_tasks=2,
        )

    # 전체 조회
    all_chains = await supabase_chain_execution.get_all_chain_executions(
        supabase_client
    )

    assert len(all_chains) >= 3


@pytest.mark.asyncio
async def test_error_handling(supabase_client):
    """에러 처리 테스트"""
    # 존재하지 않는 chain_id 조회
    result = await supabase_chain_execution.get_by_chain_id(
        supabase_client, chain_id="non-existent-chain-id"
    )

    assert result is None


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup(supabase_client, sample_chain_id):
    """각 테스트 후 정리"""
    yield
    # 테스트 후 생성된 데이터 삭제 (선택사항)
    # 실제 운영에서는 삭제하지 않음
    pass


if __name__ == "__main__":
    # 직접 실행 시
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
