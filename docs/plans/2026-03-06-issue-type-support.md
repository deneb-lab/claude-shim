# Issue Type Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `--issue-type` flag to `issue-create` so issues can be created with a GitHub issue type (Epic, Task, Bug, etc.), driven by config in `.claude-shim.json`.

**Architecture:** Config-driven, two-step create-then-update. Issue types are stored in `.claude-shim.json` under `fields.issue-types` (list of `{name, id, default}`). The CLI resolves type names from config, creates the issue with `gh issue create`, then sets the type via `updateIssue` GraphQL mutation. Two new subcommands (`list-issue-types`, `set-issue-type`) support discovery and standalone usage.

**Tech Stack:** Python 3, Pydantic v2, pytest, `gh` CLI (GraphQL API)

---

### Task 1: Add IssueType Config Model

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/config.py:12-56`
- Test: `plugins/github-project-tools/hook/tests/test_config.py`

**Step 1: Write the failing tests**

Add to `tests/test_config.py`. Import `IssueType` alongside existing imports on line 6:

```python
from github_project_tools.config import IssueType, StatusField, StatusMapping, load_config
```

Add these test classes at the end of the file:

```python
class TestIssueTypeConfig:
    def test_config_with_issue_types(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                    "issue-types": [
                        {"name": "Epic", "id": "IT_epic", "default": True},
                        {"name": "Task", "id": "IT_task"},
                        {"name": "Bug", "id": "IT_bug"},
                    ],
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.fields.issue_types is not None
        assert len(result.fields.issue_types) == 3
        assert result.fields.issue_types[0].name == "Epic"
        assert result.fields.issue_types[0].id == "IT_epic"
        assert result.fields.issue_types[0].default is True
        assert result.fields.issue_types[1].name == "Task"
        assert result.fields.issue_types[1].default is False

    def test_config_without_issue_types_is_none(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.fields.issue_types is None

    def test_issue_types_list_without_default_raises(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                    "issue-types": [
                        {"name": "Epic", "id": "IT_epic"},
                        {"name": "Task", "id": "IT_task"},
                    ],
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_issue_types_list_with_multiple_defaults_raises(
        self, tmp_path: Path
    ) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                    "issue-types": [
                        {"name": "Epic", "id": "IT_epic", "default": True},
                        {"name": "Task", "id": "IT_task", "default": True},
                    ],
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_issue_types_single_item_with_default(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                    "issue-types": [
                        {"name": "Task", "id": "IT_task", "default": True},
                    ],
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.fields.issue_types is not None
        assert len(result.fields.issue_types) == 1
        assert result.fields.issue_types[0].default is True
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py::TestIssueTypeConfig -v`
Expected: FAIL — `ImportError` (IssueType not defined) or `ValidationError` (issue-types field unknown)

**Step 3: Write minimal implementation**

In `config.py`, add the `IssueType` model after `StatusMapping` (after line 16), and update `ProjectFields`:

```python
class IssueType(BaseModel):
    name: str
    id: str
    default: bool = False


class ProjectFields(BaseModel):
    start_date: str = Field(alias="start-date")
    end_date: str = Field(alias="end-date")
    status: StatusField
    issue_types: list[IssueType] | None = Field(None, alias="issue-types")

    @model_validator(mode="after")
    def _check_issue_type_defaults(self) -> ProjectFields:
        if self.issue_types is not None and len(self.issue_types) > 0:
            defaults = [t for t in self.issue_types if t.default]
            if len(defaults) != 1:
                msg = (
                    f"issue-types must have exactly one default, "
                    f"found {len(defaults)}"
                )
                raise ValueError(msg)
        return self
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py -v`
Expected: ALL PASS (new tests + all existing tests)

**Step 5: Run full test suite**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: ALL PASS

**Step 6: Run linters**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: PASS

**Step 7: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/config.py plugins/github-project-tools/hook/tests/test_config.py
git commit -m "feat(github-project-tools): add IssueType config model with default validation"
```

---

### Task 2: Add `list-issue-types` Subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:594` (repo-only section) and `cli.py:775` (dispatch)
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add to `tests/test_cli.py` (after the existing `TestSetParent` class around line 875):

```python
class TestListIssueTypes:
    def test_returns_issue_types(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='[{"id":"IT_1","name":"Epic","description":""},{"id":"IT_2","name":"Task","description":""}]\n',
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "list-issue-types"]
            )
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert len(output) == 2
        assert output[0]["name"] == "Epic"

    def test_passes_owner_and_name_as_variables(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["--repo", "myowner/myrepo", "list-issue-types"])
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        assert "owner=myowner" in call_str
        assert "name=myrepo" in call_str

    def test_propagates_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="GraphQL error"
            )
            exit_code = main(
                ["--repo", "owner/repo", "list-issue-types"]
            )
        assert exit_code == 1
        assert "list-issue-types" in capsys.readouterr().err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestListIssueTypes -v`
Expected: FAIL — `Unknown subcommand: list-issue-types`

**Step 3: Write minimal implementation**

Add the command function in `cli.py` in the repo-only section (before `cmd_get_parent`, around line 594):

```python
def cmd_list_issue_types(repo: str) -> int:
    owner, name = repo.split("/", 1)
    result = graphql(
        """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            issueTypes(first: 50) { nodes { id name description } }
          }
        }""",
        {"owner": owner, "name": name},
        jq_filter="[.data.repository.issueTypes.nodes[] | {id, name, description}]",
    )
    if (rc := check_result(result, "list-issue-types")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

Add to `issue_cmds` set in `main()` (line 716):

```python
    issue_cmds = {
        "issue-view",
        "issue-view-full",
        "issue-create",
        "issue-close",
        "issue-assign",
        "issue-get-assignees",
        "issue-list",
        "list-issue-types",
    }
```

Add dispatch after `issue-list` (around line 741):

```python
        if subcmd == "list-issue-types":
            return cmd_list_issue_types(resolved_repo)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestListIssueTypes -v`
Expected: ALL PASS

**Step 5: Run full test suite + linters**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add list-issue-types subcommand"
```

---

### Task 3: Add `set-issue-type` Subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py` (repo-only section + dispatch)
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add to `tests/test_cli.py`:

```python
class TestSetIssueType:
    def test_sets_issue_type(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="Epic\n", stderr=""
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-issue-type", "I_issue123", "IT_epic"]
            )
        assert exit_code == 0
        assert capsys.readouterr().out.strip() == "Epic"

    def test_passes_correct_variables(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="Task\n", stderr=""
            )
            main(
                ["--repo", "owner/repo", "set-issue-type", "I_issue123", "IT_task"]
            )
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        assert "id=I_issue123" in call_str
        assert "typeId=IT_task" in call_str

    def test_propagates_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="mutation failed"
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-issue-type", "I_issue123", "IT_bad"]
            )
        assert exit_code == 1
        assert "set-issue-type" in capsys.readouterr().err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetIssueType -v`
Expected: FAIL — `Unknown subcommand: set-issue-type`

**Step 3: Write minimal implementation**

Add the command function in `cli.py` in the repo-only section (after `cmd_list_issue_types`):

```python
def cmd_set_issue_type(node_id: str, type_id: str) -> int:
    result = graphql(
        """
        mutation($id: ID!, $typeId: ID!) {
          updateIssue(input: { id: $id, issueTypeId: $typeId }) {
            issue { issueType { id name } }
          }
        }""",
        {"id": node_id, "typeId": type_id},
        jq_filter=".data.updateIssue.issue.issueType.name",
    )
    if (rc := check_result(result, "set-issue-type")) is not None:
        return rc
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

Add to `repo_only_cmds` set in `main()`:

```python
    repo_only_cmds = {
        "get-parent",
        "count-open-sub-issues",
        "list-sub-issues",
        "set-parent",
        "set-issue-type",
    }
```

Add dispatch:

```python
        if subcmd == "set-issue-type":
            return cmd_set_issue_type(sub_args[0], sub_args[1])
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetIssueType -v`
Expected: ALL PASS

**Step 5: Run full test suite + linters**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add set-issue-type subcommand"
```

---

### Task 4: Add `--issue-type` Flag to `issue-create`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:251-278` (cmd_issue_create) and `cli.py:732` (dispatch)
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add a helper function that creates config with issue types. Add near the top of `test_cli.py`, after the existing `make_config` function (line 32):

```python
def make_config_with_issue_types(tmp_path: Path) -> dict[str, object]:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {
                        "name": "In Progress",
                        "option-id": "PVTO_2",
                    },
                    "done": {"name": "Done", "option-id": "PVTO_3"},
                },
                "issue-types": [
                    {"name": "Epic", "id": "IT_epic", "default": True},
                    {"name": "Task", "id": "IT_task"},
                    {"name": "Bug", "id": "IT_bug"},
                ],
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))
    return config_data
```

Add these tests to the existing `TestIssueCreate` class:

```python
    def test_create_with_issue_type(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)
        call_count = 0

        def mock_side_effect(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # gh issue create
                return subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout="https://github.com/owner/repo/issues/42\n", stderr=""
                )
            if call_count == 2:
                # gh issue view (get node ID)
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="I_node42\n", stderr=""
                )
            # graphql mutation (set type)
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

        with patch("github_project_tools.cli.run_gh", side_effect=mock_side_effect):
            exit_code = main(
                [
                    "--repo", "owner/repo",
                    "issue-create",
                    "--title", "My Title",
                    "--body", "My Body",
                    "--issue-type", "Epic",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "https://github.com/owner/repo/issues/42" in out

    def test_create_with_issue_type_case_insensitive(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)

        def mock_side_effect(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="https://github.com/owner/repo/issues/42\n", stderr=""
            )

        with patch("github_project_tools.cli.run_gh", side_effect=mock_side_effect):
            exit_code = main(
                [
                    "--repo", "owner/repo",
                    "issue-create",
                    "--title", "T",
                    "--body", "B",
                    "--issue-type", "epic",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0

    def test_create_with_issue_type_calls_update_mutation(
        self, tmp_path: Path
    ) -> None:
        make_config_with_issue_types(tmp_path)
        calls: list[list[str]] = []

        def mock_side_effect(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            if len(calls) == 1:
                return subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout="https://github.com/owner/repo/issues/42\n", stderr=""
                )
            if len(calls) == 2:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="I_node42\n", stderr=""
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

        with patch("github_project_tools.cli.run_gh", side_effect=mock_side_effect):
            main(
                [
                    "--repo", "owner/repo",
                    "issue-create",
                    "--title", "T",
                    "--body", "B",
                    "--issue-type", "Task",
                ],
                cwd=tmp_path,
            )
        # Third call should be the GraphQL mutation
        assert len(calls) == 3
        mutation_args = " ".join(calls[2])
        assert "id=I_node42" in mutation_args
        assert "typeId=IT_task" in mutation_args

    def test_create_with_unknown_issue_type_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                [
                    "--repo", "owner/repo",
                    "issue-create",
                    "--title", "T",
                    "--body", "B",
                    "--issue-type", "NonExistent",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "unknown issue type" in err.lower()

    def test_create_with_issue_type_no_config_fails(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                [
                    "--repo", "owner/repo",
                    "issue-create",
                    "--title", "T",
                    "--body", "B",
                    "--issue-type", "Epic",
                ]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-type" in err.lower()

    def test_create_without_issue_type_still_works(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Backward compat: no --issue-type means no config needed, no extra calls."""
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="https://github.com/owner/repo/issues/99\n", stderr=""
            )
            exit_code = main(
                [
                    "--repo", "owner/repo",
                    "issue-create",
                    "--title", "T",
                    "--body", "B",
                ]
            )
        assert exit_code == 0
        # Only one call (gh issue create), no node ID or mutation calls
        assert mock_run.call_count == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate::test_create_with_issue_type -v`
Expected: FAIL — `issue-create: unknown arg: --issue-type`

**Step 3: Write minimal implementation**

Replace `cmd_issue_create` in `cli.py` (lines 251-278):

```python
def cmd_issue_create(
    repo: str, args: list[str], config: GitHubProjectToolsConfig | None = None
) -> int:
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
            print(f"issue-create: unknown arg: {args[i]}", file=sys.stderr)
            return 1
    if not title:
        print("issue-create: --title required", file=sys.stderr)
        return 1
    if not body:
        print("issue-create: --body required", file=sys.stderr)
        return 1

    # Resolve issue type ID from config
    type_id = ""
    if issue_type:
        if config is None or config.fields.issue_types is None:
            print(
                "issue-create: --issue-type requires issue-types in config",
                file=sys.stderr,
            )
            return 1
        for t in config.fields.issue_types:
            if t.name.lower() == issue_type.lower():
                type_id = t.id
                break
        if not type_id:
            names = ", ".join(t.name for t in config.fields.issue_types)
            print(
                f"issue-create: unknown issue type '{issue_type}' (available: {names})",
                file=sys.stderr,
            )
            return 1

    result = run_gh(
        ["issue", "create", "--repo", repo, "--title", title, "--body", body]
    )
    if (rc := check_result(result, "issue-create")) is not None:
        return rc
    url = result.stdout.strip() if result.stdout else ""
    if result.stdout:
        print(result.stdout, end="")

    # Set issue type if requested
    if type_id and url:
        number = url.rstrip("/").split("/")[-1]
        node_result = run_gh(
            ["issue", "view", number, "--repo", repo, "--json", "id", "--jq", ".id"]
        )
        if (rc := check_result(node_result, "issue-create (get node ID)")) is not None:
            return rc
        node_id = node_result.stdout.strip()
        type_result = graphql(
            """
            mutation($id: ID!, $typeId: ID!) {
              updateIssue(input: { id: $id, issueTypeId: $typeId }) {
                issue { issueType { id name } }
              }
            }""",
            {"id": node_id, "typeId": type_id},
        )
        if (rc := check_result(type_result, "issue-create (set type)")) is not None:
            return rc

    return 0
```

Update the dispatch in `main()`. Change the `issue-create` case (around line 732) to load config optionally:

```python
        if subcmd == "issue-create":
            config = load_config(working_dir)
            return cmd_issue_create(resolved_repo, sub_args, config=config)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueCreate -v`
Expected: ALL PASS

**Step 5: Run full test suite + linters**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add --issue-type flag to issue-create"
```

---

### Task 5: Update `read-config` Output to Include Issue Types

**Files:**
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing test**

Add to `TestReadConfig` in `test_cli.py`:

```python
    def test_outputs_issue_types_when_present(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert "issue-types" in output["fields"]
        types = output["fields"]["issue-types"]
        assert len(types) == 3
        assert types[0]["name"] == "Epic"
        assert types[0]["default"] is True

    def test_outputs_null_issue_types_when_absent(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["fields"]["issue-types"] is None
```

**Step 2: Run tests to verify they pass**

These tests should pass immediately since `model_dump_json(by_alias=True)` includes the new field. This is a verification step, not a TDD step.

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestReadConfig -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "test(github-project-tools): add read-config tests for issue-types serialization"
```

---

### Task 6: Update Setup Skill

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md`

**Step 1: Read current skill**

Read `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md` to confirm the current content matches what was read during planning.

**Step 2: Add issue type discovery step**

Insert a new **Step 5.5: Detect Issue Types** between the current Step 5 (Detect Status Mappings) and Step 6 (Write Config). This step:

1. Queries available issue types:
   ```bash
   <cli> list-issue-types
   ```
2. If the command returns an empty array `[]`, tell the user: "No issue types available for this repository. Skipping issue type configuration." Proceed to Step 6.
3. If issue types are returned, present them to the user with AskUserQuestion using `multiSelect: true`: "Which issue types should be available in the config?"
4. If user selects one or more types, ask which should be the default (single-select).
5. Save the selections as `ISSUE_TYPES` list for Step 6.

Update Step 6 (Write Config) to include `issue-types` in the `fields` object when `ISSUE_TYPES` is non-empty:

```json
"issue-types": [
  {"name": "<name>", "id": "<id>", "default": true},
  {"name": "<name2>", "id": "<id2>"}
]
```

**Step 3: Verify the allowed-tools pattern**

The setup skill already has `Bash(*/github-project-tools/scripts/github-project-tools.sh *)` which covers all subcommands including `list-issue-types`. No change needed to allowed-tools.

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): add issue type discovery to setup skill"
```

---

### Task 7: Update Add-Issue Skill

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md`

**Step 1: Read current skill**

Read `plugins/github-project-tools/skills/add-issue/SKILL.md` to confirm the current content.

**Step 2: Update Phase 2 (Gather Context)**

Add to the list of things to extract from conversation context:

```
- **Issue type (optional):** If the user specified an issue type (e.g., "Epic", "Bug", "Task"). If not specified and config has `issue-types` configured, use the default type from config.
```

**Step 3: Update Phase 3 (Create Issue)**

Update step 1 to conditionally include `--issue-type`:

```
1. Create the issue:

   **If issue types are configured** (the `read-config` output contains a non-null `issue-types` field):
   ```bash
   <cli> issue-create --title "<title>" --body "<body>" --issue-type "<type-name>"
   ```
   Use the user-specified type, or the default type from config (the entry with `"default": true`).

   **If issue types are not configured:**
   ```bash
   <cli> issue-create --title "<title>" --body "<body>"
   ```

   The output is the issue URL. Extract the issue number from the URL path.
```

**Step 4: Verify allowed-tools**

The existing pattern `Bash(*/github-project-tools/scripts/github-project-tools.sh issue-create *)` already covers `issue-create --title ... --body ... --issue-type ...` since `*` is a glob wildcard. No change needed.

**Step 5: Commit**

```bash
git add plugins/github-project-tools/skills/add-issue/SKILL.md
git commit -m "feat(github-project-tools): add issue type passthrough to add-issue skill"
```

---

### Task 8: Final Verification

**Step 1: Run full test suite**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: ALL PASS

**Step 2: Run all linters**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: ALL PASS

**Step 3: Run CI checks**

Run: `shellcheck plugins/github-project-tools/scripts/*.sh`
Expected: PASS

**Step 4: Verify shared prompt sync**

The shared prompts (`preflight.md`, `conventions.md`, `setup.md`, `parse-issue-arg.md`) are NOT modified in this feature. Verify with:

```bash
git diff --name-only main -- '**/prompts/*.md'
```

Expected: empty (no shared prompt changes)

**Step 5: Review all changes**

```bash
git log --oneline main..HEAD
git diff main --stat
```

Verify the change set matches the plan: config model, 2 new subcommands, enhanced issue-create, updated setup skill, updated add-issue skill.
