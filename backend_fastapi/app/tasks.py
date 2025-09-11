# app/tasks.py

import time
import json
import redis
from typing import Dict, Any, List, TypedDict, Optional

import logging
from .core.celery_app import celery_app
from .schemas.enums import ProcessStatus
from .schemas.stage import StageInfo
from .core.config import settings


# 4단계 AI 처리 작업들

# 타입 정의
class StageResult(TypedDict):
    chain_id: str
    result: str
    data: Dict[str, Any]
    execution_time: float
    stage: int

class PipelineStatusManager:
    """파이프라인 상태 관리 클래스"""
    
    def __init__(self):
        self._redis_client = None
    
    def get_redis_client(self) -> redis.Redis:
        """Redis 클라이언트 싱글톤 패턴으로 관리"""
        if not self._redis_client:
            self._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True
            )
        return self._redis_client
    
    def update_status(self, chain_id: str, stage: int, status: ProcessStatus, 
                     progress: int = 0, metadata: Optional[Dict] = None, task_id: Optional[str] = None) -> bool:
        """Redis에서 파이프라인 상태 업데이트 (배열 방식)"""
        try:
            redis_client = self.get_redis_client()
            
            logging.info(f"Pipeline {chain_id}: Stage {stage} - {status.value} ({progress}%)")
            
            # 기존 파이프라인 데이터 가져오기
            pipeline_data = redis_client.get(chain_id)
            
            if pipeline_data:
                # 기존 데이터가 있으면 배열로 불러오기
                pipeline_tasks = json.loads(pipeline_data)
                if not isinstance(pipeline_tasks, list):
                    # 레거시 데이터 처리 (객체인 경우 배열로 변환)
                    pipeline_tasks = [pipeline_tasks] if pipeline_tasks else []
            else:
                # 새로운 파이프라인인 경우 빈 배열로 시작
                pipeline_tasks = []
            
            # 현재 단계의 task 정보 생성
            current_task = {
                'chain_id': chain_id,
                'stage': stage,
                'status': status.value,
                'progress': progress,
                'updated_at': time.time(),
                'metadata': metadata or {}
            }

            # task_id가 제공된 경우 추가
            if task_id:
                current_task['task_id'] = task_id

            # task 시작 시 started_at 업데이트
            if status == ProcessStatus.PENDING and progress == 0 and metadata and 'start_time' in metadata:
                current_task['started_at'] = metadata['start_time']

            # 단계에 해당하는 task가 이미 있는지 확인
            stage_index = None
            for i, task in enumerate(pipeline_tasks):
                if task.get('stage') == stage:
                    stage_index = i
                    break

            if stage_index is not None:
                # 기존 단계 업데이트
                # 만약 created_at이 없다면, 현재 시간으로 설정하지 않고 기존 값 유지
                if 'created_at' not in current_task and 'created_at' in pipeline_tasks[stage_index]:
                    current_task['created_at'] = pipeline_tasks[stage_index]['created_at']
                # 만약 started_at이 없다면, 현재 시간으로 설정하지 않고 기존 값 유지
                if 'started_at' not in current_task and 'started_at' in pipeline_tasks[stage_index]:
                    current_task['started_at'] = pipeline_tasks[stage_index]['started_at']
                pipeline_tasks[stage_index].update(current_task)
            else:
                # 새로운 단계 추가
                # created_at이 없는 경우 현재 시간으로 설정
                if 'created_at' not in current_task:
                    current_task['created_at'] = time.time()
                pipeline_tasks.append(current_task)
            
            # 단계 순서대로 정렬
            pipeline_tasks.sort(key=lambda x: x.get('stage', 0))
            
            # TTL을 설정에서 가져오기 (기본값 3600초)
            ttl = getattr(settings, 'PIPELINE_TTL', 3600)
            redis_client.setex(chain_id, ttl, json.dumps(pipeline_tasks))
            return True
            
        except Exception as e:
            logging.error(f"Redis 파이프라인 상태 업데이트 실패 (Chain: {chain_id}): {e}")
            return False

    def get_pipeline_status(self, chain_id: str) -> Optional[List[Dict]]:
        """파이프라인 전체 상태 조회"""
        try:
            redis_client = self.get_redis_client()
            pipeline_data = redis_client.get(chain_id)
            
            if pipeline_data:
                pipeline_tasks = json.loads(pipeline_data)
                if isinstance(pipeline_tasks, list):
                    return pipeline_tasks
                else:
                    # 레거시 데이터 처리
                    return [pipeline_tasks] if pipeline_tasks else []
            return None
            
        except Exception as e:
            logging.error(f"Redis 파이프라인 상태 조회 실패 (Chain: {chain_id}): {e}")
            return None
    
    def get_stage_status(self, chain_id: str, stage: int) -> Optional[Dict]:
        """특정 단계의 상태 조회"""
        pipeline_tasks = self.get_pipeline_status(chain_id)
        if pipeline_tasks:
            for task in pipeline_tasks:
                if task.get('stage') == stage:
                    return task
        return None
    
    def delete_pipeline(self, chain_id: str) -> bool:
        """파이프라인 데이터 삭제"""
        try:
            redis_client = self.get_redis_client()
            result = redis_client.delete(chain_id)
            logging.info(f"Pipeline {chain_id} 데이터 삭제 {'completed' if result else 'failed'}")
            return bool(result)
        except Exception as e:
            logging.error(f"Redis 파이프라인 데이터 삭제 실패 (Chain: {chain_id}): {e}")
            return False
    
    def initialize_pipeline_stages(self, chain_id: str, input_data: Dict[str, Any]) -> bool:
        """파이프라인 시작 시 모든 스테이지 정보를 미리 생성"""
        try:
            redis_client = self.get_redis_client()
            
            # 4단계 스테이지 정보 스키마를 사용해서 생성
            stages = [
                StageInfo.create_pending_stage(
                    chain_id=chain_id,
                    stage=1,
                    stage_name='데이터 전처리',
                    description='입력 데이터 정제 및 전처리',
                    expected_duration='2-4초'
                ),
                StageInfo.create_pending_stage(
                    chain_id=chain_id,
                    stage=2,
                    stage_name='특성 추출',
                    description='텍스트 벡터화 및 특성 추출',
                    expected_duration='3-5초'
                ),
                StageInfo.create_pending_stage(
                    chain_id=chain_id,
                    stage=3,
                    stage_name='모델 추론',
                    description='AI 모델을 통한 추론 실행',
                    expected_duration='4-6초'
                ),
                StageInfo.create_pending_stage(
                    chain_id=chain_id,
                    stage=4,
                    stage_name='후처리',
                    description='결과 정리 및 최종 검증',
                    expected_duration='1-3초'
                )
            ]
            
            # 스키마를 딕셔너리로 변환해서 저장
            stages_info = [stage.to_dict() for stage in stages]
            
            # TTL을 설정에서 가져오기 (기본값 3600초)
            ttl = getattr(settings, 'PIPELINE_TTL', 3600)
            redis_client.setex(chain_id, ttl, json.dumps(stages_info))
            
            logging.info(f"Pipeline {chain_id}: 전체 스테이지 정보 초기화 완료 ({len(stages)}단계)")
            return True
            
        except Exception as e:
            logging.error(f"Pipeline {chain_id}: 스테이지 초기화 실패 - {e}")
            return False

