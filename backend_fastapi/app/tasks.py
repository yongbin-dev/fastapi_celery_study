# app/tasks_router.py

import time
from typing import Dict, Any

from .core.celery_app import celery_app

# 4단계 AI 처리 작업들
def update_pipeline_redis_status(pipeline_id: str, stage: int, status: str, progress: int = 0):
    """Redis에서 파이프라인 상태 업데이트"""
    import redis
    import json
    from .core.config import settings
    
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
        
        pipeline_key = f"pipeline:{pipeline_id}"
        pipeline_data = redis_client.get(pipeline_key)
        
        if pipeline_data:
            state_info = json.loads(pipeline_data)
            
            # 해당 단계 상태 업데이트
            for stage_info in state_info.get("stages", []):
                if stage_info["stage"] == stage:
                    stage_info["status"] = status
                    stage_info["progress"] = progress
                    break
            
            # 현재 진행 단계 업데이트
            if status == "STARTED" or status == "PROGRESS":
                state_info["current_stage"] = stage
                state_info["status"] = "PROGRESS"

            elif status == "SUCCESS":
                # 모든 단계가 완료되었는지 확인
                all_completed = all(s["status"] == "SUCCESS" for s in state_info["stages"])
                if all_completed:
                    state_info["status"] = "SUCCESS"
                    state_info["current_stage"] = len(state_info["stages"])

            elif status == "FAILURE":
                state_info["status"] = "FAILURE"
                state_info["current_stage"] = stage
            
            # Redis 업데이트
            redis_client.setex(pipeline_key, 3600, json.dumps(state_info))
    except Exception as e:
        print(f"Redis 파이프라인 상태 업데이트 실패: {e}")

@celery_app.task(bind=True, name="app.tasks.stage1_preprocessing")
def stage1_preprocessing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    1단계: 데이터 전처리
    """
    # 파이프라인 ID 추출 (root task ID 사용)
    pipeline_id = self.request.root_id or self.request.id
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 1, "STARTED", 0)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 1,
            'stage_name': '데이터 전처리',
            'status': '데이터 전처리 시작',
            'progress': 0
        }
    )
    
    # 전처리 시뮬레이션
    time.sleep(2)
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 1, "PROGRESS", 50)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 1,
            'stage_name': '데이터 전처리',
            'status': '데이터 정제 중',
            'progress': 50
        }
    )
    
    time.sleep(2)
    
    # Redis 파이프라인 상태 업데이트 - 완료
    update_pipeline_redis_status(pipeline_id, 1, "SUCCESS", 100)
    
    result = {
        'stage': 1,
        'stage_name': '데이터 전처리',
        'input_data': input_data,
        'preprocessed_data': f"전처리된_{input_data.get('text', '')}",
        'metadata': {
            'processing_time': 4,
            'cleaned_tokens': 150,
            'original_length': len(input_data.get('text', '')),
        },
        'status': 'completed'
    }
    
    return result


@celery_app.task(bind=True, name="app.tasks.stage2_feature_extraction")
def stage2_feature_extraction(self, stage1_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    2단계: 특성 추출
    """
    # 파이프라인 ID 추출
    pipeline_id = self.request.root_id or self.request.id
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 2, "STARTED", 0)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 2,
            'stage_name': '특성 추출',
            'status': '특성 추출 시작',
            'progress': 0
        }
    )
    
    time.sleep(3)
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 2, "PROGRESS", 70)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 2,
            'stage_name': '특성 추출',
            'status': '벡터화 진행 중',
            'progress': 70
        }
    )
    
    time.sleep(2)
    
    # Redis 파이프라인 상태 업데이트 - 완료
    update_pipeline_redis_status(pipeline_id, 2, "SUCCESS", 100)
    
    result = {
        'stage': 2,
        'stage_name': '특성 추출',
        'previous_result': stage1_result,
        'features': {
            'embeddings': [0.1, 0.2, 0.3, 0.4],  # 예시 임베딩
            'feature_count': 512,
            'extraction_method': 'transformer'
        },
        'metadata': {
            'processing_time': 5,
            'vector_dimension': 512
        },
        'status': 'completed'
    }
    
    return result


