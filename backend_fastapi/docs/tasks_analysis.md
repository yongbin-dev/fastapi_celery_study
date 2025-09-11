# Tasks.py 분석 문서

## 개요
`app/tasks.py`는 Celery를 이용한 4단계 AI 처리 파이프라인을 구현한 파일입니다. 각 단계는 체이닝 방식으로 연결되어 순차적으로 실행됩니다.

## 주요 구성 요소

### 1. 의존성 및 임포트
```python
import time
from typing import Dict, Any
import logging
from .core.celery_app import celery_app
from .schemas.enums import ProcessStatus
```

### 2. 유틸리티 함수

#### `update_pipeline_redis_status()`
- **목적**: Redis에서 파이프라인 실행 상태 업데이트
- **매개변수**:
  - `chain_id`: 파이프라인 실행 체인 ID
  - `stage`: 현재 단계 번호 (1-4)
  - `status`: 현재 상태 (`ProcessStatus` enum 값)
  - `progress`: 진행률 (0-100)
- **기능**: Redis에서 파이프라인 데이터를 조회하고 상태 정보를 업데이트하여 3600초 TTL로 저장

## 파이프라인 단계별 분석

### Stage 1: 데이터 전처리 (`stage1_preprocessing`)

**파일 위치**: `app/tasks.py:37-91`

**기능**:
- 입력 데이터의 전처리 및 정제
- 진행률: 0% → 50% → 100%
- 실행 시간: 총 4초 (2초 + 2초)

**주요 작업 흐름**:
1. Redis 상태를 `PENDING`으로 업데이트
2. Celery 작업 상태를 `PROGRESS`로 설정
3. 2초간 전처리 시뮬레이션
4. 진행률 50%로 업데이트 ("데이터 정제 중")
5. 2초간 추가 처리
6. 완료 상태로 업데이트 (`SUCCESS`)

**반환값**:
```python
{
    "chain_id": chain_id, 
    "result": "stage1_completed", 
    "data": input_data
}
```

**에러 처리**:
- 예외 발생 시 Redis 상태를 `FAILURE`로 설정
- 60초 후 재시도, 최대 3회 재시도

### Stage 2: 특성 추출 (`stage2_feature_extraction`)

**파일 위치**: `app/tasks.py:93-137`

**기능**:
- 전처리된 데이터에서 특성 추출 및 벡터화
- 진행률: 0% → 70% → 100%
- 실행 시간: 총 5초 (3초 + 2초)

**주요 작업 흐름**:
1. Stage 1에서 `chain_id` 추출
2. "특성 추출 시작" 상태로 초기화
3. 3초간 특성 추출 시뮬레이션
4. 진행률 70%로 업데이트 ("벡터화 진행 중")
5. 2초간 벡터화 처리
6. 완료 상태로 업데이트

**반환값**:
```python
{
    "chain_id": chain_id, 
    "result": "stage2_completed", 
    "stage1_data": stage1_result
}
```

### Stage 3: 모델 추론 (`stage3_model_inference`)

**파일 위치**: `app/tasks.py:139-182`

**기능**:
- AI 모델을 이용한 추론 실행
- 진행률: 0% → 40% → 100%
- 실행 시간: 총 6초 (2초 + 4초)

**주요 작업 흐름**:
1. Stage 2에서 `chain_id` 추출
2. "모델 로딩 중" 상태로 초기화
3. 2초간 모델 로딩 시뮬레이션
4. 진행률 40%로 업데이트 ("추론 실행 중")
5. 4초간 추론 실행
6. 완료 상태로 업데이트

**반환값**:
```python
{
    "chain_id": chain_id, 
    "result": "stage3_completed", 
    "stage2_data": stage2_result
}
```

### Stage 4: 후처리 (`stage4_post_processing`)

**파일 위치**: `app/tasks.py:184-228`

**기능**:
- 추론 결과의 후처리 및 최종 정리
- 진행률: 0% → 80% → 100%
- 실행 시간: 총 3초 (2초 + 1초)

**주요 작업 흐름**:
1. Stage 3에서 `chain_id` 추출
2. "결과 정리 중" 상태로 초기화
3. 2초간 결과 정리 시뮬레이션
4. 진행률 80%로 업데이트 ("최종 검증 중")
5. 1초간 최종 검증
6. 완료 상태로 업데이트

**최종 반환값**:
```python
{
    "chain_id": chain_id, 
    "result": "pipeline_completed", 
    "stage3_data": stage3_result
}
```

## 주요 특징

### 1. 체이닝 아키텍처
- 각 단계의 출력이 다음 단계의 입력이 되는 체인 구조
- `chain_id`를 통해 파이프라인 전체 추적 가능

### 2. 실시간 상태 추적
- **Celery**: 작업 자체의 진행 상태 추적
- **Redis**: 파이프라인 전체 상태 추적 (3600초 TTL)

### 3. 에러 처리
- Stage 1에만 재시도 로직 구현
- Redis 상태 업데이트 실패에 대한 예외 처리

### 4. 진행률 관리
- 각 단계별로 세분화된 진행률 업데이트
- 사용자에게 실시간 피드백 제공

## 실행 시간 분석

| 단계 | 작업 내용 | 소요 시간 | 누적 시간 |
|------|----------|----------|----------|
| Stage 1 | 데이터 전처리 | 4초 | 4초 |
| Stage 2 | 특성 추출 | 5초 | 9초 |
| Stage 3 | 모델 추론 | 6초 | 15초 |
| Stage 4 | 후처리 | 3초 | 18초 |

**전체 파이프라인 실행 시간**: 약 18초

## 개선 제안

1. **에러 처리 일관성**: 모든 단계에 재시도 로직 추가
2. **로깅 강화**: 각 단계별 상세 로그 추가
3. **설정 분리**: 하드코딩된 시간 값들을 설정 파일로 분리
4. **타입 힌트 보완**: 반환 타입 명시
5. **상태 코드 표준화**: Redis 상태 업데이트 시 문자열 대신 enum 사용

## 연관 파일

- `app/core/celery_app.py`: Celery 애플리케이션 설정
- `app/schemas/enums.py`: ProcessStatus enum 정의
- `app/core/config.py`: Redis 연결 설정