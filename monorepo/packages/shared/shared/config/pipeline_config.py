# app/pipeline_config.py

STAGES = [
    {
        "stage": 1,
        "name": "데이터 전처리",
        "task_name": "app.tasks.stage1_preprocessing",
        "description": "입력 데이터 정제 및 전처리",
        "expected_duration": "2-4초",
    },
    {
        "stage": 2,
        "name": "특성 추출",
        "task_name": "app.tasks.stage2_feature_extraction",
        "description": "텍스트 벡터화 및 특성 추출",
        "expected_duration": "3-5초",
    },
    {
        "stage": 3,
        "name": "모델 추론",
        "task_name": "app.tasks.stage3_model_inference",
        "description": "AI 모델을 통한 추론 실행",
        "expected_duration": "4-6초",
    },
    {
        "stage": 4,
        "name": "후처리",
        "task_name": "app.tasks.stage4_post_processing",
        "description": "결과 정리 및 최종 검증",
        "expected_duration": "1-3초",
    },
]
