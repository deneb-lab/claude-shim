# Remove Inline Commands from Setup Skill — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract all inline Bash commands from the quality-check-hook setup skill into a dispatch script so Claude Code never triggers permission prompts when running the skill.

**Architecture:** Single dispatch script `scripts/setup-quality-check-hook.sh` with subcommands (`check-uv`, `detect-runner`, `build-excludes`), following the established `github-projects.sh` pattern. The SKILL.md is updated to call the script instead of using inline commands.

**Tech Stack:** Bash, shellcheck for linting

---

### Task 1: Create the dispatch script

**Files:**
- Create: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh`

**Step 1: Create the script**

```bash
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
```

**Step 2: Make it executable**

Run: `chmod +x plugins/quality-check-hook/scripts/setup-quality-check-hook.sh`

**Step 3: Verify script runs**

Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh check-uv`
Expected: `OK` (assuming uv is installed)

Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh detect-runner`
Expected: `npx` (or whichever runner matches current directory)

Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh build-excludes /tmp /nonexistent`
Expected: `/tmp` (exists, not gitignored) — `/nonexistent` is silently skipped

Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh`
Expected: Usage message on stderr, exit 1

**Step 4: Lint with shellcheck**

Run: `shellcheck plugins/quality-check-hook/scripts/setup-quality-check-hook.sh`
Expected: No warnings

**Step 5: Commit**

```
git add plugins/quality-check-hook/scripts/setup-quality-check-hook.sh
git commit -m "feat(quality-check-hook): add setup helper dispatch script"
```

---

### Task 2: Update SKILL.md — Prerequisites section

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md:37-51`

**Step 1: Replace the Prerequisites section**

Replace lines 37-51 (from `## Prerequisites` through `Do not proceed until`) with:

```markdown
## Prerequisites

Run `scripts/setup-quality-check-hook.sh check-uv` to verify that `uv` is installed.

If the command fails, stop and tell the user:

> The quality-check-hook plugin requires uv to run. Install it with:
> `curl -LsSf https://astral.sh/uv/install.sh | sh`
> See https://docs.astral.sh/uv/getting-started/installation/ for other methods.

Do not proceed until `uv` is available.
```

Key change: The ` ```bash / which uv / ``` ` code block is gone. Claude now calls the script instead.

**Step 2: Commit**

```
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): replace inline uv check with script call"
```

---

### Task 3: Update SKILL.md — Step 2 (Detect Package Runner)

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md:63-75`

**Step 1: Replace Step 2 section**

Replace lines 63-75 (from `## Step 2: Detect Package Runner` through the confirmation prompt) with:

```markdown
## Step 2: Detect Package Runner

Run `scripts/setup-quality-check-hook.sh detect-runner` to determine the JavaScript/TypeScript package runner. The script checks lockfiles in the repository root and outputs the runner name (`bunx`, `pnpx`, or `npx`).

Use the detected runner (referred to as `{runner}` below) in all JS/TS commands. Present it to the user for confirmation: "Detected `{runner}` as the package runner. Change?"
```

Key change: The lockfile-to-runner mapping table is removed. The logic now lives in the script.

**Step 2: Commit**

```
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): replace inline runner detection with script call"
```

---

### Task 4: Update SKILL.md — Step 4 (Build Exclude List)

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md:105-119`

**Step 1: Replace the candidate filtering instructions**

Replace lines 113-117 (from `**For each candidate:**` through `Only include candidates that **exist AND are NOT gitignored**.`) with:

```markdown
Run `scripts/setup-quality-check-hook.sh build-excludes <candidates...>` where `<candidates...>` is the space-separated list of directories from above. The script outputs one directory per line — only directories that actually exist in the repo AND are not gitignored.

Use the script output as the exclude list.
```

Keep the candidate lists (JS/TS candidates, Python candidates, General candidates) and the user-facing message about gitignore — those are still needed for context.

**Step 2: Commit**

```
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): replace inline exclude-building loop with script call"
```

---

### Task 5: Final verification

**Step 1: Read the final SKILL.md end-to-end**

Read the complete file and verify:
- No ```` ```bash ```` code blocks remain (there should be zero executable bash blocks)
- All three script calls are present: `check-uv`, `detect-runner`, `build-excludes`
- The rest of the skill (Steps 1, 3, 5, 6) is unchanged
- No references to inline `git check-ignore` or `which uv` remain in instructional context (backtick references in "How the Hook Works" are fine — those are documentation, not commands)

**Step 2: Run shellcheck on the script one more time**

Run: `shellcheck plugins/quality-check-hook/scripts/setup-quality-check-hook.sh`
Expected: No warnings

**Step 3: Verify script subcommands all work**

Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh check-uv`
Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh detect-runner`
Run: `plugins/quality-check-hook/scripts/setup-quality-check-hook.sh build-excludes node_modules dist`

All should succeed without error.
