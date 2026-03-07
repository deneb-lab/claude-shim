# CLI Error Message Usage Hints — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add usage hints to error messages in 4 CLI subcommands so Claude can self-correct when using them outside their primary skill.

**Architecture:** Each command's error messages (unknown arg, missing required arg) get a `. Usage: <correct syntax>` suffix appended. No new features — just better error output.

**Tech Stack:** Python (cli.py), pytest (test_cli.py)

---

### Task 1: issue-create — add usage hint tests

**Files:**
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py` (TestIssueCreate class, after line 372)

**Step 1: Write the failing tests**

Add these tests inside the `TestIssueCreate` class, after the existing `test_create_missing_body_exits_1` test:

```python
    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                ["--repo", "owner/repo", "issue-create", "Some title", "--body", "B"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-create --title" in err

    def test_missing_title_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--body", "B"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-create --title" in err

    def test_missing_body_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--title", "T"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-create --title" in err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate::test_unknown_arg_shows_usage_hint tests/test_cli.py::TestIssueCreate::test_missing_title_shows_usage_hint tests/test_cli.py::TestIssueCreate::test_missing_body_shows_usage_hint -v`
Expected: 3 FAILED — the current error messages don't contain "Usage:"

**Step 3: Implement the fix**

In `plugins/github-project-tools/hook/src/github_project_tools/cli.py`, modify `cmd_issue_create` (lines 251-273).

Add a usage string constant near the top of the function, then reference it in all error messages:

```python
def cmd_issue_create(
    repo: str, args: list[str], config: GitHubProjectToolsConfig | None = None
) -> int:
    usage = 'Usage: issue-create --title "..." --body "..." [--issue-type "..."]'
    title = ""
    body = ""
    issue_type = ""
    i = 0
    while i < len(args):
        if args[i] == "--title":
            title = args[i + 1]
            i += 2
        elif args[i] == "--body":
            body = args[i + 1]
            i += 2
        elif args[i] == "--issue-type":
            issue_type = args[i + 1]
            i += 2
        else:
            print(f"issue-create: unknown arg: {args[i]}. {usage}", file=sys.stderr)
            return 1
    if not title:
        print(f"issue-create: --title required. {usage}", file=sys.stderr)
        return 1
    if not body:
        print(f"issue-create: --body required. {usage}", file=sys.stderr)
        return 1
```

Leave the rest of the function unchanged.

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate -v`
Expected: ALL PASS (including existing tests — they assert on "unknown arg" and "title"/"body" which are still present)

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add usage hints to issue-create error messages"
```

---

### Task 2: issue-close — add usage hint tests

**Files:**
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py` (TestIssueClose class, after line 666)
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py` (cmd_issue_close, line 339)

**Step 1: Write the failing test**

Add this test inside the `TestIssueClose` class:

```python
    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                ["--repo", "owner/repo", "issue-close", "42", "--label", "bug"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-close <number> [--comment" in err
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueClose::test_unknown_arg_shows_usage_hint -v`
Expected: FAIL

**Step 3: Implement the fix**

In `cli.py`, modify `cmd_issue_close` (line 332):

```python
def cmd_issue_close(repo: str, number: str, args: list[str]) -> int:
    usage = 'Usage: issue-close <number> [--comment "..."]'
    comment = ""
    i = 0
    while i < len(args):
        if args[i] == "--comment":
            comment = args[i + 1]
            i += 2
        else:
            print(f"issue-close: unknown arg: {args[i]}. {usage}", file=sys.stderr)
            return 1
```

Leave the rest unchanged.

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueClose -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add usage hints to issue-close error messages"
```

---

### Task 3: project-list — add usage hint tests

**Files:**
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py` (TestProjectList class, after line 1177)
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py` (cmd_project_list, line 161)

**Step 1: Write the failing tests**

Add these tests inside the `TestProjectList` class:

```python
    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-list", "unexpected"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-list --owner <owner>" in err

    def test_missing_owner_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-list"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-list --owner <owner>" in err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestProjectList::test_unknown_arg_shows_usage_hint tests/test_cli.py::TestProjectList::test_missing_owner_shows_usage_hint -v`
Expected: FAIL

**Step 3: Implement the fix**

In `cli.py`, modify `cmd_project_list` (line 161):

```python
def cmd_project_list(args: list[str]) -> int:
    usage = "Usage: project-list --owner <owner>"
    owner = ""
    i = 0
    while i < len(args):
        if args[i] == "--owner":
            if i + 1 >= len(args):
                print("project-list: --owner requires an argument", file=sys.stderr)
                return 1
            owner = args[i + 1]
            i += 2
        else:
            print(f"project-list: unknown arg: {args[i]}. {usage}", file=sys.stderr)
            return 1
    if not owner:
        print(f"project-list: --owner required. {usage}", file=sys.stderr)
        return 1
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestProjectList -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add usage hints to project-list error messages"
```

---

### Task 4: project-field-list — add usage hint tests

**Files:**
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py` (TestProjectFieldList class, after line 1211)
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py` (cmd_project_field_list, line 185)

**Step 1: Write the failing tests**

Add these tests inside the `TestProjectFieldList` class:

```python
    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-field-list", "--owner", "elahti", "--bad"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-field-list <number> --owner <owner>" in err

    def test_missing_owner_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-field-list", "1"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-field-list <number> --owner <owner>" in err

    def test_missing_number_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-field-list", "--owner", "elahti"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-field-list <number> --owner <owner>" in err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestProjectFieldList::test_unknown_arg_shows_usage_hint tests/test_cli.py::TestProjectFieldList::test_missing_owner_shows_usage_hint tests/test_cli.py::TestProjectFieldList::test_missing_number_shows_usage_hint -v`
Expected: FAIL

**Step 3: Implement the fix**

In `cli.py`, modify `cmd_project_field_list` (line 185):

```python
def cmd_project_field_list(args: list[str]) -> int:
    usage = "Usage: project-field-list <number> --owner <owner>"
    owner = ""
    number = ""
    i = 0
    while i < len(args):
        if args[i] == "--owner":
            if i + 1 >= len(args):
                print(
                    "project-field-list: --owner requires an argument", file=sys.stderr
                )
                return 1
            owner = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            number = args[i]
            i += 1
        else:
            print(f"project-field-list: unknown arg: {args[i]}. {usage}", file=sys.stderr)
            return 1
    if not owner:
        print(f"project-field-list: --owner required. {usage}", file=sys.stderr)
        return 1
    if not number:
        print(f"project-field-list: project number required. {usage}", file=sys.stderr)
        return 1
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestProjectFieldList -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add usage hints to project-field-list error messages"
```

---

### Task 5: Full test suite + lint verification

**Step 1: Run full test suite**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: ALL PASS

**Step 2: Run linter and type checker**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: No errors

**Step 3: Fix any issues**

If lint or format issues are found, fix them and re-run.

**Step 4: Commit any fixes**

Only if fixes were needed in step 3.
