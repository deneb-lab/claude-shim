# Configurable GitHub Project Skills — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace runtime auto-detection in github-project-tools with `.claude-shim.json` config, rewrite the shell script as a Python uv package, and add a setup skill.

**Architecture:** A uv-managed Python package (`hook/`) replaces `scripts/github-projects.sh`. Pydantic models validate the `github-project-tools` section of `.claude-shim.json` at runtime. A new `setup-github-project-tools` SKILL.md prompt handles interactive project detection and config writing. Existing skills are updated to read config instead of auto-detecting.

**Tech Stack:** Python 3.12+, pydantic, uv, pytest, ruff, pyright

**Design doc:** `docs/plans/2026-02-28-configurable-github-project-skills-design.md`

---

### Task 1: Create the uv project skeleton

**Files:**
- Create: `plugins/github-project-tools/hook/pyproject.toml`
- Create: `plugins/github-project-tools/hook/src/github_project_tools/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "github-project-tools"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic==2.12.5",
]

[build-system]
build-backend = "uv_build"
requires = ["uv_build"]

[dependency-groups]
dev = [
    "pyright==1.1.408",
    "pytest==9.0.2",
    "ruff==0.15.1",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "COM",  # flake8-commas
    "E",    # pycodestyle errors
    "F",    # Pyflakes
    "I",    # isort
    "PERF", # perflint
    "RUF",  # Ruff-specific
    "SIM",  # flake8-simplify
    "UP",   # pyupgrade
    "W",    # pycodestyle warnings
]
ignore = ["COM812", "E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingParameterType = "error"
reportUnknownArgumentType = "error"
reportUnknownMemberType = "error"
reportUnknownParameterType = "error"
reportUnknownVariableType = "error"
reportUnusedImport = "error"
reportUnusedVariable = "error"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Write to: `plugins/github-project-tools/hook/pyproject.toml`

**Step 2: Create empty `__init__.py`**

Write empty file to: `plugins/github-project-tools/hook/src/github_project_tools/__init__.py`

**Step 3: Create empty test `__init__.py`**

Write empty file to: `plugins/github-project-tools/hook/tests/__init__.py`

**Step 4: Lock dependencies**

Run: `cd plugins/github-project-tools/hook && uv lock`
Expected: `uv.lock` file created

**Step 5: Verify the project builds**

Run: `uv run --project plugins/github-project-tools/hook python -c "print('ok')"`
Expected: `ok`

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): scaffold uv Python package"
```

---

### Task 2: Implement pydantic config models with tests

**Files:**
- Create: `plugins/github-project-tools/hook/src/github_project_tools/config.py`
- Create: `plugins/github-project-tools/hook/tests/test_config.py`

**Step 1: Write the config tests**

Write to: `plugins/github-project-tools/hook/tests/test_config.py`

```python
import json
from pathlib import Path

import pytest

from github_project_tools.config import load_config


class TestGitHubProjectToolsConfig:
    def test_valid_config(self, tmp_path: Path) -> None:
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
        assert result.project == "https://github.com/users/testowner/projects/1"
        assert result.fields.start_date == "PVTF_start"
        assert result.fields.end_date == "PVTF_end"
        assert result.fields.status.id == "PVTF_status"
        assert result.fields.status.todo.name == "Todo"
        assert result.fields.status.todo.option_id == "PVTO_1"
        assert result.fields.status.in_progress.name == "In Progress"
        assert result.fields.status.in_progress.option_id == "PVTO_2"
        assert result.fields.status.done.name == "Done"
        assert result.fields.status.done.option_id == "PVTO_3"

    def test_no_config_file_returns_none(self, tmp_path: Path) -> None:
        result = load_config(tmp_path)
        assert result is None

    def test_no_github_project_tools_key_returns_none(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps({"quality-checks": {"include": []}}))

        result = load_config(tmp_path)
        assert result is None

    def test_invalid_config_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(
            json.dumps({"github-project-tools": {"project": 123}})
        )

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_missing_status_role_raises(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        # missing in-progress and done
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_extra_keys_ignored(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {"include": []},
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
            },
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)
        assert result is not None
        assert result.project == "https://github.com/users/testowner/projects/1"
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project plugins/github-project-tools/hook pytest -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'github_project_tools.config'`

