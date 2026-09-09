#!/bin/bash
# Checkpoint the project to GitHub. Run from the repo: bash project/sync.sh ["message"]
set -u
cd "$(dirname "$0")/.." || exit 1

# A stale lock is left behind if a git process was killed (or ran from a sandbox
# that could not clean up). Remove it only when no git process is actually running.
if [ -f .git/index.lock ]; then
  if pgrep -x git >/dev/null 2>&1; then
    echo "git is running; not touching .git/index.lock" >&2; exit 1
  fi
  echo "removing stale .git/index.lock"
  rm -f .git/index.lock || { echo "could not remove the lock" >&2; exit 1; }
fi

git add -A || { echo "git add failed" >&2; exit 1; }
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git commit -qm "${1:-checkpoint $(date '+%Y-%m-%d %H:%M')}" || { echo "commit failed" >&2; exit 1; }
git push -q origin main || { echo "push failed" >&2; exit 1; }
echo "pushed: $(git log --oneline -1)"
