# 🚀 FastAPI + Celery + Poetry 개발 환경 설정 가이드

이 문서는 FastAPI + Celery + Poetry 환경에서 VSCode 개발 설정 방법을 정리한 것입니다.
목표는 코드 품질, 생산성, 디버깅 편의성을 모두 잡는 것입니다.

## 📂 현재 프로젝트 구조
```
backend_fastapi/
├── app/
│   ├── main.py
│   ├── core/
│   ├── api/
│   ├── services/
│   ├── schemas/
│   └── ...
├── .vscode/
│   ├── settings.json
│   ├── tasks.json
│   └── launch.json
├── .venv/                 # Poetry 가상환경
├── pyproject.toml         # Poetry 설정
├── poetry.lock
├── .envrc                 # direnv 자동 환경 설정
├── .env.development
└── ...
```

## 1️⃣ VSCode 확장 프로그램 추천

| 확장 프로그램 | 설명 | 필수도 |
|---|---|---|
| Python | Python 언어 지원 | ⭐⭐⭐ |
| Pylance | Python 언어 서버 | ⭐⭐⭐ |
| Black Formatter | 코드 포맷터 | ⭐⭐⭐ |
| Ruff | 빠른 Python 린터 | ⭐⭐⭐ |
| Thunder Client | API 테스트 도구 | ⭐⭐ |
| REST Client | .http 파일 지원 | ⭐⭐ |
| Docker | Docker 지원 | ⭐⭐ |
| YAML | YAML 파일 지원 | ⭐ |

## 2️⃣ .vscode/settings.json

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.useLibraryCodeForTypes": true,

  // 코드 포맷팅
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "black-formatter.args": ["--line-length", "88"],

  // Ruff 린터
  "ruff.enable": true,
  "ruff.lintOnSave": true,
  "ruff.args": [
    "--line-length=88",
    "--select=E,F,W,B,I",
    "--ignore=E501"
  ],

  // 파일 제외
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.pytest_cache": true
  },

  // 터미널 환경
  "terminal.integrated.env.linux": {
    "PYTHONUNBUFFERED": "1",
    "PYTHONPATH": "${workspaceFolder}"
  },
  "terminal.integrated.env.windows": {
    "PYTHONUNBUFFERED": "1",
    "PYTHONPATH": "${workspaceFolder}"
  },

  // Thunder Client
  "thunder-client.saveToWorkspace": true,

  // 에디터 설정
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.rulers": [88],
  "editor.wordWrap": "on",
  "editor.minimap.enabled": false,

  // Git
  "git.confirmSync": false,
  "git.autofetch": true
}
```

## 3️⃣ .vscode/tasks.json

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run FastAPI (Uvicorn)",
      "type": "shell",
      "command": "poetry",
      "args": ["run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "5050"],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "problemMatcher": [],
      "options": {
        "env": {
          "PYTHONUNBUFFERED": "1"
        }
      }
    },
    {
      "label": "Run Celery Worker",
      "type": "shell",
      "command": "poetry",
      "args": ["run", "celery", "-A", "app.core.celery_app", "worker", "--loglevel=info"],
      "group": "build",
      "problemMatcher": [],
      "options": {
        "env": {
          "PYTHONUNBUFFERED": "1"
        }
      }
    },
    {
      "label": "Run Flower",
      "type": "shell",
      "command": "poetry",
      "args": ["run", "celery", "-A", "app.core.celery_app", "flower", "--port=5555"],
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "poetry",
      "args": ["run", "pytest"],
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "Format Code",
      "type": "shell",
      "command": "poetry",
      "args": ["run", "black", "."],
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Lint Code",
      "type": "shell",
      "command": "poetry",
      "args": ["run", "flake8"],
      "group": "build",
      "problemMatcher": []
    }
  ]
}
```



## 4️⃣ .vscode/launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "5050"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "ENVIRONMENT": "development"
      },
      "jinja": true,
      "python": "${workspaceFolder}/.venv/bin/python"
    },
    {
      "name": "Debug Celery Worker",
      "type": "python",
      "request": "launch",
      "module": "celery",
      "args": [
        "-A", "app.core.celery_app",
        "worker",
        "--loglevel=debug"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "ENVIRONMENT": "development"
      },
      "python": "${workspaceFolder}/.venv/bin/python"
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "${file}"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "ENVIRONMENT": "development"
      },
      "python": "${workspaceFolder}/.venv/bin/python"
    }
  ]
}
```

5️⃣ 사용 방법

- 프로젝트 루트에 .vscode 폴더 생성 후 위 3개 파일 저장
- 가상환경 생성
  python -m venv .venv
- 필요한 패키지 설치
  pip install fastapi uvicorn black ruff
- VSCode에서 F5 → "Debug FastAPI" 선택
- 브라우저에서 http://127.0.0.1:8000/docs 접속 → Swagger UI 확인
- 코드 수정 시 자동 리로드됨

📌 추가 팁

- settings.json의 "python.defaultInterpreterPath"는 OS와 가상환경 경로에 맞게 수정
- tasks.json의 app.main:app 경로는 실제 FastAPI 인스턴스 위치에 맞게 변경
- launch.json을 이용하면 중단점 디버깅 가능

✅ 이 설정을 적용하면 FastAPI 개발 + 디버깅 + 코드 품질 관리를 한 번에 세팅할 수 있습니다.
