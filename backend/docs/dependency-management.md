# 의존성 관리 가이드 (Poetry)

## 📦 Poetry를 사용한 도메인별 의존성 관리

이 프로젝트는 **Poetry**를 사용하여 팀별 도메인 의존성을 효율적으로 관리합니다.

## 🚀 빠른 시작

### 1. 기본 설치

```bash
# Poetry 설치 (필요시)
curl -sSL https://install.python-poetry.org | python3 -

# 기본 의존성 설치
poetry install
```

### 2. 도메인별 설치

각 팀은 자신의 도메인 의존성만 추가로 설치:

```bash
# LLM 팀
poetry install --with llm

# OCR 팀
poetry install --with ocr

# Vision 팀
poetry install --with vision

# 여러 도메인 동시 설치
poetry install --with llm,ocr,vision
```

### 3. 운영 환경 설치

```bash
# 운영 환경 패키지 포함
poetry install --with prod

# 전체 설치 (개발 + 모든 도메인 + 운영)
poetry install --with llm,ocr,vision,prod
```

## 📋 의존성 그룹 구조

### 공통 필수 의존성 (`[tool.poetry.dependencies]`)

모든 환경에서 자동으로 설치되는 패키지:

- **FastAPI 스택**: fastapi, uvicorn, pydantic
- **Celery 스택**: celery, redis
- **데이터베이스**: sqlalchemy, alembic, asyncpg, psycopg2
- **유틸리티**: httpx, python-dotenv

```bash
# 기본 의존성만 설치
poetry install --only main
```

### 개발 환경 (`[tool.poetry.group.dev]`)

테스트, 린팅, 포맷팅 도구:

- pytest, black, flake8, mypy, isort
- ipython, ipdb (디버깅)

```bash
# 개발 도구 포함 (기본값)
poetry install

# 개발 도구 제외
poetry install --without dev
```

### 운영 환경 (`[tool.poetry.group.prod]`)

운영 배포용 추가 패키지:

- gunicorn, flower, sentry-sdk

```bash
poetry install --with prod
```

### LLM 도메인 (`[tool.poetry.group.llm]`)

텍스트 생성 및 LLM 관련:

- transformers, torch, torchvision
- sentence-transformers, langchain
- huggingface-hub

```bash
poetry install --with llm
```

### OCR 도메인 (`[tool.poetry.group.ocr]`)

이미지 텍스트 추출:

- paddleocr, paddlepaddle
- opencv-python, Pillow

```bash
poetry install --with ocr
```

### Vision 도메인 (`[tool.poetry.group.vision]`)

객체 탐지 및 이미지 처리:

- ultralytics (YOLO)
- opencv-python, Pillow

```bash
poetry install --with vision
```

### Audio 도메인 (`[tool.poetry.group.audio]`)

음성 처리 (향후 확장용, 현재 주석 처리):

```bash
# 추후 활성화 시
poetry install --with audio
```

## 🔧 일반적인 사용 시나리오

### 시나리오 1: LLM 팀 개발자

```bash
# 1. 프로젝트 클론
git clone <repository>
cd backend

# 2. LLM 도메인 의존성 설치
poetry install --with llm

# 3. 개발 시작
poetry run python -m app.main
```

### 시나리오 2: OCR 팀 개발자

```bash
# OCR 도메인만 설치
poetry install --with ocr

# OCR 태스크 테스트
poetry run pytest tests/test_domains/test_ocr/ -v
```

### 시나리오 3: 통합 테스트 담당자

```bash
# 모든 도메인 설치
poetry install --with llm,ocr,vision

# 전체 테스트 실행
poetry run pytest
```

### 시나리오 4: 운영 서버 배포

```bash
# 운영 환경 + 필요한 도메인만
poetry install --without dev --with prod,llm,ocr

# 또는 전체 설치
poetry install --with llm,ocr,vision,prod
```

## 📝 의존성 추가하기

### 공통 의존성 추가

```bash
# 공통 패키지 추가 (모든 환경에서 필요)
poetry add <package-name>

# 예시
poetry add requests
```

### 도메인별 의존성 추가

