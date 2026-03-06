# Fix Silent Error Swallowing in CLI

## Problem

The github-project-tools CLI silently swallows errors from `gh` and GraphQL calls. 20 out of 25 functions that call `run_gh()` or `graphql()` always return 0, never check `result.returncode`, and never print `result.stderr`. This makes failures invisible to callers (including Claude).

Triggered by issue #81: `issue-create` silently fails when `gh issue create --label` fails (e.g., label doesn't exist in the repo). No URL, no error, exit code 0.

## Changes

### 1. Remove `--label` from add-issue (YAGNI)

The `--label` flag was added speculatively. It's not part of the documented workflow — Phase 2 (Gather Context) never mentions labels, no other skill depends on them, and users have no documented way to specify them.

Remove from:
- `skills/add-issue/SKILL.md` line 40 — the instruction to use `--label`
- `cli.py` `cmd_issue_create()` — the `--label` parsing and pass-through
- `test_cli.py` — the `test_create_with_label` test

### 2. Add `check_result` helper

Add a helper function to `cli.py`:

```python
def check_result(result: subprocess.CompletedProcess[str], label: str) -> int | None:
    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else ""
        msg = f"{label}: {stderr}" if stderr else f"{label}: command failed"
        print(msg, file=sys.stderr)
        return result.returncode
    return None
```

Returns `None` on success (caller continues), or the exit code on failure (caller early-returns).

### 3. Apply `check_result` to all 20 affected functions

Each function that calls `run_gh()` or `graphql()` and currently ignores errors gets the pattern:

```python
result = run_gh(cmd)
if (rc := check_result(result, "issue-create")) is not None:
    return rc
```

Affected functions:
- `cmd_project_list`
- `cmd_project_field_list`
- `cmd_issue_view`
- `cmd_issue_view_full`
- `cmd_issue_create`
- `cmd_issue_assign`
- `cmd_issue_get_assignees`
- `cmd_issue_list`
- `cmd_get_project_item`
- `cmd_get_start_date`
- `cmd_get_status_change_date`
- `cmd_add_to_project`
- `cmd_set_status`
- `cmd_list_status_options`
- `cmd_set_status_by_option_id`
- `cmd_set_date`
- `cmd_get_parent`
- `cmd_count_open_sub_issues`
- `cmd_list_sub_issues`
- `cmd_set_parent`

### 4. Add tests

- Test that `check_result` returns `None` on success, exit code on failure, prints stderr
- Test `cmd_issue_create` error propagation (gh fails -> exit code + stderr)
- Test a representative graphql-based command error propagation

### Not changing

- `run_gh()` contract — unchanged
- Functions with existing error handling (`detect_repo`, `get_project_id`, `cmd_preflight`, `cmd_issue_close`) — already correct
- Skills — no changes needed; CLI error propagation makes errors visible to Claude
- quality-check-hook — `2>/dev/null` on `git check-ignore` is intentional
