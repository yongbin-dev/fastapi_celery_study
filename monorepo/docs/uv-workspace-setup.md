# uv 워크스페이스 설정 가이드

## 목차

1. [개요](#개요)
2. [워크스페이스 구조](#워크스페이스-구조)
3. [초기 설정](#초기-설정)
4. [사용 방법](#사용-방법)
5. [의존성 관리](#의존성-관리)
6. [주의사항](#주의사항)
7. [트러블슈팅](#트러블슈팅)

---

## 개요

이 프로젝트는 **uv 워크스페이스 모드**를 사용하여 여러 Python 패키지를 하나의 모노레포로 관리합니다.

### uv 워크스페이스란?

- **하나의 가상환경**으로 여러 패키지를 관리
- **하나의 uv.lock** 파일로 모든 의존성 통합 관리
- 패키지 간 의존성 충돌 자동 해결
- editable mode로 즉시 변경사항 반영

---

## 워크스페이스 구조

```
monorepo/
├── .venv/                    # 통합 가상환경 (모든 패키지 포함)
├── uv.lock                   # 통합 의존성 락 파일
├── pyproject.toml            # 워크스페이스 설정
├── docs/                     # 프로젝트 문서
└── packages/
    ├── shared/               # 공통 라이브러리
    │   ├── shared/          # 실제 패키지 코드
    │   └── pyproject.toml   # shared 패키지 설정
    ├── api_server/           # FastAPI REST API 서버
    │   ├── app/             # 실제 패키지 코드
    │   └── pyproject.toml   # api_server 패키지 설정
    ├── celery_worker/        # Celery 백그라운드 워커
    │   ├── core/            # Celery 설정
    │   ├── tasks/           # Celery 태스크
    │   └── pyproject.toml   # celery_worker 패키지 설정
    └── ml_server/            # AI/ML 모델 서버
        ├── app/             # 실제 패키지 코드
        └── pyproject.toml   # ml_server 패키지 설정
```

---

## 초기 설정

### 1. uv 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 워크스페이스 초기화

```bash
cd /home/yb/dev/fastapi_celery_study/monorepo
uv sync
```

이 명령은:
- 루트에 `.venv` 디렉토리 생성
- 모든 워크스페이스 패키지 설치
- `uv.lock` 파일 생성 또는 업데이트

### 3. 설치 확인

```bash
# 가상환경 활성화
source .venv/bin/activate

# 패키지 설치 확인
python -c "
from importlib.metadata import version

packages = ['shared', 'api-server', 'celery-worker', 'ml-server']
for pkg in packages:
    try:
        v = version(pkg)
        print(f'✅ {pkg} == {v}')
    except:
        print(f'❌ {pkg} - 설치되지 않음')
"
```

---

## 사용 방법

### 가상환경 활성화

**중요**: 모든 패키지 작업에 하나의 가상환경만 사용합니다.

```bash
cd /home/yb/dev/fastapi_celery_study/monorepo
source .venv/bin/activate
```


### 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 패키지 테스트
pytest packages/api_server/tests/
pytest packages/shared/tests/
```

---

## 의존성 관리

### 새로운 의존성 추가

#### 1. pyproject.toml 수정

해당 패키지의 `pyproject.toml` 파일을 수정합니다.

예: `api_server`에 `httpx` 추가

```toml
# packages/api_server/pyproject.toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "httpx>=0.28.0",  # 새로운 의존성
    "shared",
]
```

#### 2. uv sync 실행

```bash
cd /home/yb/dev/fastapi_celery_study/monorepo
uv sync
```

이 명령은:
- 새로운 의존성을 설치
- `uv.lock` 파일을 업데이트
- 의존성 충돌을 자동으로 해결

### shared 패키지 수정

`shared` 패키지는 **editable mode**로 설치되어 있습니다:

```python
# packages/shared/shared/utils.py 수정
def new_function():
    return "즉시 반영됨!"
```

```python
# packages/api_server에서 바로 사용 가능
from shared.utils import new_function

print(new_function())  # "즉시 반영됨!"
```

**재설치 불필요** - 변경사항이 즉시 반영됩니다.

### 의존성 업데이트

```bash
# 모든 의존성을 최신 버전으로 업데이트
uv sync --upgrade

# 특정 패키지만 업데이트
uv sync --upgrade-package fastapi
```

### 의존성 확인

```bash
# 설치된 패키지 목록
uv pip list

# 특정 패키지 정보
uv pip show shared
```

---

## 주의사항

### ✅ 해야 할 것

1. **항상 루트 `.venv` 사용**
   ```bash
   source /home/yb/dev/fastapi_celery_study/monorepo/.venv/bin/activate
   ```

2. **의존성 추가 후 uv sync 실행**
   ```bash
   uv sync
   ```

3. **루트에서 uv 명령 실행**
   ```bash
   cd /home/yb/dev/fastapi_celery_study/monorepo
   uv sync
   ```

### ❌ 하지 말아야 할 것

1. **각 패키지별 .venv 생성 금지**
   ```bash
   # ❌ 이렇게 하지 마세요
   cd packages/api_server
   python -m venv .venv
   ```

2. **pip 직접 사용 금지**
   ```bash
   # ❌ 이렇게 하지 마세요
   pip install some-package

   # ✅ 대신 pyproject.toml 수정 후 uv sync
   ```

3. **uv.lock 파일 수동 수정 금지**
   - `uv.lock`은 자동 생성되는 파일입니다
   - 수동으로 수정하지 마세요

---

## 트러블슈팅

### 1. 패키지를 찾을 수 없음 (ModuleNotFoundError)

**증상**:
```
ModuleNotFoundError: No module named 'shared'
```

**해결**:
```bash
cd /home/yb/dev/fastapi_celery_study/monorepo
uv sync
source .venv/bin/activate
```

### 2. 의존성 충돌

**증상**:
```
error: Package `xxx` requires `yyy>=2.0`, but `yyy==1.0` is installed
```

**해결**:
```bash
# uv.lock 삭제 후 재생성
rm uv.lock
uv sync
```

### 3. 가상환경이 없음

**증상**:
```
-bash: .venv/bin/activate: No such file or directory
```

**해결**:
```bash
cd /home/yb/dev/fastapi_celery_study/monorepo
uv sync
```

### 4. shared 패키지 수정이 반영되지 않음

**확인**:
```bash
# editable 모드로 설치되었는지 확인
uv pip show shared

# editable mode가 아니면 재설치
cd /home/yb/dev/fastapi_celery_study/monorepo
uv sync
```

### 5. workspace member 오류

**증상**:
```
error: Workspace member `/path/to/xxx` is missing a `pyproject.toml`
```

**해결**:
- `packages/` 디렉토리에 패키지가 아닌 디렉토리가 있는지 확인
- `pyproject.toml`의 `[tool.uv.workspace]` 설정 확인

```toml
# pyproject.toml
[tool.uv.workspace]
members = [
    "packages/shared",
    "packages/api_server",
    "packages/celery_worker",
    "packages/ml_server"
]
```

---

## 추가 정보

### 워크스페이스 설정 파일

루트 `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
shared = { workspace = true }
```

### 패키지별 설정 예시

#### shared 패키지

```toml
# packages/shared/pyproject.toml
[project]
name = "shared"
version = "0.1.0"
dependencies = [
    "fastapi>=0.119.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "redis>=5.0.0",
]
```

#### api_server 패키지

```toml
# packages/api_server/pyproject.toml
[project]
name = "api-server"
version = "0.1.0"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "shared",  # 워크스페이스 패키지 의존성
]
```

---

## 참고 자료

- [uv 공식 문서](https://github.com/astral-sh/uv)
- [uv 워크스페이스 가이드](https://github.com/astral-sh/uv#workspaces)
- [Python 패키징 가이드](https://packaging.python.org/)
