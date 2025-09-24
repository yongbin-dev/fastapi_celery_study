# HTTP 테스트 가이드

이 폴더는 FastAPI 애플리케이션의 REST API를 테스트하기 위한 HTTP 파일들을 포함합니다.

## 파일 구조

```
http_tests/
├── environments/
│   └── http-client.env.json     # 환경별 변수 설정
├── basic-api.http               # 기본 API 테스트
├── pipeline-api.http            # 파이프라인 관련 API 테스트
├── model-api.http               # 모델 서비스 API 테스트
└── README.md                    # 이 파일
```

## 사용 방법

### 1. VS Code REST Client 확장 설치
- VS Code에서 "REST Client" 확장을 설치합니다
- 또는 IntelliJ IDEA의 HTTP Client를 사용할 수 있습니다

### 2. 환경 선택
- VS Code에서 `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`)를 누르고 "Rest Client: Switch Environment"를 검색
- 원하는 환경을 선택합니다 (development, production, docker)

### 3. 테스트 실행
- HTTP 파일을 열고 요청 위의 "Send Request" 링크를 클릭
- 또는 `Ctrl+Alt+R` (macOS: `Cmd+Alt+R`) 단축키 사용

## 환경 설정

### Development (기본)
- URL: `http://localhost:5050`
- 로컬 개발 서버용

### Production
- URL: `http://your-prod-server.com`
- 운영 서버용 (URL을 실제 서버 주소로 변경 필요)

### Docker
- URL: `http://localhost:5050`
- Docker Compose로 실행된 서버용

## API 엔드포인트

### 기본 API (basic-api.http)
- `GET /` - 헬스체크
- `GET /docs` - API 문서 (Swagger UI)
- `GET /openapi.json` - OpenAPI 스키마

### 파이프라인 API (pipeline-api.http)
- `GET /api/v1/tasks/models` - 사용 가능한 모델 조회
- `POST /api/v1/tasks/predict` - AI 예측 요청
- `POST /api/v1/tasks/ai-pipeline` - AI 파이프라인 생성
- `GET /api/v1/tasks/history` - 파이프라인 히스토리 조회
- `GET /api/v1/tasks/ai-pipeline/{chain_id}/tasks` - 특정 파이프라인 태스크 조회
- `DELETE /api/v1/tasks/ai-pipeline/{chain_id}/cancel` - 파이프라인 취소

### 모델 API (model-api.http)
- `GET /api/v1/model/models` - 모델 서비스의 사용 가능한 모델 조회
- `POST /api/v1/model/predict` - 모델 서비스를 통한 예측 요청

## 주의사항

1. **서버 실행 확인**: 테스트 전에 FastAPI 서버가 실행되고 있는지 확인하세요
   ```bash
   python -m app.main
   # 또는
   uvicorn app.main:app --reload --host 0.0.0.0 --port 5050
   ```

2. **Ollama 서버**: pipeline-api.http의 predict 엔드포인트는 외부 Ollama 서버가 필요합니다
   - 현재 설정된 서버: `192.168.0.122:12434`, `192.168.0.122:13434`
   - 실제 환경에 맞게 controller 파일에서 URL을 수정하세요

3. **chain_id 변수**: 파이프라인 관련 요청에서는 실제 chain_id를 사용해야 합니다
   - AI 파이프라인 생성 후 반환되는 chain_id를 사용하세요

## 팁

- 요청 사이의 `###` 구분자는 개별 테스트를 분리합니다
- 응답은 VS Code의 새 탭에서 표시됩니다
- JSON 응답은 자동으로 포맷팅됩니다
- 환경 변수는 `{{variableName}}` 형식으로 사용됩니다