**Step 3: Write the config module**

Write to: `plugins/github-project-tools/hook/src/github_project_tools/config.py`

```python
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

CONFIG_FILENAME = ".claude-shim.json"
CONFIG_KEY = "github-project-tools"


class StatusMapping(BaseModel):
    name: str
    option_id: str = Field(alias="option-id")


class StatusField(BaseModel):
    id: str
    todo: StatusMapping
    in_progress: StatusMapping = Field(alias="in-progress")
    done: StatusMapping


class ProjectFields(BaseModel):
    start_date: str = Field(alias="start-date")
    end_date: str = Field(alias="end-date")
    status: StatusField


class GitHubProjectToolsConfig(BaseModel):
    project: str
    fields: ProjectFields


def load_config(cwd: Path) -> GitHubProjectToolsConfig | None:
    config_path = cwd / CONFIG_FILENAME
    if not config_path.exists():
        return None

    raw = json.loads(config_path.read_text())

    if CONFIG_KEY not in raw:
        return None

    try:
        return GitHubProjectToolsConfig.model_validate(raw[CONFIG_KEY])
    except ValidationError as exc:
        msg = f"Invalid {CONFIG_FILENAME}: {exc}"
        raise ValueError(msg) from exc
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project plugins/github-project-tools/hook pytest -v`
Expected: All 6 tests PASS

**Step 5: Run lint and typecheck**

Run: `uv run --project plugins/github-project-tools/hook ruff check && uv run --project plugins/github-project-tools/hook ruff format --check && uv run --project plugins/github-project-tools/hook pyright`
Expected: All pass

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/config.py plugins/github-project-tools/hook/tests/test_config.py
git commit -m "feat(github-project-tools): add pydantic config models with tests"
```

---

### Task 3: Implement the CLI module — config and preflight subcommands

**Files:**
- Create: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- Create: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write tests for read-config and preflight**

Write to: `plugins/github-project-tools/hook/tests/test_cli.py`

```python
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from github_project_tools.cli import main


def make_config(tmp_path: Path) -> dict[str, object]:
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
    return config_data


class TestReadConfig:
    def test_outputs_config_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        make_config(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["project"] == "https://github.com/users/testowner/projects/1"

    def test_missing_config_exits_1(self, tmp_path: Path) -> None:
        exit_code = main(["read-config"], cwd=tmp_path)
        assert exit_code == 1


class TestPreflight:
    def test_preflight_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["gh", "auth", "status"],
                returncode=0,
                stdout="",
                stderr="✓ Logged in\n  Token scopes: repo, project",
            )
            exit_code = main(["preflight"])

        assert exit_code == 0
        assert "OK" in capsys.readouterr().out
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project plugins/github-project-tools/hook pytest tests/test_cli.py -v`
Expected: FAIL — `cannot import name 'main' from 'github_project_tools.cli'`

**Step 3: Write the CLI module (read-config and preflight)**

Write to: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from github_project_tools.config import load_config


def run_gh(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
        **kwargs,  # type: ignore[arg-type]
    )


def cmd_preflight() -> int:
    result = run_gh(["auth", "status"])
    output = result.stdout + result.stderr
    if result.returncode != 0:
        print("FAIL: gh not authenticated. Run 'gh auth login'", file=sys.stderr)
        return 1
    if "repo" not in output:
        print(
            "FAIL: 'repo' scope not granted. Run 'gh auth refresh -s repo'",
            file=sys.stderr,
        )
        return 1
    if "project" not in output:
        print(
            "FAIL: 'project' scope not granted. Run 'gh auth refresh -s project'",
            file=sys.stderr,
        )
        return 1
    print("OK: gh CLI authenticated with repo + project scopes")
    return 0


def cmd_read_config(cwd: Path) -> int:
    config = load_config(cwd)
    if config is None:
        print("No github-project-tools config found", file=sys.stderr)
        return 1
    print(config.model_dump_json(by_alias=True))
    return 0


def main(argv: list[str] | None = None, cwd: Path | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    working_dir = cwd if cwd is not None else Path.cwd()

    if not args:
        print("Usage: github-project-tools <subcommand> [args...]", file=sys.stderr)
        return 1

    # Parse global options
    repo: str | None = None
    while args and args[0].startswith("--"):
        if args[0] == "--repo":
            if len(args) < 2:
                print("--repo requires owner/repo argument", file=sys.stderr)
                return 1
            repo = args[1]
            args = args[2:]
        else:
            break

    subcmd = args[0]
    sub_args = args[1:]

    if subcmd == "preflight":
        return cmd_preflight()
    if subcmd == "read-config":
        return cmd_read_config(working_dir)

    # Subcommands that need repo detection will be added in Task 4
    _ = repo, sub_args
    print(f"Unknown subcommand: {subcmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run tests to verify they pass**

Run: `uv run --project plugins/github-project-tools/hook pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Run lint and typecheck**

