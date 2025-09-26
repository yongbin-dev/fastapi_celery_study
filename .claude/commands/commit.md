# 커밋 명령어

이 명령어는 완전한 git 커밋 워크플로우를 수행합니다: 모든 파일을 추가하고, 커밋 메시지를 생성하며, 변경사항을 커밋합니다.

## 사용법
```
/commit [선택적 커밋 메시지]
```

## 예시
```
/commit
/commit "feat: 새로운 사용자 인증 기능 추가"
```

## Implementation
```bash
#!/bin/bash

# Get optional commit message from arguments
COMMIT_MSG="$*"

# Add all files
echo "Adding all files to staging..."
git add .

# Check if there are any changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit."
    exit 0
fi

# If no commit message provided, generate one based on changes
if [ -z "$COMMIT_MSG" ]; then
    echo "Generating commit message based on changes..."

    # Get status and diff for message generation
    STATUS=$(git status --porcelain)
    DIFF=$(git diff --cached --name-only | head -10)

    # Simple commit message generation based on file patterns
    if echo "$STATUS" | grep -q "^A"; then
        COMMIT_MSG="feat: 새로운 파일 및 기능 추가"
    elif echo "$STATUS" | grep -q "^M.*\.py$"; then
        COMMIT_MSG="update: Python 파일 수정"
    elif echo "$STATUS" | grep -q "^M.*\.(js|ts|tsx)$"; then
        COMMIT_MSG="update: JavaScript/TypeScript 파일 수정"
    elif echo "$STATUS" | grep -q "^M.*\.md$"; then
        COMMIT_MSG="docs: 문서 업데이트"
    elif echo "$STATUS" | grep -q "^D"; then
        COMMIT_MSG="remove: 파일 삭제"
    else
        COMMIT_MSG="update: 일반적인 코드 변경사항"
    fi
fi

# Perform the commit
echo "Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG

> Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Show the result
echo "Commit completed successfully!"
git log --oneline -1
```