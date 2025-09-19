# Commit Command

This command performs a complete git commit workflow: adds all files, generates a commit message, and commits the changes.

## Usage
```
/commit [optional commit message]
```

## Examples
```
/commit
/commit "feat: add new user authentication feature"
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
        COMMIT_MSG="feat: add new files and features"
    elif echo "$STATUS" | grep -q "^M.*\.py$"; then
        COMMIT_MSG="update: modify Python files"
    elif echo "$STATUS" | grep -q "^M.*\.(js|ts|tsx)$"; then
        COMMIT_MSG="update: modify JavaScript/TypeScript files"
    elif echo "$STATUS" | grep -q "^M.*\.md$"; then
        COMMIT_MSG="docs: update documentation"
    elif echo "$STATUS" | grep -q "^D"; then
        COMMIT_MSG="remove: delete files"
    else
        COMMIT_MSG="update: general code changes"
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