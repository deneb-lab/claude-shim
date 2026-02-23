# Design: Remove Command Substitution from All Skills

## Problem

Skills instruct Claude to run bash commands containing `$()` command substitution, which triggers Claude Code's permission prompt every time. Two patterns cause this:

1. **Date substitution:** `set-date "$ITEM_ID" "$FIELD" "$(date +%Y-%m-%d)"` in start-implementation and end-implementation (4 occurrences)
2. **Heredoc substitution:** `--body "$(cat <<'EOF'...EOF)"` in trivy-audit report-writer (3 occurrences)

## Solution

### Change 1: `set-date` always uses today's date

The date parameter is always `$(date +%Y-%m-%d)` — no skill ever passes a specific date. Remove the date parameter entirely and have the script resolve today's date internally.

**Before:** `set-date <item-id> <field-id> <date>` (3 args)
**After:** `set-date <item-id> <field-id>` (2 args)

Script implementation:

```bash
cmd_set_date() {
  local item="$1" field="$2"
  local date
  date=$(date +%Y-%m-%d)
  # graphql mutation unchanged, uses $date
}
```

Affected files:
- `plugins/github-project-tools/scripts/github-projects.sh` — change `cmd_set_date`, update usage header
- `plugins/trivy-audit/scripts/github-projects.sh` — same change (separate copy)
- `plugins/github-project-tools/skills/start-implementation/SKILL.md` — 2 occurrences, remove `"$(date +%Y-%m-%d)"` arg
- `plugins/github-project-tools/skills/end-implementation/SKILL.md` — 2 occurrences, remove `"$(date +%Y-%m-%d)"` arg
- Remove `Bash(date:*)` from `allowed-tools` in both skill frontmatters

### Change 2: `--body-file` flag for multi-line bodies

Add `--body-file <path>` as an alternative to `--body` in `issue-create` and `issue-edit`. The script reads file contents into the body variable.

Script implementation (in both `cmd_issue_create` and `cmd_issue_edit`):

```bash
--body-file) body=$(cat "$2"); shift 2 ;;
```

Affected files:
- `plugins/github-project-tools/scripts/github-projects.sh` — add `--body-file` to `cmd_issue_create` and `cmd_issue_edit`
- `plugins/trivy-audit/scripts/github-projects.sh` — same change
- `plugins/trivy-audit/skills/report/prompts/report-writer.md` — change `--body "$(cat <<'ISSUE_EOF'...)"` to Write tool + `--body-file /tmp/trivy-audit-<purpose>.md`

### Convention updates

Update all conventions.md files to document:
- `set-date` no longer takes a date parameter
- Prefer `--body-file` over inline `--body` for multi-line content
- Write multi-line bodies to named temp files in `/tmp/` before passing to script
