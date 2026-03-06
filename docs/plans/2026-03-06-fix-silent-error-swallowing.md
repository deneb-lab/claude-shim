# Fix Silent Error Swallowing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 20 CLI functions that silently swallow errors from `gh`/GraphQL calls, and remove the YAGNI `--label` feature from `issue-create`.

**Architecture:** Add a `check_result` helper that checks `returncode`, prints `stderr`, and returns the exit code on failure. Apply it to all affected functions. Remove `--label` from skill and CLI.

**Tech Stack:** Python 3, pytest, `gh` CLI

---

### Task 1: Remove `--label` from add-issue skill

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md:40`

**Step 1: Remove the label instruction**

Delete line 40 from `SKILL.md`:
```
   If the user specified a label, add `--label "<label>"`.
```

The surrounding lines (37-42) should become:
```markdown
   ```bash
   <cli> issue-create --title "<title>" --body "<body>"
   ```

   The output is the issue URL. Extract the issue number from the URL path.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/add-issue/SKILL.md
git commit -m "fix(github-project-tools): remove YAGNI --label from add-issue skill"
```

---

### Task 2: Add `check_result` helper with tests

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:11` (insert after imports)
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py` (add new test class)

**Step 1: Write the failing tests**

Add a new test class at the end of `test_cli.py`:

```python
class TestCheckResult:
    def test_returns_none_on_success(self) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok\n", stderr=""
        )
        assert check_result(result, "test-cmd") is None

    def test_returns_exit_code_on_failure(self) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="something broke"
        )
        assert check_result(result, "test-cmd") == 2

    def test_prints_stderr_with_label(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="label 'task' not found"
        )
        check_result(result, "issue-create")
        err = capsys.readouterr().err
        assert "issue-create" in err
        assert "label 'task' not found" in err

    def test_prints_generic_message_when_no_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )
        check_result(result, "set-status")
        err = capsys.readouterr().err
        assert "set-status" in err
        assert "command failed" in err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestCheckResult -v`
Expected: FAIL with `ImportError` (function doesn't exist yet)

**Step 3: Implement `check_result`**

Add after the imports section in `cli.py` (after line 9, before `run_gh`):

```python
def check_result(result: subprocess.CompletedProcess[str], label: str) -> int | None:
    """Check a subprocess result, print stderr on failure, return exit code or None."""
    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else ""
        msg = f"{label}: {stderr}" if stderr else f"{label}: command failed"
        print(msg, file=sys.stderr)
        return result.returncode
    return None
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestCheckResult -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add check_result helper for error propagation"
```

---

### Task 3: Remove `--label` from CLI and test error propagation for `issue-create`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:233-263`
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py` (remove label test, add error test)

**Step 1: Write the failing error propagation test**

Add to `TestIssueCreate` class in `test_cli.py`:

```python
    def test_create_gh_failure_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="label 'task' not found",
            )
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                ]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-create" in err
        assert "label 'task' not found" in err
```

**Step 2: Run to verify it fails**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate::test_create_gh_failure_propagates_error -v`
Expected: FAIL (exit_code is 0, not 1)

**Step 3: Remove `--label` and add error checking to `cmd_issue_create`**

Replace `cmd_issue_create` (lines 233-263) with:

```python
def cmd_issue_create(repo: str, args: list[str]) -> int:
    title = ""
    body = ""
    i = 0
    while i < len(args):
        if args[i] == "--title":
            title = args[i + 1]
            i += 2
        elif args[i] == "--body":
            body = args[i + 1]
            i += 2
        else:
            print(f"issue-create: unknown arg: {args[i]}", file=sys.stderr)
            return 1
    if not title:
        print("issue-create: --title required", file=sys.stderr)
        return 1
    if not body:
        print("issue-create: --body required", file=sys.stderr)
        return 1
    result = run_gh(
        ["issue", "create", "--repo", repo, "--title", title, "--body", body]
    )
    if (rc := check_result(result, "issue-create")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**Step 4: Delete `test_create_with_label`**

Remove the `test_create_with_label` method (lines 257-281 in the original test file).

**Step 5: Run all issue-create tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate -v`
Expected: PASS (all tests including new error propagation test)

**Step 6: Also verify `--label` is now rejected as unknown arg**

Add test:

```python
    def test_create_rejects_label_flag(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--label",
                    "bug",
                ]
            )
        assert exit_code == 1
        assert "unknown arg" in capsys.readouterr().err.lower()
```

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate::test_create_rejects_label_flag -v`
Expected: PASS

**Step 7: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "fix(github-project-tools): remove --label from issue-create, add error propagation"
```

---

### Task 4: Add error checking to `run_gh`-based commands

