# GitHub Project Skills Permissions Architecture

**Date:** 2026-03-01
**Issue:** [#64](https://github.com/elahti/deneb-marketplace/issues/64)

## Problem

GitHub project skills invoke `uv run --project <path> python -m github_project_tools <subcommand>`, which causes Claude Code to prompt for `uv run.*` — a broad permission covering all `uv run` commands, not just github-project-tools. The existing `allowed-tools` frontmatter references the removed `github-projects.sh` shell script and is non-functional.

## Solution

Add a thin wrapper script that encapsulates the `uv run` invocation, giving each skill a unique, stable command prefix for per-subcommand permission scoping.

## Wrapper Script

**`plugins/github-project-tools/scripts/github-project-tools.sh`:**

```bash
#!/usr/bin/env bash
set -euo pipefail
HOOK_DIR="$(cd "$(dirname "$0")/../hook" && pwd)"
exec uv run --project "$HOOK_DIR" python -m github_project_tools "$@"
```

- Resolves `HOOK_DIR` as absolute path relative to the script's own location
- `exec` replaces the shell process — no extra process overhead
- All arguments forwarded, including `--repo owner/repo` when set

## Preflight Changes

`preflight.md` (shared across all 4 skills) changes:

1. **Glob target:** `~/.claude/plugins/**/github-project-tools/scripts/github-project-tools.sh` (was `**/hook/pyproject.toml`)
2. **`<cli>` definition:** The resolved absolute path to the wrapper script (was `uv run --project <HOOK_PATH> python -m github_project_tools`)

## Per-Subcommand `allowed-tools`

Each skill gets exact subcommand patterns in its YAML frontmatter. The `*/github-project-tools/scripts/github-project-tools.sh` prefix uniquely identifies this plugin.

### start-implementation

```yaml
allowed-tools:
  Bash(*/github-project-tools/scripts/github-project-tools.sh preflight),
  Bash(*/github-project-tools/scripts/github-project-tools.sh read-config),
  Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *),
  Bash(git rev-parse *),
  Bash(git checkout *),
  Bash(git worktree *)
```

### end-implementation

```yaml
allowed-tools:
  Bash(*/github-project-tools/scripts/github-project-tools.sh preflight),
  Bash(*/github-project-tools/scripts/github-project-tools.sh read-config),
  Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh count-open-sub-issues *)
```

### add-issue

```yaml
allowed-tools:
  Bash(*/github-project-tools/scripts/github-project-tools.sh preflight),
  Bash(*/github-project-tools/scripts/github-project-tools.sh read-config),
  Bash(*/github-project-tools/scripts/github-project-tools.sh issue-create *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *),
  Bash(*/github-project-tools/scripts/github-project-tools.sh set-parent *)
```

### setup-github-project-tools

```yaml
allowed-tools:
  Bash(*/github-project-tools/scripts/github-project-tools.sh preflight),
  Bash(*/github-project-tools/scripts/github-project-tools.sh read-config),
  Bash(gh repo view *),
  Bash(gh project *)
```

## Conventions Update

`conventions.md` (shared across all 4 skills) updates the first bullet to reflect that `<cli>` is now the resolved path to the wrapper script, not a `uv run` command. The literal-path-as-first-token rule still applies.

## Files Changed

| File | Change |
|------|--------|
| `scripts/github-project-tools.sh` | **New** — wrapper script |
| `skills/*/SKILL.md` (4 files) | Update `allowed-tools` frontmatter |
| `skills/*/prompts/preflight.md` (4 copies) | New glob target, new `<cli>` definition |
| `skills/*/prompts/conventions.md` (4 copies) | Reflect wrapper script invocation |
