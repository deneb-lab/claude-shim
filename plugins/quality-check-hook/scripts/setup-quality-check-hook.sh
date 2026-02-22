#!/usr/bin/env bash
# Setup helpers for the quality-check-hook setup skill
# Usage: scripts/setup-quality-check-hook.sh <subcommand> [args...]
#
# Subcommands:
#   check-uv                              Verify uv is installed
#   detect-runner                         Detect JS/TS package runner from lockfiles
#   build-excludes <dir1> <dir2> ...      Filter exclude candidates (exist + not gitignored)

set -euo pipefail

# --- Subcommands ---

cmd_check_uv() {
  if command -v uv &>/dev/null; then
    echo "OK"
  else
    echo "FAIL: uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
  fi
}

cmd_detect_runner() {
  if [[ -f "bun.lockb" || -f "bun.lock" ]]; then echo "bunx"
  elif [[ -f "pnpm-lock.yaml" ]]; then echo "pnpx"
  else echo "npx"
  fi
}

cmd_build_excludes() {
  for dir in "$@"; do
    if [[ -d "$dir" ]] && ! git check-ignore -q "$dir" 2>/dev/null; then
      echo "$dir"
    fi
  done
}

# --- Dispatch ---

case "${1:-}" in
  check-uv)        shift; cmd_check_uv "$@" ;;
  detect-runner)   shift; cmd_detect_runner "$@" ;;
  build-excludes)  shift; cmd_build_excludes "$@" ;;
  *)
    echo "Usage: $0 <check-uv|detect-runner|build-excludes> [args...]" >&2
    exit 1
    ;;
esac
