# 개발 환경 설정 가이드

## 🐍 **가상환경 자동 활성화 설정**

이 프로젝트는 **direnv + Poetry** 조합을 사용하여 개발자가 디렉토리에 진입할 때마다 자동으로 가상환경이 활성화되도록 설정되어 있습니다.

## 📋 **필수 설치**

### 1. direnv 설치

#### macOS (Homebrew)

```bash
brew install direnv
```

#### Ubuntu/Debian

```bash
sudo apt install direnv
```

#### CentOS/RHEL

```bash
# EPEL 저장소 활성화 후
yum install direnv
```

### 2. Shell Hook 설정

사용 중인 Shell에 따라 다음 중 하나를 실행:

#### Zsh (macOS 기본)

```bash
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc
```

#### Bash

```bash
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
```

#### Fish Shell

```bash
echo 'direnv hook fish | source' >> ~/.config/fish/config.fish
```

## 🚀 **프로젝트 설정**

### 1. 프로젝트 클론 및 초기 설정

```bash
git clone <repository-url>
cd backend_fastapi

# Poetry 설치 (미설치 시)
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install
```

### 2. 자동 환경 설정 확인

```bash
# 프로젝트 디렉토리 진입 시 자동으로 물어봄
cd backend_fastapi
# direnv: error .envrc is blocked. Run `direnv allow` to approve its content

# 허용
direnv allow
```

## ✅ **설정 완료 확인**

### 정상 작동 테스트

```bash
# 디렉토리 나가기
cd ..

# 다시 진입하면 자동 활성화 메시지 표시
cd backend_fastapi
# direnv: loading ~/path/to/backend_fastapi/.envrc
# direnv: export +VIRTUAL_ENV ~PATH
# 🐍 가상환경 자동 활성화: backend_fastapi

# Python 경로 확인
which python
# ~/path/to/backend_fastapi/.venv/bin/python

# 패키지 확인
pip list | grep fastapi
```

## 🛠️ **IDE 설정**

### VS Code 설정

`.vscode/settings.json` 파일이 이미 설정되어 있습니다:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.terminal.activateEnvInCurrentTerminal": true,
  "terminal.integrated.env.osx": {
    "VIRTUAL_ENV": "${workspaceFolder}/.venv"
  }
}
```

### PyCharm 설정

1. `File` → `Settings` → `Project` → `Python Interpreter`
2. `Add Interpreter` → `Existing Environment`
3. `Interpreter Path`: `./venv/bin/python` 선택

## 🔧 **개발 명령어**

가상환경이 자동 활성화되면 다음 명령어들을 바로 사용할 수 있습니다:

### 서버 실행

```bash
# FastAPI 개발 서버
uvicorn app.main:app --reload --host 0.0.0.0 --port 5050

# 또는 Poetry를 통해 (권장)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 5050
```

### Celery 실행

```bash
# Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Flower (모니터링)
celery -A app.core.celery_app flower --port=5555
```

### 코드 품질 도구

```bash
# 코드 포맷팅
black .

# 린트 검사
flake8

# 타입 검사
mypy .

# 테스트 실행
pytest
```

## 🎯 **편의 명령어 설정**

자주 사용하는 명령어를 위한 Shell Alias 추가:

### ~/.zshrc 또는 ~/.bashrc에 추가

```bash
# FastAPI 개발 편의 명령어
alias fapi-dev="poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 5050"
alias fapi-worker="poetry run celery -A app.core.celery_app worker --loglevel=info"
alias fapi-flower="poetry run celery -A app.core.celery_app flower --port=5555"
alias fapi-test="poetry run pytest"
alias fapi-format="poetry run black . && poetry run flake8"
```

적용:

```bash
source ~/.zshrc  # 또는 ~/.bashrc
```

## 🐳 **Docker와의 통합**

로컬 개발은 direnv로, 배포는 Docker로 사용하는 하이브리드 방식:

```bash
# 로컬 개발
cd backend_fastapi  # 자동 가상환경 활성화
fapi-dev

# Docker 개발 (필요시)
docker-compose up
```

## 🔍 **문제 해결**

### direnv가 작동하지 않을 때

```bash
# direnv 상태 확인
direnv status

# Shell Hook 재설정
eval "$(direnv hook zsh)"  # 또는 bash

# .envrc 재허용
direnv allow
```

### 가상환경이 생성되지 않았을 때

```bash
# Poetry 가상환경 재생성
poetry env remove python
poetry install
```

### 권한 오류 발생시

```bash
# direnv 캐시 초기화
direnv reload
```

## 🚨 **보안 고려사항**

- `.envrc` 파일은 프로젝트별로 `direnv allow` 명령어로 명시적 허용 필요
- 팀 공유시 `.envrc` 내용을 반드시 검토 후 허용
- 민감한 환경변수는 `.envrc` 대신 별도 `.env` 파일 사용

## 📚 **추가 리소스**

- [direnv 공식 문서](https://direnv.net/)
- [Poetry 가이드](https://python-poetry.org/docs/)
- [FastAPI 개발 가이드](https://fastapi.tiangolo.com/)

## 🆘 **도움이 필요한 경우**

1. 팀 Slack 채널에 문의
2. 이슈 등록: `GitHub Issues`
3. 개발 환경 관련 위키 문서 참조

---

**마지막 업데이트**: 2024-09-12  
**작성자**: Development Team
