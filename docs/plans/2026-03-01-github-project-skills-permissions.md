# GitHub Project Skills Permissions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace broad `uv run.*` permission with per-subcommand `allowed-tools` via a thin wrapper script.

**Architecture:** A new shell script `scripts/github-project-tools.sh` encapsulates the `uv run --project <path> python -m github_project_tools` invocation. Skills glob for the wrapper instead of `pyproject.toml`, making the script path the first token of every bash command. Each skill's frontmatter lists exact per-subcommand permissions.

**Tech Stack:** Bash (wrapper script), YAML frontmatter (allowed-tools), Markdown (skill prompts)

---

### Task 1: Create wrapper script

**Files:**
- Create: `plugins/github-project-tools/scripts/github-project-tools.sh`

**Step 1: Create the wrapper script**

```bash
#!/usr/bin/env bash
set -euo pipefail
HOOK_DIR="$(cd "$(dirname "$0")/../hook" && pwd)"
exec uv run --project "$HOOK_DIR" python -m github_project_tools "$@"
```

Make it executable: `chmod +x plugins/github-project-tools/scripts/github-project-tools.sh`

**Step 2: Run shellcheck**

Run: `shellcheck plugins/github-project-tools/scripts/github-project-tools.sh`
Expected: No warnings.

**Step 3: Smoke-test the wrapper**

Run: `plugins/github-project-tools/scripts/github-project-tools.sh preflight`
Expected: `OK: gh CLI authenticated with repo + project scopes`

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-project-tools.sh
git commit -m "feat(github-project-tools): add wrapper script for CLI invocation"
```

---

### Task 2: Update preflight.md (all 4 copies)

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/preflight.md`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/preflight.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/preflight.md`
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/prompts/preflight.md`

**Step 1: Replace all 4 copies with new content**

Replace the entire contents of each file with:

```markdown
1. Find the bundled CLI wrapper. Use Glob to locate it:
   ```
   ~/.claude/plugins/**/github-project-tools/scripts/github-project-tools.sh
   ```
   Store the matched path as `CLI_PATH`. For example, if the match is `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/2.1.0/scripts/github-project-tools.sh`, then `CLI_PATH` is that full path.

2. All commands for the rest of this skill use this invocation pattern:
   ```bash
   <CLI_PATH> <subcommand> [args...]
   ```
   Referred to as `<cli> <subcommand>` in the rest of this document.

3. Run preflight checks:
   ```bash
   <cli> preflight
   ```
4. If preflight fails, stop and show the error message to the user. Do not proceed.
```

**Step 2: Verify all 4 copies are identical**

Run: `diff plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/start-implementation/prompts/preflight.md && diff plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/end-implementation/prompts/preflight.md && diff plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/setup-github-project-tools/prompts/preflight.md && echo "All in sync"`
Expected: `All in sync`

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/preflight.md
git commit -m "feat(github-project-tools): update preflight to use wrapper script"
```

---

### Task 3: Update conventions.md (all 4 copies)

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/prompts/conventions.md`

**Step 1: Replace all 4 copies with new content**

Replace the entire contents of each file with:

```markdown
- **CLI invocation:** The `<cli>` prefix (see preflight) MUST be the literal resolved path to `github-project-tools.sh` as the first token of every bash command — e.g. `<cli> issue-assign 14`. NEVER split the path into a variable. Claude Code matches permissions by the first token; variable-wrapped paths produce a different fingerprint every time, forcing repeated approval prompts.
- **No command substitution** in bash commands — never use `$(...)`. If logic is needed, add it to the CLI. Use `--body-file` for multi-line content (write to a temp file with the Write tool first).
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `<cli>` — never call `gh` directly.
- **Date field IDs** come from the config (read during setup). They may change if the project is recreated — re-run the setup skill to refresh.
- **Project is optional.** If no config is found during setup and the user declines to configure, skip all project operations (get-project-item, add-to-project, set-date, set-status) but still perform issue operations (assign, view, close, parent check).
```

The only change is in bullet 1: "literal first tokens" → "literal resolved path to `github-project-tools.sh` as the first token".

**Step 2: Verify all 4 copies are identical**

Run: `diff plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/start-implementation/prompts/conventions.md && diff plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/end-implementation/prompts/conventions.md && diff plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/setup-github-project-tools/prompts/conventions.md && echo "All in sync"`
Expected: `All in sync`

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/conventions.md
git commit -m "feat(github-project-tools): update conventions for wrapper script invocation"
```

---

### Task 4: Update allowed-tools in all 4 SKILL.md frontmatters

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:1-5` (frontmatter)
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:1-5` (frontmatter)
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md:1-4` (frontmatter)
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:1-4` (frontmatter)

**Step 1: Update start-implementation frontmatter**

Replace lines 1-5 with:

```yaml
---
name: start-implementation
description: Start implementing a GitHub issue - assigns, sets dates/status, and presents issue context
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *), Bash(git rev-parse *), Bash(git checkout *), Bash(git worktree *)
---
```

**Step 2: Update end-implementation frontmatter**

Replace lines 1-5 with:

```yaml
---
name: end-implementation
description: Close a GitHub issue - sets end date, done status, closes issue, updates parent lifecycle
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *), Bash(*/github-project-tools/scripts/github-project-tools.sh count-open-sub-issues *)
---
```

**Step 3: Update add-issue frontmatter**

Replace lines 1-4 with:

```yaml
---
name: add-issue
description: Create a GitHub issue from conversation context and add it to the project board with Todo status
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-create *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-parent *)
---
```

**Step 4: Update setup-github-project-tools frontmatter**

Replace lines 1-4 with:

```yaml
---
name: setup-github-project-tools
description: Set up or modify github-project-tools configuration in .claude-shim.json for the current repository
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(gh repo view *), Bash(gh project *)
---
```

**Step 5: Commit**

```bash
git add plugins/github-project-tools/skills/*/SKILL.md
git commit -m "feat(github-project-tools): add per-subcommand allowed-tools to all skills"
```

---

### Task 5: Run CI checks locally

**Step 1: Run shellcheck on all .sh files**

Run: `find plugins/github-project-tools -name '*.sh' -print0 | xargs -0 shellcheck`
Expected: No warnings.

**Step 2: Run shared prompt sync check**

Run the same diff checks from CI:

```bash
base=plugins/github-project-tools/skills
for file in preflight.md conventions.md; do
  for skill in start-implementation end-implementation setup-github-project-tools; do
    diff -q "$base/add-issue/prompts/$file" "$base/$skill/prompts/$file"
  done
done
echo "All shared prompts in sync"
```

Expected: No diff output, followed by `All shared prompts in sync`.

**Step 3: Verify no regressions in hook tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: All tests pass (wrapper script doesn't change Python code).