Run: `uv run --project plugins/github-project-tools/hook ruff check && uv run --project plugins/github-project-tools/hook ruff format --check && uv run --project plugins/github-project-tools/hook pyright`
Expected: All pass

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add CLI module with read-config and preflight"
```

---

### Task 4: Implement CLI — repo detection and issue subcommands

Port the issue-related subcommands from `github-projects.sh` to `cli.py`. These call `gh` CLI and need repo detection (auto-detect via git remote or `--repo` override).

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write tests for repo detection and issue subcommands**

Add to `tests/test_cli.py`:

```python
class TestRepoDetection:
    def test_auto_detect_repo(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            # detect_repo call
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout='{"nameWithOwner":"owner/repo"}', stderr="",
                ),
                # issue-view-full call
                subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout='{"id":"I_1","number":1,"title":"Test","body":"","state":"OPEN"}',
                    stderr="",
                ),
            ]
            exit_code = main(["issue-view-full", "1"])

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["title"] == "Test"

    def test_repo_override_skips_detection(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='{"id":"I_1","number":1,"title":"Test","body":"","state":"OPEN"}',
                stderr="",
            )
            exit_code = main(["--repo", "other/repo", "issue-view-full", "1"])

        assert exit_code == 0
        # Verify --repo was passed to gh
        call_args = mock_run.call_args[0][0]
        assert "--repo" in call_args
        assert "other/repo" in call_args


class TestIssueAssign:
    def test_assigns_to_me(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "issue-assign", "42"])

        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "edit" in call_args
        assert "--add-assignee" in call_args
        assert "@me" in call_args
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project plugins/github-project-tools/hook pytest tests/test_cli.py -v -k "TestRepo or TestIssue"`
Expected: FAIL

**Step 3: Implement repo detection and issue subcommands in `cli.py`**

Add these functions and update the `main()` dispatch:

- `detect_repo(repo_override)` — returns repo from override or `gh repo view`
- `cmd_issue_view_full(repo, number)` — `gh issue view <n> --repo <r> --json id,number,title,body,state`
- `cmd_issue_view(repo, number, extra_args)` — passthrough to `gh issue view`
- `cmd_issue_create(repo, args)` — parse `--title`, `--body`, `--body-file`, `--label`
- `cmd_issue_edit(repo, number, args)` — parse `--body`, `--body-file`
- `cmd_issue_close(repo, number, args)` — parse `--comment`, `--comment-file`, check state first
- `cmd_issue_assign(repo, number)` — `gh issue edit <n> --repo <r> --add-assignee @me`

Model these closely on the shell script's implementations. Each function calls `run_gh()` and prints the stdout.

**Step 4: Run tests to verify they pass**

Run: `uv run --project plugins/github-project-tools/hook pytest -v`
Expected: All tests PASS

**Step 5: Run lint and typecheck**

Run: `uv run --project plugins/github-project-tools/hook ruff check && uv run --project plugins/github-project-tools/hook ruff format --check && uv run --project plugins/github-project-tools/hook pyright`
Expected: All pass

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): add repo detection and issue subcommands"
```

---

