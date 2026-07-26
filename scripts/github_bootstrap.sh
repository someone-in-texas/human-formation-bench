#!/usr/bin/env bash
set -euo pipefail

OWNER="$(gh api user --jq .login)"
REPO="${HFB_REPO_NAME:-human-formation-bench}"
FULL_REPO="$OWNER/$REPO"

gh repo view "$FULL_REPO" >/dev/null
gh repo edit "$FULL_REPO" \
  --description "An open, research-grounded benchmark for how AI interactions may support or undermine human agency, truthfulness, relationships, humility, and flourishing." \
  --enable-issues \
  --enable-discussions \
  --enable-projects=false \
  --enable-wiki=false \
  --enable-secret-scanning \
  --enable-secret-scanning-push-protection \
  --allow-update-branch \
  --delete-branch-on-merge \
  --enable-squash-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge

gh api --method PUT -H "Accept: application/vnd.github+json" "/repos/$FULL_REPO/topics" \
  -f names[]='ai-evaluation' \
  -f names[]='ai-alignment' \
  -f names[]='human-ai-interaction' \
  -f names[]='psychometrics' \
  -f names[]='inspect-ai' \
  -f names[]='responsible-ai' \
  -f names[]='open-source' \
  -f names[]='benchmark' >/dev/null

for endpoint in vulnerability-alerts automated-security-fixes private-vulnerability-reporting; do
  if ! gh api --method PUT "/repos/$FULL_REPO/$endpoint" >/dev/null 2>&1; then
    printf 'Warning: GitHub rejected %s; inspect plan or feature availability.\n' "$endpoint" >&2
  fi
done

labels=(
  "bug:d73a4a"
  "enhancement:a2eeef"
  "research:1d76db"
  "psychometrics:5319e7"
  "philosophy:8a2be2"
  "alignment:e99695"
  "security:b60205"
  "scenario:0e8a16"
  "rubric:fbca04"
  "documentation:0075ca"
  "good first issue:7057ff"
  "help wanted:008672"
  "breaking change:b60205"
  "blocked:000000"
  "needs evidence:d4c5f9"
  "needs human review:f9d0c4"
  "dependencies:0366d6"
  "stale:ededed"
)
for item in "${labels[@]}"; do
  name="${item%:*}"
  color="${item##*:}"
  gh label create "$name" --repo "$FULL_REPO" --color "$color" --force >/dev/null
done

printf 'Configured %s. Rulesets are intentionally applied after stable checks complete once.\n' "$FULL_REPO"
