# Fix issue-close --comment for already-closed issues

## Problem

When `gh issue close` encounters an already-closed issue (e.g., auto-closed by PR merge), it prints a warning and exits non-zero without posting the `--comment`. The `cmd_issue_close` function in `github-projects.sh` delegates directly to `gh issue close` and does not handle this case, silently dropping the comment.

## Approach

Check issue state before closing. If already closed, post the comment separately.

## Changes

### `cmd_issue_close` in `github-projects.sh`

1. Add `--comment-file` flag (reads comment from file path, matching `--body-file` pattern from `issue-create`/`issue-edit`).
2. Before running `gh issue close`, check issue state via `gh issue view <number> --repo "$REPO" --json state -q .state`.
3. If OPEN: proceed as today with `gh issue close --comment`.
4. If CLOSED: skip `gh issue close`. If a comment was provided, post via `gh issue comment <number> --repo "$REPO" --body-file <file>` (or `--body` for inline).

### Skill prompts

No changes needed. The end-implementation skill calls `issue-close` which will now handle the already-closed case internally. All three call sites (main issue with comment, main issue without comment, parent issue) go through the same function.

## Scope

- Single function change in `github-projects.sh`
- No skill prompt changes
- No new subcommands