### Task 5: Implement CLI — project subcommands (config-driven)

Port GraphQL queries and mutations that interact with the project board. These now read project ID, field IDs, and status mappings from config instead of auto-detecting.

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write tests for project subcommands**

Add to `tests/test_cli.py`:

```python
class TestSetStatus:
    def test_uses_config_option_id(self, tmp_path: Path) -> None:
        make_config(tmp_path)

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='{"data":{"updateProjectV2ItemFieldValue":{"projectV2Item":{"id":"PVTI_1"}}}}',
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
                cwd=tmp_path,
            )

        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        # Verify the GraphQL call includes the option-id from config
        call_str = " ".join(call_args)
        assert "PVTO_3" in call_str  # done option-id from make_config

    def test_unknown_status_fails(self, tmp_path: Path) -> None:
        make_config(tmp_path)

        exit_code = main(
            ["--repo", "owner/repo", "set-status", "PVTI_item", "invalid"],
            cwd=tmp_path,
        )

        assert exit_code == 1


class TestSetDate:
    def test_sets_date_to_today(self, tmp_path: Path) -> None:
        make_config(tmp_path)

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='{"data":{}}',
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )

        assert exit_code == 0


class TestGetProjectItem:
    def test_returns_item_id(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        make_config(tmp_path)

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="PVTI_item123\n",
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "get-project-item", "I_node"],
                cwd=tmp_path,
            )

        assert exit_code == 0


class TestAddToProject:
    def test_returns_item_id(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        make_config(tmp_path)

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="PVTI_new\n",
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "add-to-project", "I_node"],
                cwd=tmp_path,
            )

        assert exit_code == 0
```

**Step 2: Run tests to verify they fail**

Run: `uv run --project plugins/github-project-tools/hook pytest tests/test_cli.py -v -k "TestSet or TestGetProject or TestAddTo"`
Expected: FAIL

**Step 3: Implement project subcommands in `cli.py`**

Add a helper to extract the project ID from the config project URL:

```python
def extract_project_id_from_config(config: GitHubProjectToolsConfig) -> tuple[str, str]:
    """Extract owner and project number from project URL.

    URL format: https://github.com/users/<owner>/projects/<number>
    or: https://github.com/orgs/<owner>/projects/<number>
    """
    ...
```

Add a `graphql(query, **variables)` helper that calls `run_gh(["api", "graphql", "-f", f"query={query}", ...])`.

Port these subcommands, all reading project ID from config:
- `cmd_get_project_item(config, node_id)` — GraphQL query
- `cmd_get_start_date(config, node_id)` — GraphQL query
- `cmd_add_to_project(config, node_id)` — GraphQL mutation
- `cmd_set_status(config, item_id, status_key)` — look up `config.fields.status.<role>.option_id`
- `cmd_set_date(config, item_id, field_id)` — GraphQL mutation with today's date
- `cmd_get_parent(repo, node_id)` — GraphQL query (repo-only, no config needed)
- `cmd_count_open_sub_issues(repo, node_id)` — GraphQL query
- `cmd_set_parent(repo, child_id, parent_id)` — GraphQL mutation
- `cmd_table_set_status(repo, parent_number, sub_number, status)` — reads issue body, updates table

Note: `set-status`, `set-date`, `get-project-item`, `add-to-project` need config. The `main()` function must load config for these subcommands and fail with exit code 1 if missing (prompting the user to run the setup skill).

**Step 4: Run tests to verify they pass**

Run: `uv run --project plugins/github-project-tools/hook pytest -v`
Expected: All tests PASS

**Step 5: Run lint and typecheck**

Run: `uv run --project plugins/github-project-tools/hook ruff check && uv run --project plugins/github-project-tools/hook ruff format --check && uv run --project plugins/github-project-tools/hook pyright`
Expected: All pass

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): add config-driven project subcommands"
```

---

### Task 6: Add `__main__.py` and verify CLI end-to-end

**Files:**
- Create: `plugins/github-project-tools/hook/src/github_project_tools/__main__.py`

**Step 1: Create `__main__.py`**

Write to: `plugins/github-project-tools/hook/src/github_project_tools/__main__.py`

```python
from github_project_tools.cli import main