@celery_app.task(bind=True, name="app.tasks.stage3_model_inference")
def stage3_model_inference(self, stage2_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    3단계: 모델 추론
    """
    # 파이프라인 ID 추출
    pipeline_id = self.request.root_id or self.request.id
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 3, "STARTED", 0)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 3,
            'stage_name': '모델 추론',
            'status': '모델 로딩 중',
            'progress': 0
        }
    )
    
    time.sleep(2)
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 3, "PROGRESS", 40)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 3,
            'stage_name': '모델 추론',
            'status': '추론 실행 중',
            'progress': 40
        }
    )
    
    time.sleep(4)
    
    # Redis 파이프라인 상태 업데이트 - 완료
    update_pipeline_redis_status(pipeline_id, 3, "SUCCESS", 100)
    
    result = {
        'stage': 3,
        'stage_name': '모델 추론',
        'previous_result': stage2_result,
        'prediction': {
            'confidence': 0.89,
            'predicted_class': 'positive',
            'probabilities': {'positive': 0.89, 'negative': 0.11}
        },
        'metadata': {
            'model_name': 'bert-base-korean',
            'inference_time': 6,
            'gpu_used': False
        },
        'status': 'completed'
    }
    
    return result


@celery_app.task(bind=True, name="app.tasks.stage4_post_processing")
def stage4_post_processing(self, stage3_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    4단계: 후처리 및 결과 정리
    """
    # 파이프라인 ID 추출
    pipeline_id = self.request.root_id or self.request.id
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 4, "STARTED", 0)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 4,
            'stage_name': '후처리',
            'status': '결과 정리 중',
            'progress': 0
        }
    )
    
    time.sleep(2)
    
    # Redis 파이프라인 상태 업데이트
    update_pipeline_redis_status(pipeline_id, 4, "PROGRESS", 80)
    
    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 4,
            'stage_name': '후처리',
            'status': '최종 검증 중',
            'progress': 80
        }
    )
    
    time.sleep(1)
    
    # Redis 파이프라인 상태 업데이트 - 완료
    update_pipeline_redis_status(pipeline_id, 4, "SUCCESS", 100)
    
    # 모든 단계 결과 통합
    final_result = {
        'stage': 4,
        'stage_name': '후처리',
        'pipeline_results': {
            'stage1': stage3_result['previous_result']['previous_result'],
            'stage2': stage3_result['previous_result'],
            'stage3': stage3_result,
            'stage4': {
                'final_output': f"최종 결과: {stage3_result['prediction']['predicted_class']}",
                'confidence_score': stage3_result['prediction']['confidence'],
                'processing_complete': True
            }
        },
        'summary': {
            'total_processing_time': 20,  # 전체 소요 시간
            'pipeline_status': 'success',
            'final_prediction': stage3_result['prediction']['predicted_class'],
            'confidence': stage3_result['prediction']['confidence']
        },
        'status': 'completed'
    }
    
    return final_result


@celery_app.task(bind=True, name="app.tasks.ai_pipeline_orchestrator")
def ai_pipeline_orchestrator(self, input_data: Dict[str, Any]) -> str:
    """
    AI 처리 파이프라인 오케스트레이터 - 4단계 체인 실행
    """
    from celery import chain
    
    # 체인 작업 생성: stage1 -> stage2 -> stage3 -> stage4
    pipeline = chain(

        stage1_preprocessing.s(input_data),
        stage2_feature_extraction.s(),
        stage3_model_inference.s(),
        stage4_post_processing.s()
    )
    
    # 체인 실행
    result = pipeline.apply_async()

    return result  # 최종 작업 ID 반환