# 전역 상태 관리자 인스턴스
status_manager = PipelineStatusManager()


def get_status_manager() -> PipelineStatusManager:
    """PipelineStatusManager 인스턴스를 반환 (의존성 주입용)"""
    return status_manager



# 유틸리티 함수들
def calculate_overall_progress(stage: int, stage_progress: int, total_stages: int) -> int:
    """전체 파이프라인 진행률 계산"""
    if total_stages == 0:
        return 0
    stage_weight = 100 / total_stages  # 전체 단계 수에 따라 가중치 동적 계산
    completed_stages = (stage - 1) * stage_weight
    current_stage_progress = (stage_progress / 100) * stage_weight
    return int(completed_stages + current_stage_progress)

def validate_stage_input(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """단계 간 데이터 전달 시 검증"""
    if not data or not isinstance(data, dict):
        logging.error("입력 데이터가 dict 타입이 아닙니다")
        return False
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logging.error(f"필수 필드 누락: {missing_fields}")
        return False
    return True

def validate_chain_id(chain_id: Optional[str]) -> bool:
    """체인 ID 유효성 검증"""
    if not chain_id or not isinstance(chain_id, str) or not chain_id.strip():
        logging.error("유효하지 않은 chain_id")
        return False
    return True

def create_stage_result(chain_id: str, stage: int, result_type: str, 
                       data: Dict[str, Any], execution_time: float) -> StageResult:
    """단계 결과 객체 생성 헬퍼 함수"""
    return {
        "chain_id": chain_id,
        "result": result_type,
        "data": data,
        "execution_time": execution_time,
        "stage": stage
    }

def handle_stage_error(self, chain_id: str, stage: int, stage_name: str, 
                      error: Exception, start_time: float) -> None:
    """단계 에러 처리 공통 로직"""
    execution_time = time.time() - start_time
    error_message = f"Chain {chain_id}: Stage {stage} ({stage_name}) 실패 - {str(error)}"
    logging.error(error_message)
    
    # Redis 상태 업데이트
    status_manager.update_status(chain_id, stage, ProcessStatus.FAILURE, 0,
                               {'error': str(error), 'execution_time': execution_time, 'stage_name': stage_name})
    
    # Celery에 에러 전파 (재시도 로직)
    raise self.retry(exc=error, countdown=60, max_retries=3)

def update_celery_progress(self, chain_id: str, stage: int, stage_name: str, status: str, 
                          progress: int) -> None:
    """셀러리 진행 상태 업데이트 공통 로직"""
    pipeline_status = status_manager.get_pipeline_status(chain_id)
    total_stages = len(pipeline_status) if pipeline_status else 0
    overall_progress = calculate_overall_progress(stage, progress, total_stages)
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': stage,
            'stage_name': stage_name,
            'status': status,
            'progress': progress,
            'overall_progress': overall_progress
        }
    )

