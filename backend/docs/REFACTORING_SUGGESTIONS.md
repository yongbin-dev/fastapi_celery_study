# tasks.py 리팩토링 제안

이 문서는 `tasks.py` 파일의 유지보수성, 유연성 및 테스트 용이성을 개선하기 위한 리팩토링 제안 사항을 제공합니다.

## 1. 파이프라인 스테이지 정의 추출

`initialize_pipeline_stages` 함수에는 스테이지 정의가 하드코딩되어 있어 유연성이 떨어집니다. 스테이지를 추가, 제거 또는 수정하려면 이 함수의 코드를 직접 변경해야 합니다.

**제안:** 스테이지 정의를 별도의 설정 파일(예: YAML 또는 JSON)이나 전용 모듈로 분리하세요. 이렇게 하면 파이프라인을 더 쉽게 설정하고 관리할 수 있습니다.

**예시 (`pipeline_config.py`):**

```python
STAGES = [
    {
        "stage": 1,
        "name": "데이터 전처리",
        "description": "입력 데이터 정제 및 전처리",
        "expected_duration": "2-4초",
    },
    {
        "stage": 2,
        "name": "특성 추출",
        "description": "텍스트 벡터화 및 특성 추출",
        "expected_duration": "3-5초",
    },
    # ... 등등
]
```

그런 다음 `tasks.py`에서 이 설정을 가져와서 스테이지를 초기화할 수 있습니다.

## 2. Celery 작업의 코드 중복 줄이기

4개의 Celery 작업(`stage1_preprocessing`, `stage2_feature_extraction` 등)은 많은 상용구 코드를 공유합니다. 예를 들어, 모든 작업은 작업 시작, 상태 업데이트, 오류 처리 및 로깅에 대해 동일한 구조를 가집니다.

**제안:** 공통 로직을 캡슐화하는 제네릭 작업 핸들러나 데코레이터를 만드세요. 이렇게 하면 개별 작업 구현이 훨씬 더 깔끔해지고 특정 비즈니스 로직에 더 집중할 수 있습니다.

**예시 (데코레이터 사용):**

```python
from functools import wraps

def pipeline_stage(stage_name: str, stage_num: int):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # args 또는 kwargs에서 chain_id 추출
            # ...

            start_time = time.time()
            
            # 작업 실행 전 공통 로직
            status_manager.update_status(chain_id, stage_num, ProcessStatus.PENDING, 0, 
                                       {'stage_name': stage_name, 'start_time': start_time}, task_id=self.request.id)
            update_celery_progress(self, chain_id, stage_num, stage_name, 'started', 0)

            try:
                # 실제 작업 로직 실행
                result = func(self, *args, **kwargs)

                # 작업 실행 후 공통 로직
                execution_time = time.time() - start_time
                status_manager.update_status(chain_id, stage_num, ProcessStatus.SUCCESS, 100,
                                           {'stage_name': stage_name, 'execution_time': execution_time}, task_id=self.request.id)
                log_stage_metrics(chain_id, stage_num, stage_name, execution_time)
                
                return result
            except Exception as e:
                handle_stage_error(self, chain_id, stage_num, stage_name, e, start_time)
                raise

        return wrapper
    return decorator

@celery_app.task(bind=True, name="app.tasks.stage1_preprocessing")
@pipeline_stage(stage_name="데이터 전처리", stage_num=1)
def stage1_preprocessing(self, input_data: Dict[str, Any], chain_id: str = None) -> StageResult:
    # ... 실제 전처리 로직 ...
```

## 3. Redis에서 `PipelineStatusManager` 분리

`PipelineStatusManager`는 Redis에 강하게 결합되어 있습니다. Redis가 이러한 종류의 작업에 좋은 선택이긴 하지만, 이러한 강한 결합은 테스트를 더 어렵게 만들고 나중에 다른 백엔드로 전환하기 어렵게 만듭니다.

**제안:** 파이프라인 상태를 업데이트하고 검색하기 위한 인터페이스를 정의하는 상태 관리자를 위한 추상 기본 클래스를 정의하세요. 그런 다음 이 인터페이스를 구현하는 `RedisPipelineStatusManager`를 만드세요. 이렇게 하면 의존성 주입을 사용하여 작업에 상태 관리자를 제공할 수 있으므로 코드가 더 모듈화되고 테스트하기 쉬워집니다.

**예시:**

```python
from abc import ABC, abstractmethod

class AbstractPipelineStatusManager(ABC):
    @abstractmethod
    def update_status(self, ...):
        pass
    # ... 다른 메소드들

class RedisPipelineStatusManager(AbstractPipelineStatusManager):
    # ... Redis를 사용한 구현 ...
```

## 4. 설정 관리 개선

코드는 `from .core.config import settings`에서 직접 설정을 가져옵니다. 이것은 일반적인 패턴이지만 개발, 테스트, 프로덕션과 같은 다양한 환경에 대한 설정을 관리하기 어렵게 만들 수 있습니다.

**제안:** 더 강력한 설정 관리 라이브러리(이미 부분적으로 사용하고 있는 Pydantic의 `BaseSettings`와 같은)를 사용하고 필요한 구성 요소에 설정을 주입하세요. 이렇게 하면 코드가 의존성에 대해 더 명시적이 되고 설정하기 쉬워집니다.

## 5. 유틸리티 함수 리팩토링

"유틸리티 함수들" 섹션에는 책임이 다른 함수들이 섞여 있습니다.

