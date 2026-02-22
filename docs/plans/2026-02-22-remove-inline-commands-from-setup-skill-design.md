# Design: Remove Inline Commands from quality-check-hook Setup Skill

## Problem

The setup-quality-check-hook SKILL.md contains inline Bash commands (multi-line loops, `$()` subshells) that trigger Claude Code permission prompts every time the skill runs. Specifically:

- `which uv` prerequisite check (bash code block)
- Lockfile detection logic (checking for bun.lockb, pnpm-lock.yaml, etc.)
- `git check-ignore -q` loop over candidate exclude directories

## Solution

Create a single dispatch script `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh` following the established `github-projects.sh` pattern, then update the SKILL.md to call it instead of using inline commands.

## Script: `scripts/setup-quality-check-hook.sh`

### Subcommands

| Subcommand | Args | Output | Purpose |
|---|---|---|---|
| `check-uv` | none | "OK" to stdout, or error to stderr + exit 1 | Verify uv is installed |
| `detect-runner` | none | Runner name: `bunx`, `pnpx`, or `npx` | Detect JS package runner from lockfiles in cwd |
| `build-excludes` | `<dir1> <dir2> ...` | One dir per line (only dirs that exist AND are not gitignored) | Filter exclude candidates |

### Implementation

```bash
#!/usr/bin/env bash
set -euo pipefail

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

case "${1:-}" in
  check-uv)        shift; cmd_check_uv "$@" ;;
  detect-runner)   shift; cmd_detect_runner "$@" ;;
  build-excludes)  shift; cmd_build_excludes "$@" ;;
  *)
    echo "Usage: $0 <check-uv|detect-runner|build-excludes> [args...]" >&2
    exit 1 ;;
esac
```

## SKILL.md Changes

### Prerequisites (lines 37-51)

**Before:** Inline `which uv` bash code block
**After:** `Run scripts/setup-quality-check-hook.sh check-uv`

### Step 2 — Detect Package Runner (lines 63-75)

**Before:** Lockfile detection table with manual instructions
**After:** `Run scripts/setup-quality-check-hook.sh detect-runner` — table removed, logic is in the script

### Step 4 — Build Exclude List (lines 105-119)

**Before:** Per-directory loop checking existence + `git check-ignore -q`
**After:** `Run scripts/setup-quality-check-hook.sh build-excludes <candidates...>`

### No changes needed

- Step 1 (check existing config) — uses Read/AskUserQuestion
- Step 3 (detect tooling) — uses Read/Glob tools
- Step 5 (present config) — text output
- Step 6 (write config) — uses Write tool
