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
for tool in brew git gh uv python3.12 node rg jq tmux git-lfs fzf zoxide fd personal-apps; do
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
profile_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
if command -v python3.12 >/dev/null 2>&1; then
  if python3.12 "$profile_root/tools/check_checkout.py" "$profile_root"; then
    printf 'OK full dotfiles checkout\n'
  else failures=$((failures + 1)); fi
fi
if [ "$(uname -s)" = Darwin ] && command -v swift >/dev/null 2>&1; then
  if swift "$profile_root/tools/check-font.swift"; then
    printf 'OK Meslo Powerline glyphs\n'
  else failures=$((failures + 1)); fi
fi
printf 'Baseline findings: %s\n' "$failures"
exit "$((failures > 0))"