def log_stage_metrics(chain_id: str, stage: int, stage_name: str, 
                     execution_time: float, input_size: int = 0):
    """단계별 메트릭 로깅"""
    logging.info(
        f"[METRICS] Chain: {chain_id} | Stage: {stage} | Name: {stage_name} | "
        f"Time: {execution_time:.2f}s | Input Size: {input_size}"
    )


@celery_app.task(bind=True, name="app.tasks.stage1_preprocessing")
def stage1_preprocessing(self, input_data: Dict[str, Any], chain_id: str = None) -> StageResult:
    """
    1단계: 데이터 전처리
    """
    start_time = time.time()
    stage_name = "데이터 전처리"
    
    # 체인 ID 및 입력 데이터 검증
    if not validate_chain_id(chain_id):
        raise ValueError("유효하지 않은 chain_id")
    
    if not input_data or not isinstance(input_data, dict):
        logging.error(f"Chain {chain_id}: Stage 1 입력 데이터 검증 실패")
        raise ValueError("입력 데이터가 유효하지 않습니다")
    
    input_size = len(str(input_data))
    logging.info(f"Chain {chain_id}: Stage 1 시작 - 입력 데이터 크기: {input_size} bytes")

    try:
        # Redis 파이프라인 상태 업데이트 (미리 초기화된 스테이지 정보를 업데이트)
        task_id = self.request.id  # Celery task ID
        status_manager.update_status(chain_id, 1, ProcessStatus.PENDING, 0, 
                                   {'stage_name': stage_name, 'start_time': start_time}, task_id=task_id)
        logging.info(f"Chain {chain_id}: Stage 1 상태 업데이트 완료 (Task ID: {task_id})")

        update_celery_progress(self, chain_id, 1, stage_name, '데이터 전처리 시작', 0)

        # 전처리 시뮬레이션
        logging.info(f"Chain {chain_id}: 데이터 전처리 시작")
        time.sleep(2)
        logging.info(f"Chain {chain_id}: 데이터 정제 완료")

        # Redis 파이프라인 상태 업데이트
        status_manager.update_status(chain_id, 1, ProcessStatus.PENDING, 50,
                                   {'stage_name': stage_name, 'substep': '데이터 정제'}, task_id=task_id)

        update_celery_progress(self, chain_id, 1, stage_name, '데이터 정제 중', 50)

        time.sleep(2)
        logging.info(f"Chain {chain_id}: 데이터 전처리 마무리")

        # 실행 시간 계산
        execution_time = time.time() - start_time
        
        # Redis 파이프라인 상태 업데이트 - 완료
        status_manager.update_status(chain_id, 1, ProcessStatus.SUCCESS, 100,
                                   {'stage_name': stage_name, 'execution_time': execution_time}, task_id=task_id)
        
        # 메트릭 로깅
        log_stage_metrics(chain_id, 1, stage_name, execution_time, input_size)
        
        # 다음 stage로 전달할 데이터
        return create_stage_result(chain_id, 1, "stage1_completed", input_data, execution_time)

    except Exception as e:
        handle_stage_error(self, chain_id, 1, stage_name, e, start_time)
        raise Exception from e

