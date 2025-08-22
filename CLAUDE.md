# CLAUDE.md

이 파일은 이 저장소에서 코드 작업을 할 때 Claude Code (claude.ai/code)에게 지침을 제공합니다.

## 개발 명령어

의존성 설치:
```bash
pip install -r requirements.txt
```

애플리케이션 실행:
```bash
python main.py
```

애플리케이션은 `http://0.0.0.0:8000`에서 자동 리로드 기능과 함께 실행됩니다.

## 아키텍처 개요

이는 **Kafka 메시지 처리** 기능을 갖춘 **FastAPI 기반 LLM 서비스**입니다. 아키텍처는 레이어 패턴을 따릅니다:

### 핵심 구성요소

**FastAPI 웹 서버** (`main.py`):
- 채팅 상호작용 및 모델 관리를 위한 RESTful API 엔드포인트
- Kafka 컨슈머를 위한 비동기 라이프사이클 관리
- 엔드포인트: `/chat`, `/models`, `/`

**모델 관리 레이어** (`services/model_service.py`):
- 전역 싱글톤 `model_service`가 여러 AI 모델을 관리
- 확장성을 위한 추상 베이스 모델 패턴
- 현재 Hugging Face 트랜스포머(DialoGPT) 지원

**Kafka 통합** (`kafka/`):
- 설정 기반 컨슈머 관리 시스템
- 스레드 기반 메시지 처리
- `topic_config.py`의 토픽 설정이 핸들러와 그룹을 정의
- 현재 AI 요청 처리를 위한 `python-topic`으로 구성

### 주요 디자인 패턴

**추상 베이스 모델** (`models/base_model.py`):
- 모든 ML 모델이 `BaseModel`을 상속
- `load_model()` 및 `predict()` 인터페이스를 강제
- `is_loaded` 플래그를 통한 상태 관리

**설정 기반 Kafka 컨슈머** (`kafka/config_based_consumer.py`):
- `TopicConfig` 데이터클래스가 토픽-핸들러 매핑을 정의
- 문자열 이름을 통한 동적 핸들러 로딩
- 토픽당 스레드 컨슈머 패턴

**서비스 레이어 패턴**:
- `ModelService`가 ML 모델의 레지스트리와 퍼사드 역할
- 오류 처리가 포함된 중앙집중식 예측 인터페이스

## Kafka 설정

시스템에서 기대하는 설정:
- `localhost:9092`의 Kafka 브로커
- AI 요청을 위한 `python-topic` 토픽
- `ai-service-group` 컨슈머 그룹

AI 요청을 위한 메시지 형식:
```json
{"text": "사용자 메시지", "max_length": 100}
```

## 의존성

- **FastAPI/Uvicorn**: 웹 프레임워크 및 ASGI 서버
- **PyTorch + Transformers**: ML 모델 추론
- **kafka-python**: Kafka 클라이언트 라이브러리
- **Pydantic**: 데이터 검증 및 직렬화

## 모델 로딩

모델은 FastAPI 라이프스팬 컨텍스트 매니저를 통해 시작시 로드됩니다. LLM 모델(`microsoft/DialoGPT-medium`)은 현재 시작 순서에서 주석 처리되어 있지만 `main.py`의 43-46줄 주석을 해제하여 활성화할 수 있습니다.