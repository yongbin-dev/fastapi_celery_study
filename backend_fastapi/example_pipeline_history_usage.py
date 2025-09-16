# example_pipeline_history_usage.py
"""
get_pipeline_history DB 조회 기능 사용 예제 (AsyncSession 버전)
"""

import asyncio
from app.services.pipeline_service import get_pipeline_service
from app.core.database import get_db_manager

async def example_usage():
    """get_pipeline_history 사용 예제 (비동기)"""

    # 1. 서비스 인스턴스 가져오기
    pipeline_service = get_pipeline_service()

    # 2. AsyncSession 사용
    async with get_db_manager().get_async_session() as db:

        # 3. 최근 24시간 동안의 모든 파이프라인 히스토리 조회
        pipeline_histories = await pipeline_service.get_pipeline_history(
            db=db,
            hours=24,
            limit=50
        )

        print(f"총 {len(pipeline_histories)}개의 파이프라인 조회됨")

        # 4. 각 파이프라인 정보 출력
        for pipeline in pipeline_histories:
            print(f"\n=== Pipeline: {pipeline.chain_id} ===")
            print(f"총 단계: {pipeline.total_stages}")
            print(f"현재 단계: {pipeline.current_stage}")
            print(f"전체 진행률: {pipeline.overall_progress}%")
            print(f"완료된 단계: {pipeline.completed_stages}")
            print(f"실패한 단계: {pipeline.failed_stages}")

            print("\n단계별 상세 정보:")
            for stage in pipeline.stages:
                print(f"  Stage {stage.stage}: {stage.stage_name}")
                print(f"    상태: {stage.status}")
                print(f"    진행률: {stage.progress}%")
                if stage.task_id:
                    print(f"    Task ID: {stage.task_id}")
                if stage.error_message:
                    print(f"    오류: {stage.error_message}")
                print()

        # 5. 특정 상태의 파이프라인만 조회
        success_pipelines = await pipeline_service.get_pipeline_history(
            db=db,
            hours=24,
            status="SUCCESS",
            limit=10
        )

        print(f"\n성공한 파이프라인: {len(success_pipelines)}개")

        # 6. 실패한 파이프라인만 조회
        failed_pipelines = await pipeline_service.get_pipeline_history(
            db=db,
            hours=24,
            status="FAILURE",
            limit=10
        )

        print(f"실패한 파이프라인: {len(failed_pipelines)}개")

if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(example_usage())