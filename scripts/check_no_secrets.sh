#!/usr/bin/env bash
# Fail if anything that looks like a committed secret is present.
set -euo pipefail

patterns=(
  'sk-ant-'
  'ntn_'
  'nvapi-[A-Za-z0-9_-]{10,}'
  'AKIA[0-9A-Z]{16}'
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
)

fail=0
for pattern in "${patterns[@]}"; do
  if git grep -n -E "$pattern" -- . 2>/dev/null; then
    echo "check_no_secrets: matched pattern: $pattern"
    fail=1
  fi
done

# Real env files must never be tracked.
if git ls-files | grep -E '(^|/)\.env(\..+)?$' | grep -v -E '\.env\.example$' ; then
  echo "check_no_secrets: a real .env file is tracked"
  fail=1
fi

exit "$fail"