These 7 functions call `run_gh()` directly and always return 0. Apply `check_result` to each.

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`

**Functions to fix (with the pattern):**

Each follows the same transformation — insert a `check_result` call between the `run_gh` call and the stdout print:

**`cmd_project_list`** (line 167-170):
```python
    result = run_gh(["project", "list", "--owner", owner, "--format", "json"])
    if (rc := check_result(result, "project-list")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_project_field_list`** (line 198-203):
```python
    result = run_gh(
        ["project", "field-list", number, "--owner", owner, "--format", "json"]
    )
    if (rc := check_result(result, "project-field-list")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_issue_view`** (line 210-213):
```python
    result = run_gh(["issue", "view", number, "--repo", repo, *extra_args])
    if (rc := check_result(result, "issue-view")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_issue_view_full`** (line 217-230):
```python
    result = run_gh(
        [
            "issue",
            "view",
            number,
            "--repo",
            repo,
            "--json",
            "id,number,title,body,state",
        ]
    )
    if (rc := check_result(result, "issue-view-full")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_issue_assign`** (line 307-310):
```python
    result = run_gh(["issue", "edit", number, "--repo", repo, "--add-assignee", "@me"])
    if (rc := check_result(result, "issue-assign")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_issue_get_assignees`** (line 314-329):
```python
    result = run_gh(
        [
            "issue",
            "view",
            number,
            "--repo",
            repo,
            "--json",
            "assignees",
            "--jq",
            "[.assignees[].login]",
        ]
    )
    if (rc := check_result(result, "issue-get-assignees")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_issue_list`** (line 333-336):
```python
    result = run_gh(["issue", "list", "--repo", repo, *extra_args])
    if (rc := check_result(result, "issue-list")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**Step 1: Apply all changes above**

**Step 2: Write one representative error propagation test**

Add to `test_cli.py`:

```python
class TestRunGhErrorPropagation:
    """Verify run_gh-based commands propagate errors."""

    def test_issue_view_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="issue not found"
            )
            exit_code = main(
                ["--repo", "owner/repo", "issue-view", "999", "--json", "id"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-view" in err
        assert "issue not found" in err

    def test_issue_assign_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="permission denied"
            )
            exit_code = main(["--repo", "owner/repo", "issue-assign", "42"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-assign" in err

    def test_project_list_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="not found"
            )
            exit_code = main(["project-list", "--owner", "nobody"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "project-list" in err
```

**Step 3: Run all tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "fix(github-project-tools): add error propagation to run_gh-based commands"
```

---

### Task 5: Add error checking to `graphql`-based commands

These 12 functions call `graphql()` and always return 0. Some capture the result and print stdout, others don't capture it at all.

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`

**Group A — functions that already capture `result` (add check before stdout print):**

**`cmd_get_project_item`** (line 344-360):
```python
    result = graphql(...)
    if (rc := check_result(result, "get-project-item")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

**`cmd_get_start_date`** (line 366-397) — same pattern with label `"get-start-date"`.

**`cmd_get_status_change_date`** (line 403-431) — this one has custom output logic. Insert check before the custom logic:
```python
    result = graphql(...)
    if (rc := check_result(result, "get-status-change-date")) is not None:
        return rc
    out = result.stdout.strip() if result.stdout else ""
    if out and out != "null":
        print(out)
    else:
        print("null")
    return 0
```

**`cmd_add_to_project`** (line 436-448) — label `"add-to-project"`.

**`cmd_list_status_options`** (line 489-503) — label `"list-status-options"`.

**`cmd_get_parent`** (line 561-573) — label `"get-parent"`.

**`cmd_count_open_sub_issues`** (line 577-591) — label `"count-open-sub-issues"`.

**`cmd_list_sub_issues`** (line 595-611) — label `"list-sub-issues"`.

**`cmd_set_parent`** (line 615-627) — label `"set-parent"`.

**Group B — functions that DON'T capture result (need to capture it first):**

**`cmd_set_status`** (line 469-484):
```python
    result = graphql(
        """...""",
        {
            "project": project_id,
            "item": item_id,
            "field": field_id,
            "value": option_id,
        },
    )
    if (rc := check_result(result, "set-status")) is not None:
        return rc
    return 0
```

**`cmd_set_status_by_option_id`** (line 513-528) — same pattern with label `"set-status-by-option-id"`.

**`cmd_set_date`** (line 539-554) — same pattern with label `"set-date"`.

**Step 1: Apply all changes above**

**Step 2: Write representative error propagation tests**

Add to `test_cli.py`:

```python
class TestGraphqlErrorPropagation:
    """Verify graphql-based commands propagate errors."""

    def test_set_status_propagates_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="GraphQL error"
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "set-status" in err

    def test_add_to_project_propagates_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="mutation failed"
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "add-to-project", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "add-to-project" in err

    def test_set_parent_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="not found"
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-parent", "I_child", "I_parent"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "set-parent" in err
```

**Step 3: Run all tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "fix(github-project-tools): add error propagation to graphql-based commands"
```

---

### Task 6: Run full CI checks

**Step 1: Run all tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: All tests PASS

**Step 2: Run linter**

Run: `cd plugins/github-project-tools/hook && uv run ruff check`
Expected: No errors

**Step 3: Run formatter check**

Run: `cd plugins/github-project-tools/hook && uv run ruff format --check`
Expected: No formatting issues (if there are, run `uv run ruff format` and commit)

**Step 4: Run type checker**

Run: `cd plugins/github-project-tools/hook && uv run pyright`
Expected: No errors

**Step 5: Run shellcheck**

Run: `find plugins/ -name '*.sh' -exec shellcheck {} +`
Expected: No errors

**Step 6: Commit formatting fixes if any**

```bash
git add -u && git commit -m "style(github-project-tools): formatting fixes"
```