raise SystemExit(main())
```

**Step 2: Verify the CLI works via `python -m`**

Run: `uv run --project plugins/github-project-tools/hook python -m github_project_tools preflight`
Expected: `OK: gh CLI authenticated with repo + project scopes`

Run: `uv run --project plugins/github-project-tools/hook python -m github_project_tools read-config`
Expected: Exit code 1 (no config in this repo) with stderr message

**Step 3: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/__main__.py
git commit -m "feat(github-project-tools): add __main__.py for python -m invocation"
```

---

### Task 7: Update shared prompts — preflight.md

Update the preflight prompt in all 3 skills to glob for the `hook/` directory instead of the `.sh` script.

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/preflight.md`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/preflight.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/preflight.md`

**Step 1: Write the new preflight.md content**

All three copies get identical content:

```markdown
1. Find the bundled hook project. Use Glob to locate it:
   ```
   ~/.claude/plugins/**/github-project-tools/hook/pyproject.toml
   ```
   Store the **parent directory** of the matched `pyproject.toml` as `HOOK_PATH`. For example, if the match is `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/1.1.0/hook/pyproject.toml`, then `HOOK_PATH` is `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/1.1.0/hook`.

2. All commands for the rest of this skill use this invocation pattern:
   ```bash
   uv run --project <HOOK_PATH> python -m github_project_tools <subcommand> [args...]
   ```
   Referred to as `<cli> <subcommand>` in the rest of this document.

3. Run preflight checks:
   ```bash
   <cli> preflight
   ```
4. If preflight fails, stop and show the error message to the user. Do not proceed.
```

**Step 2: Write the new content to all 3 files**

Update `plugins/github-project-tools/skills/add-issue/prompts/preflight.md`, `plugins/github-project-tools/skills/start-implementation/prompts/preflight.md`, and `plugins/github-project-tools/skills/end-implementation/prompts/preflight.md` with identical content.

**Step 3: Verify shared prompts are in sync**

Run the CI sync check logic manually:
```bash
diff plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/start-implementation/prompts/preflight.md && diff plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/end-implementation/prompts/preflight.md && echo "All in sync"
```
Expected: `All in sync`

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/preflight.md
git commit -m "feat(github-project-tools): update preflight to use Python CLI"
```

---

### Task 8: Update shared prompts — setup.md

Replace the setup prompt to read config and invoke the setup skill if missing.

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/setup.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/setup.md`

**Step 1: Write the new setup.md content**

Both copies get identical content:

```markdown
The script auto-detects the current repository from the git remote. When `REPO_OVERRIDE` is set (see issue-fetching phase), pass `--repo $REPO_OVERRIDE` before the subcommand in every CLI invocation to override auto-detection.

1. Read the project config:
   ```bash
   <cli> read-config
   ```

   - **If the command succeeds** (exit code 0), it outputs JSON. Extract and save:
     - `START_FIELD` from `.fields.start-date`
     - `END_FIELD` from `.fields.end-date`
     - The `set-status` subcommand accepts `todo`, `in-progress`, and `done` directly — no manual mapping needed.
     - Note that **a project is available** — proceed with project operations in later phases.

   - **If the command fails** (exit code 1), no config is available. Tell the user:
     "No github-project-tools configuration found. Running setup."
     Then invoke the `github-project-tools:setup-github-project-tools` skill via the Skill tool.
     After setup completes, re-run `<cli> read-config` and extract the values above.
```

**Step 2: Write to both files**

Update `plugins/github-project-tools/skills/start-implementation/prompts/setup.md` and `plugins/github-project-tools/skills/end-implementation/prompts/setup.md` with identical content.

**Step 3: Verify sync**

```bash
diff plugins/github-project-tools/skills/start-implementation/prompts/setup.md plugins/github-project-tools/skills/end-implementation/prompts/setup.md && echo "In sync"
```
Expected: `In sync`

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/setup.md
git commit -m "feat(github-project-tools): update setup prompt to use config"
```

---

### Task 9: Update shared prompts — conventions.md

Update the invocation pattern example and remove the "date field IDs looked up at runtime" note (they come from config now).

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/conventions.md`

