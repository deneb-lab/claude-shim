# Remove File-Based Content Passing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove all file-based content flags (`--body-file`, `--comment-file`) from the github-project-tools CLI and update the end-implementation skill to pass content inline.

**Architecture:** Remove `--body-file` from `issue-create` and `issue-edit`, remove `--comment-file` from `issue-close` and simplify its "already closed" branch. Update the SKILL.md and conventions.md across all skills.

**Tech Stack:** Python (cli.py), pytest, Markdown (SKILL.md, conventions.md)

---

### Task 1: Remove `--body-file` from `issue-create`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:233-266`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py:144-241`

**Step 1: Remove the `--body-file` branch from `cmd_issue_create`**

In `cli.py`, remove lines 245-247 (the `elif args[i] == "--body-file"` block):

```python
# REMOVE these 3 lines:
        elif args[i] == "--body-file":
            body = Path(args[i + 1]).read_text()
            i += 2
```

**Step 2: Remove the `test_create_with_body_file` test**

In `test_cli.py`, remove the entire `test_create_with_body_file` method (lines 199-225).

**Step 3: Run tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate -v`
Expected: All remaining `TestIssueCreate` tests PASS.

**Step 4: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): remove --body-file from issue-create"
```

---

### Task 2: Remove `--body-file` from `issue-edit`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:269-288`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py:244-297`

**Step 1: Remove the `--body-file` branch from `cmd_issue_edit`**

In `cli.py`, remove lines 276-278 (the `elif args[i] == "--body-file"` block):

```python
# REMOVE these 3 lines:
        elif args[i] == "--body-file":
            body = Path(args[i + 1]).read_text()
            i += 2
```

**Step 2: Remove the `test_edit_with_body_file` test**

In `test_cli.py`, remove the entire `test_edit_with_body_file` method (lines 267-289).

**Step 3: Run tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueEdit -v`
Expected: All remaining `TestIssueEdit` tests PASS.

**Step 4: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): remove --body-file from issue-edit"
```

---

### Task 3: Remove `--comment-file` from `issue-close` and simplify

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:291-338`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py:316-454`

**Step 1: Rewrite `cmd_issue_close` to remove `--comment-file` and simplify**

Replace the entire function body with:

```python
def cmd_issue_close(repo: str, number: str, args: list[str]) -> int:
    comment = ""
    i = 0
    while i < len(args):
        if args[i] == "--comment":
            comment = args[i + 1]
            i += 2
        else:
            print(f"issue-close: unknown arg: {args[i]}", file=sys.stderr)
            return 1

    # Check current issue state
    state_result = run_gh(
        ["issue", "view", number, "--repo", repo, "--json", "state", "--jq", ".state"]
    )
    state = state_result.stdout.strip()

    if state == "OPEN":
        cmd = ["issue", "close", number, "--repo", repo, "--reason", "completed"]
        if comment:
            cmd.extend(["--comment", comment])
        run_gh(cmd)
    else:
        print(f"Issue #{number} is already closed — skipping close.", file=sys.stderr)
        if comment:
            run_gh(["issue", "comment", number, "--repo", repo, "--body", comment])
    return 0
```

Changes from original:
- Removed `comment_file` variable
- Removed `--comment-file` arg parsing
- Removed `if comment_file: comment = Path(comment_file).read_text()`
- Simplified "already closed" branch: removed `if comment_file` / `--body-file` path, always uses `--body` inline

**Step 2: Remove file-based tests from `TestIssueClose`**

Remove these two test methods:
- `test_closes_with_comment_file` (lines 360-385)
- `test_closed_issue_with_comment_file_uses_body_file` (lines 426-454)

**Step 3: Run tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueClose -v`
Expected: All remaining `TestIssueClose` tests PASS (closes_open_issue, closes_with_comment, skips_close_for_closed_issue, closed_issue_with_comment_adds_comment).

**Step 4: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): remove --comment-file from issue-close"
```

---

### Task 4: Update end-implementation SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:98-107`

**Step 1: Replace the temp file instructions with inline `--comment`**

Replace lines 98-107:

```markdown
2. Close the issue. If `SUMMARY` is non-empty (from Phase 2.5), write it to a temp file and include it as a closing comment:
   - Write the summary to `/tmp/issue-close-comment.md` using the Write tool
   - Then close:
     ```bash
     <cli> issue-close <number> --comment-file /tmp/issue-close-comment.md
     ```
   If `SUMMARY` is empty, close without a comment:
   ```bash
   <cli> issue-close <number>
   ```
```

With:

```markdown
2. Close the issue. If `SUMMARY` is non-empty (from Phase 2.5), include it as a closing comment:
   ```bash
   <cli> issue-close <number> --comment "SUMMARY"
   ```
   If `SUMMARY` is empty, close without a comment:
   ```bash
   <cli> issue-close <number>
   ```
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): use inline --comment in end-implementation skill"
```

---

### Task 5: Update conventions.md (all 4 copies)

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/conventions.md:2`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/conventions.md:2`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/conventions.md:2`
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/prompts/conventions.md:2`

**Step 1: Update line 2 in all 4 copies**

Replace:
```
- **No command substitution** in bash commands — never use `$(...)`. If logic is needed, add it to the CLI. Use `--body-file` for multi-line content (write to a temp file with the Write tool first).
```

With:
```
- **No command substitution** in bash commands — never use `$(...)`. If logic is needed, add it to the CLI. Pass multi-line content inline via `--body` or `--comment`.
```

**Step 2: Verify all copies are identical**

Run: `git diff` and verify all 4 files have the same change.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/conventions.md
git commit -m "feat(github-project-tools): update conventions to remove --body-file guidance"
```

---

### Task 6: Run full test suite and lint

**Step 1: Run all tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: All tests PASS.

**Step 2: Run linters**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All clean.

**Step 3: Check if `Path` import is still needed**

Verify `Path` is still used in `cli.py` for type annotations (`load_config_or_fail`, `cmd_read_config`, `main`). If the import `from pathlib import Path` is no longer used anywhere, remove it. (It should still be needed for the `cwd: Path` parameter types.)
