#!/bin/bash

# 전체 패키지를 루트 가상환경에 설정하는 스크립트
set -e  # 오류 발생 시 즉시 종료

echo "🚀 FastAPI + Celery + ML Monorepo 통합 설정 시작"
echo ""

# 프로젝트 루트 디렉토리 확인
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "📂 프로젝트 루트: $ROOT_DIR"
echo ""

# 1. 루트 가상환경 생성 또는 업데이트
echo "📦 1/2: 루트 가상환경 설정 중..."
cd "$ROOT_DIR"
uv venv .venv --python 3.12
source .venv/bin/activate
echo "✅ 루트 가상환경 활성화 완료"
echo ""

# 2. 모든 워크스페이스 패키지를 편집 가능 모드로 설치
# uv는 pyproject.toml의 [tool.uv.workspace] 설정을 읽어 'shared' 같은 내부 의존성을 올바르게 처리합니다.
echo "📦 2/2: 모든 패키지를 편집 가능 모드로 설치 중..."
uv pip install -e ./packages/shared
uv pip install -e ./packages/api_server
uv pip install -e ./packages/celery_worker
# uv pip install -e ./packages/ml_server
uv pip install -e "./packages/ml_server[ocr-cpu]"
echo "✅ 모든 패키지 설치 완료"
echo ""

deactivate
echo "🎉 모든 패키지가 루트 가상환경에 성공적으로 설정되었습니다!"
echo ""
echo "📝 다음 단계:"
echo "   1. VS Code를 사용하신다면, 파이썬 인터프리터를 루트의 .venv로 설정하세요."
echo "      경로: $ROOT_DIR/.venv/bin/python"
echo "   2. 환경 변수 설정: cp .env.example .env (아직 안했다면)"
echo "   3. .env 파일에 필요한 값을 채워넣으세요."
echo "   4. 각 서비스를 실행하세요 (자세한 내용은 README.md 참고)."
echo ""