**Step 1: Write the new conventions.md content**

All three copies get identical content:

```markdown
- **CLI invocation:** The `<cli>` prefix (see preflight) MUST be the literal first tokens of every bash command — e.g. `<cli> issue-assign 14`. NEVER split the path into a variable. Claude Code matches permissions by the first token; variable-wrapped paths produce a different fingerprint every time, forcing repeated approval prompts.
- **No command substitution** in bash commands — never use `$(...)`. If logic is needed, add it to the CLI. Use `--body-file` for multi-line content (write to a temp file with the Write tool first).
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `<cli>` — never call `gh` directly.
- **Date field IDs** come from the config (read during setup). They may change if the project is recreated — re-run the setup skill to refresh.
- **Project is optional.** If no config is found during setup and the user declines to configure, skip all project operations (get-project-item, add-to-project, set-date, set-status) but still perform issue operations (assign, view, close, parent check).
```

**Step 2: Write to all 3 files**

Update all three conventions.md files with identical content.

**Step 3: Verify sync**

```bash
diff plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/start-implementation/prompts/conventions.md && diff plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/end-implementation/prompts/conventions.md && echo "All in sync"
```
Expected: `All in sync`

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/conventions.md
git commit -m "feat(github-project-tools): update conventions for Python CLI"
```

---

### Task 10: Update skill SKILL.md files

Update the three existing skills to use `<cli>` instead of `<resolved-path>`, remove `get-project-fields` calls, and update the allowed tools.

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md`
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md`

**Step 1: Update add-issue/SKILL.md**

Changes:
- Replace all `<resolved-path>` references with `<cli>`
- Remove any inline `get-project-fields` calls (covered by setup.md prompt now)
- Add Phase 1: Setup — include `[prompts/setup.md](prompts/setup.md)` reference (add-issue currently doesn't have this; it needs config to know project ID)
- Update allowed tools from `Bash(github-projects.sh:*)` to `Bash(uv:*)`

**Step 2: Update start-implementation/SKILL.md**

Changes:
- Replace all `<resolved-path>` with `<cli>`
- Update allowed tools
- The setup phase already references setup.md, which now handles config

**Step 3: Update end-implementation/SKILL.md**

Changes:
- Replace all `<resolved-path>` with `<cli>`
- Update allowed tools
- The setup phase already references setup.md

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/*/SKILL.md
git commit -m "feat(github-project-tools): update skills for Python CLI"
```

---

### Task 11: Create setup-github-project-tools skill

Create the new setup skill that interactively detects project configuration and writes to `.claude-shim.json`.

**Files:**
- Create: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md`
- Create: `plugins/github-project-tools/skills/setup-github-project-tools/prompts/preflight.md`
- Create: `plugins/github-project-tools/skills/setup-github-project-tools/prompts/conventions.md`

**Step 1: Create prompts directory and shared prompts**

Copy `preflight.md` and `conventions.md` from add-issue (they must be identical).

```bash
mkdir -p plugins/github-project-tools/skills/setup-github-project-tools/prompts
cp plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/setup-github-project-tools/prompts/
cp plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/setup-github-project-tools/prompts/
```

**Step 2: Write SKILL.md**

Write to: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md`

```markdown
---
name: setup-github-project-tools
description: Set up or modify github-project-tools configuration in .claude-shim.json for the current repository
---

# GitHub Projects — Setup

Configure the github-project-tools plugin for this repository. Detects your GitHub Project, field IDs, and status mappings, then writes the configuration to `.claude-shim.json`.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Step 1: Check for Existing Config

Run:
```bash
<cli> read-config
```

- **If the command succeeds** (exit code 0, outputs JSON): Show the user a summary of the current configuration (project URL, field names, status mappings). Ask using AskUserQuestion:
  1. **Keep current config** — stop, no changes needed.
  2. **Reconfigure** — proceed to Step 2, overwriting the existing config.

- **If the command fails** (exit code 1): Proceed directly to Step 2.

## Step 2: Detect Repository

Auto-detect the repository:
```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

