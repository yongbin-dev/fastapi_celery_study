# Claude Code Configuration

## 커밋 메시지 가이드라인

### 기본 형식
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 타입 (Type)
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅, 세미콜론 누락 등 (기능 변경 없음)
- `refactor`: 코드 리팩토링 (기능 변경 없음)
- `test`: 테스트 추가 또는 수정
- `chore`: 빌드 프로세스 또는 보조 도구 변경
- `perf`: 성능 개선
- `ci`: CI 설정 파일 및 스크립트 변경

### 스코프 (Scope) 예시
- `api`: API 관련 변경
- `ui`: 사용자 인터페이스 변경
- `db`: 데이터베이스 관련 변경
- `auth`: 인증/권한 관련 변경
- `config`: 설정 파일 변경
- `pipeline`: 데이터 파이프라인 관련 변경
- `celery`: Celery 작업 관련 변경
- `fastapi`: FastAPI 관련 변경

### 예시
```
feat(api): 사용자 프로필 업데이트 API 추가

사용자가 자신의 프로필 정보를 업데이트할 수 있는 
새로운 API 엔드포인트를 추가했습니다.

Closes #123
```

```
fix(celery): 작업 실행 시 타임존 동기화 문제 해결

Asia/Seoul 타임존으로 통일하여 작업 스케줄링 
오류를 수정했습니다.
```

```
chore: 의존성 업데이트 및 개발환경 설정
```

### 주의사항
- 첫 번째 줄은 50자 이내로 작성
- 본문은 72자로 줄바꿈
- 현재형, 명령형으로 작성 ("추가한다" 대신 "추가")
- 한글 또는 영어 사용 가능