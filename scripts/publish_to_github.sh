#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="${GITHUB_REPO_URL:-https://github.com/Faycal214/telecom-network-optimization.git}"
WORK_DIR="$(mktemp -d)"

trap 'rm -rf "$WORK_DIR"' EXIT

if ! command -v git >/dev/null 2>&1; then
    echo "Git is required." >&2
    exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
    echo "Installing dependency: rsync is required."
    echo "Run: sudo apt install rsync"
    exit 1
fi

echo "Cloning $REPO_URL ..."
git clone "$REPO_URL" "$WORK_DIR/repo"

echo "Copying project files, excluding Git internals..."

rsync -a \
    --exclude='.git/' \
    --exclude='.venv/' \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.pytest_cache/' \
    --exclude='*.pyc' \
    --exclude='*.egg-info/' \
    "$PROJECT_DIR"/ "$WORK_DIR/repo"/

cd "$WORK_DIR/repo"

git add -A

if git diff --cached --quiet; then
    echo "No changes to publish."
    exit 0
fi

echo
echo "Reviewing staged changes:"
git --no-pager diff --cached --stat

echo
echo "Creating commit..."
git commit -m "feat: add telecom network optimization research prototype"

echo
echo "Pushing to GitHub..."
git push origin HEAD

echo
echo "Published successfully: $REPO_URL"
