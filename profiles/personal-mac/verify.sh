#!/bin/bash
# Read-only baseline check. Does not install, authenticate, start services or list secrets.
set -u
failures=0
check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'OK command: %s\n' "$1"
  else
    printf 'MISSING command: %s\n' "$1"
    failures=$((failures + 1))
  fi
}
if [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ]; then
  printf 'OK native Apple Silicon shell\n'
else
  printf 'MISSING native macOS arm64 shell\n'
  failures=$((failures + 1))
fi
if xcode-select -p >/dev/null 2>&1; then
  printf 'OK developer tools\n'
else
  printf 'MISSING developer tools\n'
  failures=$((failures + 1))
fi
for tool in brew git gh uv node rg jq tmux git-lfs; do
  check_command "$tool"
done
if command -v node >/dev/null 2>&1; then
  if node -e 'const v=process.versions.node.split(".").map(Number); process.exit(v[0]===24 ? 0 : 1)' ; then
    printf 'OK selected Node 24 runtime\n'
  else
    printf 'CHECK Node selection: this profile expects Node 24 on PATH\n'
    failures=$((failures + 1))
  fi
fi
printf 'Baseline findings: %s\n' "$failures"
exit "$((failures > 0))"