**제안:** 이러한 함수들을 더 응집력 있는 모듈로 그룹화하세요. 예를 들어, 유효성 검사 함수(`validate_stage_input`, `validate_chain_id`)는 `validation.py` 모듈로 옮길 수 있습니다. 진행률 계산 로직은 `PipelineStatusManager`의 일부이거나 별도의 `progress.py` 모듈이 될 수 있습니다.

## 6. `update_status` 로직 단순화

`update_status` 함수에는 작업 목록에서 스테이지를 찾아 업데이트하는 비교적 복잡한 블록이 있습니다.

**제안:** 스테이지 번호를 키로 사용하여 Redis에 스테이지를 저장하는 딕셔너리를 사용하면 이를 단순화할 수 있습니다. 이렇게 하면 목록을 반복하지 않고도 스테이지 정보에 직접 액세스할 수 있습니다. 그러나 이를 위해서는 Redis에 저장된 데이터 구조를 변경해야 합니다.

## 7. 작업 상태를 위한 데이터 클래스 도입

Celery 작업들은 서로 딕셔너리(예: `stage1_result`, `stage2_result`)를 전달합니다. 이것은 타입 세이프하지 않으며, 딕셔너리 키의 오타나 데이터 구조 변경 시 오류를 유발할 수 있습니다.

**제안:** Pydantic `BaseModel`이나 표준 파이썬 `dataclass`를 사용하여 작업 간에 전달되는 데이터를 나타내세요. 이는 타입 힌트, 유효성 검사 및 스테이지 간의 명확한 데이터 계약을 제공합니다.

**예시:**

```python
from pydantic import BaseModel

class PipelineData(BaseModel):
    chain_id: str
    input_data: Dict[str, Any]
    # ... 스테이지 간에 전달되는 다른 필드들

# 작업에서:
def stage1_preprocessing(self, pipeline_data: PipelineData) -> PipelineData:
    # ...
    return pipeline_data

def stage2_feature_extraction(self, pipeline_data: PipelineData) -> PipelineData:
    # ...
    return pipeline_data
```

## 8. 작업 이름 및 설정 중앙화

작업 이름(예: `"app.tasks.stage1_preprocessing"`)이 `@celery_app.task` 데코레이터에 하드코딩되어 있습니다. 이는 특히 작업 수가 많을 때 작업을 관리하고 구성하기 어렵게 만들 수 있습니다.

**제안:** 작업 이름을 중앙 위치에 상수로 정의하거나, 더 좋게는 스테이지 설정에 따라 동적으로 생성하세요. 이렇게 하면 작업 이름을 더 쉽게 관리하고 일관성을 보장할 수 있습니다.

**예시:**

```python
# pipeline_config.py에서
STAGES = [
    {"stage": 1, "name": "데이터 전처리", "task_name": "app.tasks.stage1_preprocessing", ...},
    {"stage": 2, "name": "특성 추출", "task_name": "app.tasks.stage2_feature_extraction", ...},
]

# tasks.py에서
from .pipeline_config import STAGES

@celery_app.task(bind=True, name=STAGES[0]["task_name"])
def stage1_preprocessing(...):
    # ...
```

## 9. 오류 처리 및 재시도 개선

`handle_stage_error` 함수에는 하드코딩된 재시도 메커니즘(`countdown=60, max_retries=3`)이 있습니다. 이는 모든 유형의 오류에 최적이지 않을 수 있습니다. 일부 오류는 일시적일 수 있어 더 즉각적인 재시도가 유용할 수 있으며, 다른 오류는 영구적이어서 전혀 재시도해서는 안 될 수도 있습니다.

**제안:** 더 정교한 재시도 전략을 구현하세요. 예외 유형에 따라 다른 재시도 정책을 사용할 수 있습니다. 예를 들어, 네트워크 관련 오류에 대해서는 지수적 백오프 전략을 사용할 수 있습니다. 또한 애플리케이션에 대한 사용자 지정 예외 클래스를 정의하여 재시도 동작을 더 세밀하게 제어할 수 있습니다.

## 10. 로깅 개선

작업의 로깅은 전반적으로 양호하지만, 더 구조화되고 일관성 있게 만들 수 있습니다. 예를 들어, 일부 로그 메시지에는 `chain_id`가 포함되어 있지만 다른 메시지에는 포함되어 있지 않습니다.

**제안:** 구조화된 로깅 라이브러리(`structlog`와 같은)를 사용하여 기계가 읽을 수 있는 형식(예: JSON)으로 로그를 생성하세요. 이렇게 하면 특히 분산 시스템에서 로그를 검색, 필터링 및 분석하기가 훨씬 쉬워집니다. 또한 각 작업 시작 시 "바인딩된" `chain_id`를 가진 로거 인스턴스를 생성하여 특정 파이프라인 실행에 대한 모든 로그 메시지에 동일한 ID가 태그되도록 할 수 있습니다.

## 11. `status_manager`에 의존성 주입 사용

`status_manager`는 전역 인스턴스로 생성됩니다. 이는 테스트에서 전역 인스턴스를 패치해야 하므로 테스트를 더 어렵게 만들 수 있습니다.

**제안:** 의존성 주입 프레임워크(`fastapi-injector` 또는 `dependency-injector`와 같은)를 사용하여 `status_manager`의 라이프사이클을 관리하고 필요한 구성 요소에 주입하세요. 이렇게 하면 코드가 더 모듈화되고 테스트하기 쉬워집니다. Celery 작업은 FastAPI의 의존성 주입과 즉시 통합되지는 않지만, 의존성을 명시적으로 전달하거나 서비스 로케이터 패턴을 사용하여 원칙을 적용할 수 있습니다.
