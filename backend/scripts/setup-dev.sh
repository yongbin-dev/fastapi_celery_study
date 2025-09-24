#!/bin/bash
# setup-dev.sh - 개발환경 자동 설정 스크립트

set -e

echo "🚀 FastAPI 프로젝트 개발환경 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
check_command() {
    if command -v $1 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $1이 설치되어 있습니다.${NC}"
        return 0
    else
        echo -e "${RED}❌ $1이 설치되어 있지 않습니다.${NC}"
        return 1
    fi
}

install_direnv() {
    echo "📦 direnv 설치 중..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew >/dev/null 2>&1; then
            brew install direnv
        else
            echo -e "${RED}❌ Homebrew가 필요합니다. https://brew.sh 에서 설치해주세요.${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt >/dev/null 2>&1; then
            sudo apt update && sudo apt install -y direnv
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y direnv
        else
            echo -e "${YELLOW}⚠️ 패키지 매니저를 찾을 수 없습니다. 수동으로 설치해주세요.${NC}"
            echo "설치 가이드: https://direnv.net/docs/installation.html"
            exit 1
        fi
    fi
}

setup_shell_hook() {
    local shell_name=$(basename "$SHELL")
    local rc_file=""
    
    case $shell_name in
        "zsh")
            rc_file="$HOME/.zshrc"
            ;;
        "bash")
            rc_file="$HOME/.bashrc"
            ;;
        "fish")
            rc_file="$HOME/.config/fish/config.fish"
            ;;
        *)
            echo -e "${YELLOW}⚠️ 지원되지 않는 Shell: $shell_name${NC}"
            return 1
            ;;
    esac

    if [[ $shell_name == "fish" ]]; then
        local hook_line="direnv hook fish | source"
    else
        local hook_line="eval \"\$(direnv hook $shell_name)\""
    fi

    if grep -q "direnv hook" "$rc_file" 2>/dev/null; then
        echo -e "${GREEN}✅ direnv hook이 이미 설정되어 있습니다.${NC}"
    else
        echo "$hook_line" >> "$rc_file"
        echo -e "${GREEN}✅ $rc_file에 direnv hook을 추가했습니다.${NC}"
        echo -e "${YELLOW}⚠️ 새 터미널을 열거나 'source $rc_file'을 실행해주세요.${NC}"
    fi
}

# 메인 실행
main() {
    echo "🔍 필수 도구 확인 중..."

    # pyenv 확인 및 설치
    if ! command -v pyenv >/dev/null 2>&1; then
        echo "📦 pyenv 설치 중..."
        curl https://pyenv.run | bash

        # PATH 추가
        export PATH="$HOME/.pyenv/bin:$PATH"

        if ! command -v pyenv >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️ pyenv 설치 완료. 새 터미널에서 다시 실행해주세요.${NC}"
            echo "또는 다음 명령어를 실행하세요:"
            echo "export PATH=\"\$HOME/.pyenv/bin:\$PATH\""
            exit 0
        fi
    fi

    # pyenv 초기화 (Poetry에서 python 명령어 사용 가능하도록)
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    echo -e "${GREEN}✅ pyenv가 초기화되었습니다.${NC}"

    # Python 확인
    if ! check_command python3; then
        echo -e "${RED}❌ Python3가 필요합니다. 설치해주세요.${NC}"
        exit 1
    fi
    
    # Poetry 확인 및 설치
    if ! check_command poetry; then
        echo "📦 Poetry 설치 중..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        
        if ! check_command poetry; then
            echo -e "${RED}❌ Poetry 설치 실패${NC}"
            exit 1
        fi
    fi
    
    # direnv 확인 및 설치
    if ! check_command direnv; then
        install_direnv
    fi
    
    # Shell Hook 설정
    setup_shell_hook
    
    # Poetry 의존성 설치
    echo "📚 Poetry 의존성 설치 중..."
    poetry env use python3
    poetry install
    
    # 가상환경 정보 출력
    echo -e "${GREEN}✅ 가상환경 경로: $(poetry env info --path)${NC}"
    
    # .envrc 허용
    if [[ -f ".envrc" ]]; then
        echo "🔒 .envrc 파일 허용 중..."
        eval "$(direnv hook bash)" 2>/dev/null || true
        direnv allow
    fi
    
    echo ""
    echo -e "${GREEN}🎉 개발환경 설정이 완료되었습니다!${NC}"
    echo ""
    echo -e "${YELLOW}📋 다음 단계:${NC}"
    echo "1. 새 터미널을 열거나 현재 터미널에서 다음을 실행:"
    echo "   source ~/.zshrc  (또는 해당하는 shell rc 파일)"
    echo ""
    echo "2. 프로젝트 디렉토리를 나갔다가 다시 들어오면 자동 활성화 확인:"
    echo "   cd .. && cd $(basename $PWD)"
    echo ""
    echo -e "${YELLOW}🛠️ 사용 가능한 명령어:${NC}"
    echo "   dev     - FastAPI 서버 시작"
    echo "   worker  - Celery Worker 시작"
    echo "   flower  - Flower 모니터링 시작"
    echo "   test    - 테스트 실행"
    echo "   format  - 코드 포맷팅"
    echo "   help    - 도움말"
}

# 스크립트 실행
main "$@"