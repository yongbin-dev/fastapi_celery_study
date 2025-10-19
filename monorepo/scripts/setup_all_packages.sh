#!/bin/bash

# 전체 패키지 자동 설정 스크립트
# 각 패키지별로 독립적인 가상환경을 생성하고 의존성을 설치합니다.

set -e  # 오류 발생 시 즉시 종료

echo "🚀 FastAPI + Celery + ML Monorepo 설정 시작"
echo ""

# 루트 디렉토리 확인
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGES_DIR="$ROOT_DIR/packages"

echo "📂 프로젝트 루트: $ROOT_DIR"
echo ""

# 1. shared 패키지 설정
echo "📦 1/4: shared 패키지 설정 중..."
cd "$PACKAGES_DIR/shared"
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e .
deactivate
echo "✅ shared 패키지 설정 완료"
echo ""

# 2. api_server 패키지 설정
echo "📦 2/4: api_server 패키지 설정 중..."
cd "$PACKAGES_DIR/api_server"
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e ../shared
uv pip install -e .
deactivate
echo "✅ api_server 패키지 설정 완료"
echo ""

# 3. celery_worker 패키지 설정
echo "📦 3/4: celery_worker 패키지 설정 중..."
cd "$PACKAGES_DIR/celery_worker"
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e ../shared
uv pip install -e .
deactivate
echo "✅ celery_worker 패키지 설정 완료"
echo ""

# 4. ml_server 패키지 설정
echo "📦 4/4: ml_server 패키지 설정 중..."
cd "$PACKAGES_DIR/ml_server"
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e ../shared
uv pip install -e .
deactivate
echo "✅ ml_server 패키지 설정 완료"
echo ""

echo "🎉 모든 패키지 설정이 완료되었습니다!"
echo ""
echo "📝 다음 단계:"
echo "   1. 환경 변수 설정: cp .env.example .env"
echo "   2. .env 파일 편집하여 실제 값 입력"
echo "   3. 각 서비스 실행 (README.md 참고)"
echo ""