Save as `REPO` (e.g., `owner/repo`). Extract `OWNER` as the part before `/`.

Confirm with the user: "Detected repository: `REPO`. Correct?"

## Step 3: Detect Project

List the owner's projects:
```bash
gh project list --owner "$OWNER" --format json
```

Parse the JSON output. The `.projects` array contains objects with `number`, `title`, `id`, and `url`.

- **If no projects found:** Tell the user "No GitHub Projects found for owner `OWNER`. Create a project first, then re-run this setup." Stop.

- **If exactly one project:** Auto-select it. Tell the user: "Found project: `title` (`url`). Using this project." Ask for confirmation.

- **If multiple projects:** Try to auto-detect which project is used by this repo:
  ```bash
  gh issue list --repo "$REPO" --limit 5 --json number,projectItems
  ```
  Check if any returned issues have `projectItems` linking to one of the listed projects. If a match is found, recommend that project.

  Present the list of projects to the user with AskUserQuestion, highlighting the recommendation if any. User picks one.

Save `PROJECT_URL`, `PROJECT_NUMBER`, and `PROJECT_ID` from the selected project.

## Step 4: Detect Field IDs

Get the project's fields:
```bash
gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json
```

Parse the JSON output. The `.fields` array contains objects with `name`, `id`, and `type`.

**Date fields:** Look for fields with names matching (case-insensitive):
- Start date: "Start date", "Start Date", "Start"
- End date: "End date", "End Date", "End", "Due date", "Due Date"

If auto-detection finds matches, save `START_FIELD_ID` and `END_FIELD_ID`. Confirm with the user.

If auto-detection fails for either field, present the full list of date-type fields and ask the user to pick.

**Status field:** Look for a field named "Status" (case-insensitive). Save `STATUS_FIELD_ID` and the field's `.options` array.

If no "Status" field is found, present all single-select fields and ask the user to pick.

## Step 5: Detect Status Mappings

Using the status field's `.options` array from Step 4, auto-match option names to logical roles:

| Role | Try matching (case-insensitive) |
|------|-------------------------------|
| `todo` | "Todo", "To Do", "To do", "Backlog", "New" |
| `in-progress` | "In Progress", "In progress", "Working", "Active", "Doing" |
| `done` | "Done", "Complete", "Completed", "Shipped", "Closed" |

For each role:
- If exactly one option matches, auto-assign it.
- If multiple options match, ask the user to pick.
- If no options match, present the full list and ask the user to assign.

Present the proposed mapping for confirmation:
```
Status mappings:
  todo       → "Todo" (PVTO_xxx)
  in-progress → "In Progress" (PVTO_yyy)
  done       → "Done" (PVTO_zzz)
```

Ask: "Does this look right?"

## Step 6: Write Config

Build the configuration object:
```json
{
  "github-project-tools": {
    "project": "<PROJECT_URL>",
    "fields": {
      "start-date": "<START_FIELD_ID>",
      "end-date": "<END_FIELD_ID>",
      "status": {
        "id": "<STATUS_FIELD_ID>",
        "todo": { "name": "<name>", "option-id": "<id>" },
        "in-progress": { "name": "<name>", "option-id": "<id>" },
        "done": { "name": "<name>", "option-id": "<id>" }
      }
    }
  }
}
```

Present the final config JSON to the user for confirmation.

**Write to `.claude-shim.json`:**
- If the file exists: read it, add or replace the `github-project-tools` key, preserve all other keys (like `quality-checks`), write back.
- If the file doesn't exist: create it with just the `github-project-tools` key.

Use the Write tool to save the file.

## Step 7: Confirm

Tell the user:

> Configuration saved to `.claude-shim.json`. The github-project-tools skills will now use this configuration.
>
> Re-run this skill anytime to review or update the configuration.

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
```

**Step 3: Verify shared prompts are in sync with other skills**

```bash
diff plugins/github-project-tools/skills/add-issue/prompts/preflight.md plugins/github-project-tools/skills/setup-github-project-tools/prompts/preflight.md && diff plugins/github-project-tools/skills/add-issue/prompts/conventions.md plugins/github-project-tools/skills/setup-github-project-tools/prompts/conventions.md && echo "In sync"
```
Expected: `In sync`

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/
git commit -m "feat(github-project-tools): add setup-github-project-tools skill"
```