@celery_app.task(bind=True, name="app.tasks.stage2_feature_extraction")
def stage2_feature_extraction(self, stage1_result: Dict[str, Any]) -> StageResult:
    """
    2단계: 특성 추출
    """
    start_time = time.time()
    stage_name = "특성 추출"
    
    # stage1에서 전달받은 chain_id 추출
    if not validate_stage_input(stage1_result, ['chain_id']):
        raise ValueError("Stage 1 결과 데이터가 유효하지 않습니다")
    
    chain_id = stage1_result.get("chain_id")
    input_size = len(str(stage1_result))
    logging.info(f"Chain {chain_id}: Stage 2 시작 - 입력 데이터 크기: {input_size} bytes")

    try:
        # Redis 파이프라인 상태 업데이트
        task_id = self.request.id  # Celery task ID
        status_manager.update_status(chain_id, 2, ProcessStatus.PENDING, 0,
                                   {'stage_name': stage_name, 'start_time': start_time}, task_id=task_id)

        update_celery_progress(self, chain_id, 2, stage_name, '특성 추출 시작', 0)

        logging.info(f"Chain {chain_id}: 특성 추출 시작")
        time.sleep(3)
        logging.info(f"Chain {chain_id}: 벡터화 진행 중")

        # Redis 파이프라인 상태 업데이트
        status_manager.update_status(chain_id, 2, ProcessStatus.PENDING, 70,
                                   {'stage_name': stage_name, 'substep': '벡터화'}, task_id=task_id)

        update_celery_progress(self, chain_id, 2, stage_name, '벡터화 진행 중', 70)

        time.sleep(2)
        logging.info(f"Chain {chain_id}: 특성 추출 완료")

        # 실행 시간 계산
        execution_time = time.time() - start_time

        # Redis 파이프라인 상태 업데이트 - 완료
        status_manager.update_status(chain_id, 2, ProcessStatus.SUCCESS, 100,
                                   {'stage_name': stage_name, 'execution_time': execution_time}, task_id=task_id)
        
        # 메트릭 로깅
        log_stage_metrics(chain_id, 2, stage_name, execution_time, input_size)
        
        # 다음 stage로 전달할 데이터
        return create_stage_result(chain_id, 2, "stage2_completed", stage1_result, execution_time)

    except Exception as e:
        handle_stage_error(self, chain_id, 2, stage_name, e, start_time)
        raise Exception from e