```bash
# 특정 도메인에만 패키지 추가
poetry add --group llm <package-name>
poetry add --group ocr <package-name>
poetry add --group vision <package-name>

# 예시
poetry add --group llm openai
poetry add --group ocr easyocr
```

### 개발/운영 의존성 추가

```bash
# 개발 도구 추가
poetry add --group dev <package-name>

# 운영 환경 패키지 추가
poetry add --group prod <package-name>
```

## 🔄 의존성 업데이트

```bash
# 전체 의존성 업데이트
poetry update

# 특정 패키지만 업데이트
poetry update <package-name>

# 특정 그룹만 업데이트
poetry update --only llm
```

## 📊 의존성 확인

```bash
# 설치된 패키지 목록
poetry show

# 특정 패키지 상세 정보
poetry show <package-name>

# 의존성 트리
poetry show --tree

# 오래된 패키지 확인
poetry show --outdated
```

## 🎯 가상환경 관리

```bash
# 가상환경 활성화
poetry shell

# 가상환경 정보 확인
poetry env info

# 가상환경 삭제 후 재생성
poetry env remove python
poetry install --with llm
```

## 🔐 Lock 파일 관리

```bash
# poetry.lock 업데이트 (패키지 재설치 없이)
poetry lock --no-update

# poetry.lock 완전 재생성
poetry lock

# lock 파일 검증
poetry lock --check
```

## 💡 팁과 Best Practices

### 1. 팀별 설치 스크립트 작성

LLM 팀용 `setup_llm.sh`:
```bash
#!/bin/bash
poetry install --with llm
echo "✅ LLM 도메인 환경 설정 완료"
```

OCR 팀용 `setup_ocr.sh`:
```bash
#!/bin/bash
poetry install --with ocr
echo "✅ OCR 도메인 환경 설정 완료"
```

### 2. CI/CD 파이프라인 예시

```yaml
# .github/workflows/test.yml
- name: Install dependencies
  run: |
    poetry install --with llm,ocr,vision

- name: Run tests
  run: |
    poetry run pytest
```

### 3. Docker에서 사용

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Poetry 설치
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# 도메인별 설치 (예: LLM)
RUN poetry install --without dev --with llm

COPY . .
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### 4. 의존성 충돌 방지

```bash
# 새 패키지 추가 전 충돌 확인
poetry add <package-name> --dry-run

# 문제 발생 시 lock 파일 재생성
poetry lock --no-update
poetry install
```

## 🆚 Poetry vs requirements.txt 비교

| 항목 | Poetry (현재) | requirements.txt (이전) |
|------|--------------|------------------------|
| **그룹 관리** | ✅ 도메인별 optional group | ❌ 파일 분리 필요 |
| **버전 관리** | ✅ 자동 (poetry.lock) | ❌ 수동 관리 |
| **의존성 해결** | ✅ 자동 충돌 해결 | ❌ 수동 해결 |
| **가상환경** | ✅ 통합 관리 | ❌ 별도 관리 |
| **설치 속도** | ✅ 캐시 활용 | ⚠️ 느림 |

## 🚨 트러블슈팅

### 문제: "패키지 충돌 발생"

```bash
# 해결책 1: Lock 파일 재생성
poetry lock --no-update
poetry install

# 해결책 2: 특정 버전 지정
poetry add "package-name==1.0.0"
```

### 문제: "설치가 너무 느림"

```bash
# 해결책: 병렬 설치 활성화
poetry config installer.max-workers 10
poetry install
```

### 문제: "가상환경이 꼬임"

```bash
# 해결책: 가상환경 완전 재설정
poetry env remove python
poetry cache clear pypi --all
poetry install --with llm  # 필요한 그룹 지정
```

## 📚 추가 참고자료

- [Poetry 공식 문서](https://python-poetry.org/docs/)
- [의존성 그룹 상세 가이드](https://python-poetry.org/docs/managing-dependencies/#dependency-groups)
- [프로젝트 아키텍처 개선안](./architecture-improvement.md)
- [도메인 개발 가이드](./domain-setup-guide.md)