"""테스트용 Celery 태스크

테스트 및 개발 목적의 Celery 태스크 모음
"""

from typing import Any, Dict

from celery_app import celery_app
from shared.core.logging import get_logger
from shared.pipeline.exceptions import RetryableError

logger = get_logger(__name__)

def check_for_revoke(task_id: str) -> bool:
        """Celery AsyncResult를 통해 현재 태스크가 취소되었는지 확인합니다."""
        try:
            # 상태를 직접 쿼리하는 가장 견고한 방법 사용
            status = celery_app.AsyncResult(task_id).status
            return status == 'REVOKED'
        except Exception as e:
            logger.error(f"취소 상태 조회 중 오류 발생 (task_id: {task_id}): {e}")
            return False

@celery_app.task(
    bind=True,
    name="tasks.test_tasks",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def test_tasks(self, duration: int = 30, **kwargs) -> Dict[str, Any]:
    """테스트용 Celery 태스크

    지정된 시간 동안 실행되면서 진행 상황을 업데이트하는 태스크입니다.

    Args:
        duration: 실행 시간 (초, 기본값 30초)
        **kwargs: Celery 내부 인자 (options 등)

    Returns:
        실행 결과 정보
    """
    import time

    task_id = self.request.id
    logger.info(f"테스트 태스크 시작: task_id={task_id}, duration={duration}초")

    start_time = time.time()

    # 진행 상황을 10% 단위로 업데이트
    steps = 10
    step_duration = duration / steps

    for step in range(1, steps + 1):

        # 🚨 [핵심 로직]: 각 스텝 시작 시 취소 상태 확인
        if check_for_revoke(task_id):
            logger.warning(f"테스트 태스크 {task_id} 취소 요청 감지. 우아하게 종료합니다.")

            # 태스크 상태를 REVOKED로 최종 업데이트
            self.update_state(state='REVOKED', meta={'message': 'Task terminated gracefully by revoke'})

            # 작업을 즉시 종료하고 결과 반환
            return {
                'task_id': task_id,
                'status': 'revoked',
                'message': 'Task terminated gracefully by revoke command'
            }

        # 각 스텝마다 대기
        time.sleep(step_duration)

        # 진행률 계산
        progress = (step / steps) * 100
        elapsed = time.time() - start_time

        # 태스크 상태 업데이트
        self.update_state(
            state='PROGRESS',
            meta={
                'current': step,
                'total': steps,
                'progress': progress,
                'elapsed': round(elapsed, 2),
                'message': f'진행 중... {progress:.0f}%'
            }
        )

        logger.info(
            f"테스트 태스크 진행: task_id={task_id}, "
            f"progress={progress:.0f}%, elapsed={elapsed:.2f}초"
        )

    end_time = time.time()
    total_elapsed = end_time - start_time

    result = {
        'task_id': task_id,
        'status': 'completed',
        'duration': duration,
        'actual_elapsed': round(total_elapsed, 2),
        'steps': steps,
        'message': f'{duration}초 테스트 태스크 완료'
    }

    logger.info(f"테스트 태스크 완료: {result}")

    return result