@celery_app.task(bind=True, name="app.tasks.stage3_model_inference")
def stage3_model_inference(self, stage2_result: Dict[str, Any]) -> StageResult:
    """
    3단계: 모델 추론
    """
    start_time = time.time()
    stage_name = "모델 추론"
    
    # stage2에서 전달받은 chain_id 추출
    if not validate_stage_input(stage2_result, ['chain_id']):
        raise ValueError("Stage 2 결과 데이터가 유효하지 않습니다")
    
    chain_id = stage2_result.get("chain_id")
    input_size = len(str(stage2_result))
    logging.info(f"Chain {chain_id}: Stage 3 시작 - 입력 데이터 크기: {input_size} bytes")

    try:
        # Redis 파이프라인 상태 업데이트
        task_id = self.request.id  # Celery task ID
        status_manager.update_status(chain_id, 3, ProcessStatus.PENDING, 0,
                                   {'stage_name': stage_name, 'start_time': start_time}, task_id=task_id)

        update_celery_progress(self, chain_id, 3, stage_name, '모델 로딩 중', 0)

        logging.info(f"Chain {chain_id}: 모델 로딩 시작")
        time.sleep(2)
        logging.info(f"Chain {chain_id}: 모델 로딩 완료, 추론 시작")

        # Redis 파이프라인 상태 업데이트
        status_manager.update_status(chain_id, 3, ProcessStatus.PENDING, 40,
                                   {'stage_name': stage_name, 'substep': '추론 실행'}, task_id=task_id)

        update_celery_progress(self, chain_id, 3, stage_name, '추론 실행 중', 40)

        time.sleep(4)
        logging.info(f"Chain {chain_id}: 모델 추론 완료")

        # 실행 시간 계산
        execution_time = time.time() - start_time

        # Redis 파이프라인 상태 업데이트 - 완료
        status_manager.update_status(chain_id, 3, ProcessStatus.SUCCESS, 100,
                                   {'stage_name': stage_name, 'execution_time': execution_time}, task_id=task_id)
        
        # 메트릭 로깅
        log_stage_metrics(chain_id, 3, stage_name, execution_time, input_size)
        
        # 다음 stage로 전달할 데이터
        return create_stage_result(chain_id, 3, "stage3_completed", stage2_result, execution_time)

    except Exception as e:
        handle_stage_error(self, chain_id, 3, stage_name, e, start_time)
        raise Exception from e

@celery_app.task(bind=True, name="app.tasks.stage4_post_processing")
def stage4_post_processing(self, stage3_result: Dict[str, Any]) -> StageResult:
    """
    4단계: 후처리 및 결과 정리
    """
    start_time = time.time()
    stage_name = "후처리"
    
    # stage3에서 전달받은 chain_id 추출
    if not validate_stage_input(stage3_result, ['chain_id']):
        raise ValueError("Stage 3 결과 데이터가 유효하지 않습니다")
    
    chain_id = stage3_result.get("chain_id")
    input_size = len(str(stage3_result))
    logging.info(f"Chain {chain_id}: Stage 4 시작 - 입력 데이터 크기: {input_size} bytes")

    try:
        # Redis 파이프라인 상태 업데이트
        task_id = self.request.id  # Celery task ID
        status_manager.update_status(chain_id, 4, ProcessStatus.PENDING, 0,
                                   {'stage_name': stage_name, 'start_time': start_time}, task_id=task_id)

        update_celery_progress(self, chain_id, 4, stage_name, '결과 정리 중', 0)

        logging.info(f"Chain {chain_id}: 후처리 시작")
        time.sleep(2)
        logging.info(f"Chain {chain_id}: 최종 검증 시작")

        # Redis 파이프라인 상태 업데이트
        status_manager.update_status(chain_id, 4, ProcessStatus.PENDING, 80,
                                   {'stage_name': stage_name, 'substep': '최종 검증'}, task_id=task_id)

        update_celery_progress(self, chain_id, 4, stage_name, '최종 검증 중', 80)

        time.sleep(1)
        logging.info(f"Chain {chain_id}: 파이프라인 완료")

        # 실행 시간 계산
        execution_time = time.time() - start_time

        # Redis 파이프라인 상태 업데이트 - 완료
        status_manager.update_status(chain_id, 4, ProcessStatus.SUCCESS, 100,
                                   {'stage_name': stage_name, 'execution_time': execution_time}, task_id=task_id)
        
        # 메트릭 로깅
        log_stage_metrics(chain_id, 4, stage_name, execution_time, input_size)
        
        # 최종 결과 반환
        return create_stage_result(chain_id, 4, "pipeline_completed", stage3_result, execution_time)

    except Exception as e:
        handle_stage_error(self, chain_id, 4, stage_name, e, start_time)
        raise Exception from e