---

### Task 12: Update CI workflow

Add Python lint/typecheck/test jobs for the github-project-tools hook. Update the shared prompt sync check to include the new setup skill.

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add github-project-tools Python jobs**

Add three new jobs mirroring the existing quality-check-hook pattern:

```yaml
  github-tools-lint:
    runs-on: claude-shim-runner
    container:
      image: registry.phoebe.fi/claude-shim/ci:latest
      credentials:
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    steps:
      - name: Checkout
        uses: actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8  # v6

      - name: Ruff check
        run: uv run --project plugins/github-project-tools/hook ruff check

      - name: Ruff format check
        run: >-
          uv run --project plugins/github-project-tools/hook
          ruff format --check

  github-tools-typecheck:
    runs-on: claude-shim-runner
    container:
      image: registry.phoebe.fi/claude-shim/ci:latest
      credentials:
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    steps:
      - name: Checkout
        uses: actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8  # v6

      - name: Pyright
        run: uv run --project plugins/github-project-tools/hook pyright

  github-tools-test:
    runs-on: claude-shim-runner
    container:
      image: registry.phoebe.fi/claude-shim/ci:latest
      credentials:
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    steps:
      - name: Checkout
        uses: actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8  # v6

      - name: Pytest
        run: uv run --project plugins/github-project-tools/hook pytest -v
```

**Step 2: Update shared prompt sync check**

Update the `Verify shared prompts are in sync` step to:
- Include `setup-github-project-tools` in the preflight.md and conventions.md checks (now 4 skills share these)
- Keep setup.md and parse-issue-arg.md checks for start/end-implementation

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add github-project-tools Python lint, typecheck, and test jobs"
```

---

### Task 13: Delete old shell script and update plugin metadata

Remove `scripts/github-projects.sh` and bump the plugin version.

**Files:**
- Delete: `plugins/github-project-tools/scripts/github-projects.sh`
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Delete the shell script**

```bash
git rm plugins/github-project-tools/scripts/github-projects.sh
rmdir plugins/github-project-tools/scripts 2>/dev/null || true
```

**Step 2: Bump plugin version**

Update `plugins/github-project-tools/.claude-plugin/plugin.json` — change version from `"1.0.1"` to `"2.0.0"` (breaking change: shell script replaced by Python).

Update `.claude-plugin/marketplace.json` — change the github-project-tools entry version from `"1.0.1"` to `"2.0.0"`.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/ .claude-plugin/marketplace.json
git commit -m "feat(github-project-tools)!: remove shell script, bump to v2.0.0"
```

---

### Task 14: End-to-end verification

Verify everything works together in the claude-shim repo.

**Step 1: Run all Python tests**

```bash
uv run --project plugins/github-project-tools/hook pytest -v
uv run --project plugins/quality-check-hook/hook pytest -v
```

Expected: All tests pass in both plugins.

**Step 2: Run all linters**

```bash
uv run --project plugins/github-project-tools/hook ruff check
uv run --project plugins/github-project-tools/hook ruff format --check
uv run --project plugins/github-project-tools/hook pyright
```

Expected: All pass.

**Step 3: Verify shared prompt sync**

Run the CI sync check script manually (from the repo root) to confirm all shared prompts are identical.

**Step 4: Verify CLI works**

```bash
uv run --project plugins/github-project-tools/hook python -m github_project_tools preflight
uv run --project plugins/github-project-tools/hook python -m github_project_tools read-config
```

Expected: preflight succeeds, read-config fails with exit 1 (no config in claude-shim repo itself).

**Step 5: Verify JSON files are valid**

```bash
find . -name '*.json' -not -path './.git/*' -exec jq . {} \; > /dev/null
```

Expected: No errors.

**Step 6: Commit any fixes**

If any issues were found and fixed, commit them.
