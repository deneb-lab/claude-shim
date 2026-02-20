# Claude Code Hooks Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a config-driven PostToolUse hook plugin that runs quality checks on files after Claude edits them, using Python + uv for zero-setup redistribution.

**Architecture:** A marketplace plugin (`plugins/claude-code-hooks/`) that registers a PostToolUse hook via native `hooks/hooks.json`. The hook reads `.claude-shim.json` from the consuming repo root, matches edited files against glob patterns, and runs configured commands sequentially. Built as a uv-managed Python project with Pydantic for config validation and wcmatch for glob matching.

**Tech Stack:** Python 3.13, uv, Pydantic, wcmatch, ruff, pyright, pytest

**Design doc:** `docs/plans/2026-02-20-claude-code-hooks-plugin-design.md`

---

### Task 1: Plugin Scaffold

Create the plugin metadata files and directory structure.

**Files:**
- Create: `plugins/claude-code-hooks/.claude-plugin/plugin.json`
- Create: `plugins/claude-code-hooks/hooks/hooks.json`

**Step 1: Create plugin.json**

```json
{
  "name": "claude-code-hooks",
  "description": "Config-driven quality checks for edited files — formatting, linting, auto-fix via PostToolUse hooks",
  "version": "0.1.0",
  "author": {
    "name": "elahti"
  },
  "repository": "https://github.com/elahti/claude-shim",
  "license": "MIT",
  "keywords": ["hooks", "linting", "formatting", "quality", "automation"]
}
```

**Step 2: Create hooks.json**

```json
{
  "description": "Config-driven quality checks for edited files",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --project \"${CLAUDE_PLUGIN_ROOT}/hook\" python -m claude_code_hooks.main",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

**Step 3: Commit**

```bash
git add plugins/claude-code-hooks/.claude-plugin/plugin.json plugins/claude-code-hooks/hooks/hooks.json
git commit -m "feat(claude-code-hooks): add plugin scaffold with hooks.json"
```

---

### Task 2: Python Project Setup

Create the uv-managed Python project with all tooling configuration.

**Files:**
- Create: `plugins/claude-code-hooks/hook/pyproject.toml`
- Create: `plugins/claude-code-hooks/hook/src/claude_code_hooks/__init__.py`
- Create: `plugins/claude-code-hooks/hook/tests/__init__.py`

**Step 1: Create pyproject.toml**

Use exact latest versions for all dependencies. The `requires-python` should be `">=3.12"` to support 3.12+.

```toml
[project]
name = "claude-code-hooks"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic==2.12.5",
    "wcmatch==10.1",
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
ignore = ["E501"]

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

**Step 2: Create empty __init__.py files**

`plugins/claude-code-hooks/hook/src/claude_code_hooks/__init__.py`: empty file.

`plugins/claude-code-hooks/hook/tests/__init__.py`: empty file.

**Step 3: Generate uv.lock**

Run: `cd plugins/claude-code-hooks/hook && uv lock`

This generates `uv.lock` pinning all transitive dependencies.

**Step 4: Verify tooling works**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check src/ tests/ && uv run pyright && uv run pytest`

Expected: all pass (no source files to check yet, no tests to run).

**Step 5: Commit**

```bash
git add plugins/claude-code-hooks/hook/
git commit -m "feat(claude-code-hooks): add uv project with tooling config"
```

---

### Task 3: Config Module (TDD)

Implement `.claude-shim.json` parsing with Pydantic models.

**Files:**
- Create: `plugins/claude-code-hooks/hook/src/claude_code_hooks/config.py`
- Create: `plugins/claude-code-hooks/hook/tests/test_config.py`

**Step 1: Write failing tests**

```python
from pathlib import Path
import json
import pytest
from claude_code_hooks.config import ClaudeShimConfig, load_config


class TestClaudeShimConfig:
    def test_valid_config(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {
                "include": [
                    {
                        "pattern": "**/*.ts",
                        "commands": ["npx prettier --write"],
                    }
                ],
                "exclude": ["node_modules"],
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert len(result.quality_checks.include) == 1
        assert result.quality_checks.include[0].pattern == "**/*.ts"
        assert result.quality_checks.include[0].commands == ["npx prettier --write"]
        assert result.quality_checks.exclude == ["node_modules"]

    def test_no_config_file_returns_none(self, tmp_path: Path) -> None:
        result = load_config(tmp_path)
        assert result is None

    def test_no_quality_checks_key_returns_none(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps({"other-key": {}}))

        result = load_config(tmp_path)
        assert result is None

    def test_empty_exclude_defaults(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {
                "include": [
                    {"pattern": "**/*.py", "commands": ["ruff check"]}
                ]
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.quality_checks.exclude == []

    def test_invalid_config_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps({"quality-checks": {"include": "not-a-list"}}))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_multiple_include_entries(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {
                "include": [
                    {"pattern": "**/*.ts", "commands": ["cmd1"]},
                    {"pattern": "**/*.py", "commands": ["cmd2", "cmd3"]},
                ]
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert len(result.quality_checks.include) == 2
        assert result.quality_checks.include[1].commands == ["cmd2", "cmd3"]
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_config.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'claude_code_hooks.config'`

**Step 3: Implement config.py**

```python
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

CONFIG_FILENAME = ".claude-shim.json"


class QualityCheckEntry(BaseModel):
    pattern: str
    commands: list[str]


class QualityChecks(BaseModel):
    include: list[QualityCheckEntry]
    exclude: list[str] = []


class ClaudeShimConfig(BaseModel):
    quality_checks: QualityChecks = Field(alias="quality-checks")


def load_config(cwd: Path) -> ClaudeShimConfig | None:
    config_path = cwd / CONFIG_FILENAME
    if not config_path.exists():
        return None

    raw = json.loads(config_path.read_text())

    if "quality-checks" not in raw:
        return None

    try:
        return ClaudeShimConfig.model_validate(raw)
    except ValidationError as exc:
        msg = f"Invalid {CONFIG_FILENAME}: {exc}"
        raise ValueError(msg) from exc
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_config.py -v`

Expected: all 6 tests PASS.

**Step 5: Run quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run pyright`

Expected: all pass.

**Step 6: Commit**

```bash
git add plugins/claude-code-hooks/hook/src/claude_code_hooks/config.py plugins/claude-code-hooks/hook/tests/test_config.py
git commit -m "feat(claude-code-hooks): add config module with Pydantic models"
```

---

### Task 4: Matcher Module (TDD)

Implement glob matching logic that checks files against include/exclude patterns.

**Files:**
- Create: `plugins/claude-code-hooks/hook/src/claude_code_hooks/matcher.py`
- Create: `plugins/claude-code-hooks/hook/tests/test_matcher.py`

**Step 1: Write failing tests**

```python
from claude_code_hooks.config import QualityCheckEntry, QualityChecks
from claude_code_hooks.matcher import collect_commands


class TestCollectCommands:
    def test_single_pattern_match(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
        )
        result = collect_commands("src/app.ts", checks)
        assert result == ["cmd1"]

    def test_single_pattern_no_match(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
        )
        result = collect_commands("src/app.py", checks)
        assert result == []

    def test_brace_expansion(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(
                    pattern="**/*.{ts,tsx}", commands=["prettier"]
                )
            ],
        )
        assert collect_commands("src/app.ts", checks) == ["prettier"]
        assert collect_commands("src/app.tsx", checks) == ["prettier"]
        assert collect_commands("src/app.js", checks) == []

    def test_multiple_patterns_same_file(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(
                    pattern="**/*.{js,ts}", commands=["prettier", "eslint --fix"]
                ),
                QualityCheckEntry(pattern="**/*.ts", commands=["eslint"]),
            ],
        )
        result = collect_commands("src/app.ts", checks)
        assert result == ["prettier", "eslint --fix", "eslint"]

    def test_multiple_patterns_partial_match(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(
                    pattern="**/*.{js,ts}", commands=["prettier"]
                ),
                QualityCheckEntry(pattern="**/*.ts", commands=["tsc"]),
            ],
        )
        result = collect_commands("src/app.js", checks)
        assert result == ["prettier"]

    def test_exclude_filters_file(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
            exclude=["node_modules"],
        )
        result = collect_commands("node_modules/pkg/index.ts", checks)
        assert result == []

    def test_exclude_glob_pattern(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
            exclude=["src/generated/**/*.ts"],
        )
        assert collect_commands("src/generated/types.ts", checks) == []
        assert collect_commands("src/app.ts", checks) == ["cmd1"]

    def test_empty_include(self) -> None:
        checks = QualityChecks(include=[])
        result = collect_commands("src/app.ts", checks)
        assert result == []

    def test_preserves_command_order(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(pattern="**/*", commands=["first", "second"]),
                QualityCheckEntry(pattern="**/*.ts", commands=["third"]),
            ],
        )
        result = collect_commands("src/app.ts", checks)
        assert result == ["first", "second", "third"]
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_matcher.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'claude_code_hooks.matcher'`

**Step 3: Implement matcher.py**

```python
from __future__ import annotations

from wcmatch import glob as wcglob

from claude_code_hooks.config import QualityChecks

GLOB_FLAGS = wcglob.GLOBSTAR | wcglob.BRACE | wcglob.DOTGLOB


def _matches(pattern: str, file_path: str) -> bool:
    return bool(wcglob.globmatch(file_path, pattern, flags=GLOB_FLAGS))


def _is_excluded(file_path: str, exclude: list[str]) -> bool:
    return any(_matches(pattern, file_path) for pattern in exclude)


def collect_commands(file_path: str, checks: QualityChecks) -> list[str]:
    if _is_excluded(file_path, checks.exclude):
        return []

    commands: list[str] = []
    for entry in checks.include:
        if _matches(entry.pattern, file_path):
            commands.extend(entry.commands)

    return commands
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_matcher.py -v`

Expected: all 9 tests PASS.

**Step 5: Run quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run pyright`

Expected: all pass.

**Step 6: Commit**

```bash
git add plugins/claude-code-hooks/hook/src/claude_code_hooks/matcher.py plugins/claude-code-hooks/hook/tests/test_matcher.py
git commit -m "feat(claude-code-hooks): add matcher module with glob matching"
```

---

### Task 5: Runner Module (TDD)

Implement sequential command execution.

**Files:**
- Create: `plugins/claude-code-hooks/hook/src/claude_code_hooks/runner.py`
- Create: `plugins/claude-code-hooks/hook/tests/test_runner.py`

**Step 1: Write failing tests**

```python
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from claude_code_hooks.runner import run_commands, CommandResult


class TestRunCommands:
    def test_all_commands_succeed(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = run_commands(["cmd1", "cmd2"], str(test_file), cwd=str(tmp_path))

        assert result.success
        assert mock_run.call_count == 2

    def test_first_command_fails_stops_execution(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="lint output", stderr="error detail"
            )
            result = run_commands(
                ["failing-cmd", "never-runs"], str(test_file), cwd=str(tmp_path)
            )

        assert not result.success
        assert "failing-cmd" in result.error_message
        assert mock_run.call_count == 1

    def test_file_path_appended_as_last_arg(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            run_commands(
                ["npx prettier --write"], str(test_file), cwd=str(tmp_path)
            )

        call_args = mock_run.call_args
        assert str(test_file) in call_args[0][0]

    def test_empty_commands_returns_success(self, tmp_path: Path) -> None:
        result = run_commands([], str(tmp_path / "test.ts"), cwd=str(tmp_path))
        assert result.success

    def test_command_output_included_in_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="line 5: unexpected token",
                stderr="",
            )
            result = run_commands(["eslint"], str(test_file), cwd=str(tmp_path))

        assert not result.success
        assert "unexpected token" in result.error_message

    def test_command_timeout(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="slow-cmd", timeout=30)
            result = run_commands(["slow-cmd"], str(test_file), cwd=str(tmp_path))

        assert not result.success
        assert "timed out" in result.error_message.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_runner.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'claude_code_hooks.runner'`

**Step 3: Implement runner.py**

```python
from __future__ import annotations

import subprocess
from dataclasses import dataclass

COMMAND_TIMEOUT_SECONDS = 30


@dataclass
class CommandResult:
    success: bool
    error_message: str = ""


def run_commands(commands: list[str], file_path: str, *, cwd: str) -> CommandResult:
    if not commands:
        return CommandResult(success=True)

    for command in commands:
        full_command = f"{command} {file_path}"
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                error_message=f"Command timed out after {COMMAND_TIMEOUT_SECONDS}s: {command}",
            )

        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            return CommandResult(
                success=False,
                error_message=f"Command failed: {command}\n{output}",
            )

    return CommandResult(success=True)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_runner.py -v`

Expected: all 6 tests PASS.

**Step 5: Run quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run pyright`

Expected: all pass.

**Step 6: Commit**

```bash
git add plugins/claude-code-hooks/hook/src/claude_code_hooks/runner.py plugins/claude-code-hooks/hook/tests/test_runner.py
git commit -m "feat(claude-code-hooks): add runner module for command execution"
```

---

### Task 6: Main Entry Point (TDD)

Implement the hook entry point that ties everything together.

**Files:**
- Create: `plugins/claude-code-hooks/hook/src/claude_code_hooks/main.py`
- Create: `plugins/claude-code-hooks/hook/tests/test_main.py`

**Step 1: Write failing tests**

```python
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude_code_hooks.main import handle_hook


class TestHandleHook:
    def _make_payload(self, file_path: str, cwd: str) -> dict[str, object]:
        return {
            "session_id": "test",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
            "tool_response": {"filePath": file_path, "success": True},
            "cwd": cwd,
        }

    def test_no_config_file_returns_success(self, tmp_path: Path) -> None:
        payload = self._make_payload(str(tmp_path / "test.ts"), str(tmp_path))
        exit_code, stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0
        assert stderr == ""

    def test_no_matching_patterns_returns_success(self, tmp_path: Path) -> None:
        config = {
            "quality-checks": {
                "include": [{"pattern": "**/*.py", "commands": ["ruff check"]}]
            }
        }
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
        payload = self._make_payload(str(tmp_path / "test.ts"), str(tmp_path))

        exit_code, stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0
        assert stderr == ""

    def test_command_success(self, tmp_path: Path) -> None:
        config = {
            "quality-checks": {
                "include": [{"pattern": "**/*.ts", "commands": ["prettier --write"]}]
            }
        }
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
        test_file = tmp_path / "src" / "app.ts"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("content")
        payload = self._make_payload(str(test_file), str(tmp_path))

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            exit_code, stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0

    def test_command_failure_returns_exit_2(self, tmp_path: Path) -> None:
        config = {
            "quality-checks": {
                "include": [{"pattern": "**/*.ts", "commands": ["eslint"]}]
            }
        }
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
        test_file = tmp_path / "app.ts"
        test_file.write_text("content")
        payload = self._make_payload(str(test_file), str(tmp_path))

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="error found", stderr=""
            )
            exit_code, stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 2
        assert "eslint" in stderr

    def test_invalid_config_returns_exit_2(self, tmp_path: Path) -> None:
        (tmp_path / ".claude-shim.json").write_text(
            json.dumps({"quality-checks": {"include": "bad"}})
        )
        payload = self._make_payload(str(tmp_path / "test.ts"), str(tmp_path))

        exit_code, stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 2
        assert "Invalid" in stderr

    def test_edit_tool_extracts_file_path(self, tmp_path: Path) -> None:
        config = {
            "quality-checks": {
                "include": [{"pattern": "**/*.ts", "commands": ["cmd"]}]
            }
        }
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
        test_file = tmp_path / "app.ts"
        test_file.write_text("content")
        payload = {
            "session_id": "test",
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(test_file),
                "old_string": "a",
                "new_string": "b",
            },
            "tool_response": {},
            "cwd": str(tmp_path),
        }

        with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            exit_code, stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0
        assert mock_run.call_count == 1

    def test_missing_file_path_returns_success(self, tmp_path: Path) -> None:
        payload = {
            "session_id": "test",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {},
            "tool_response": {},
            "cwd": str(tmp_path),
        }
        exit_code, stdout, stderr = handle_hook(json.dumps(payload))
        assert exit_code == 0
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_main.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'claude_code_hooks.main'`

**Step 3: Implement main.py**

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

from claude_code_hooks.config import load_config
from claude_code_hooks.matcher import collect_commands
from claude_code_hooks.runner import run_commands


def _extract_file_path(tool_input: dict[str, object]) -> str | None:
    file_path = tool_input.get("file_path")
    if isinstance(file_path, str):
        return file_path
    return None


def handle_hook(raw_input: str) -> tuple[int, str, str]:
    payload = json.loads(raw_input)
    tool_input: dict[str, object] = payload.get("tool_input", {})
    cwd = str(payload.get("cwd", "."))

    file_path = _extract_file_path(tool_input)
    if file_path is None:
        return 0, "{}", ""

    cwd_path = Path(cwd)

    try:
        config = load_config(cwd_path)
    except ValueError as exc:
        return 2, "", str(exc)

    if config is None:
        return 0, "{}", ""

    try:
        relative_path = str(Path(file_path).relative_to(cwd_path))
    except ValueError:
        return 0, "{}", ""

    commands = collect_commands(relative_path, config.quality_checks)
    if not commands:
        return 0, "{}", ""

    result = run_commands(commands, file_path, cwd=cwd)

    if not result.success:
        return 2, "", result.error_message

    return 0, "{}", ""


def main() -> None:
    raw_input = sys.stdin.read()
    exit_code, stdout, stderr = handle_hook(raw_input)

    if stdout:
        sys.stdout.write(stdout)
    if stderr:
        sys.stderr.write(stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_main.py -v`

Expected: all 7 tests PASS.

**Step 5: Run all tests + quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest -v && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run pyright`

Expected: all 28 tests PASS, linting/formatting/types all clean.

**Step 6: Commit**

```bash
git add plugins/claude-code-hooks/hook/src/claude_code_hooks/main.py plugins/claude-code-hooks/hook/tests/test_main.py
git commit -m "feat(claude-code-hooks): add main entry point"
```

---

### Task 7: CI Integration

Update the Dockerfile and GitHub Actions workflow to support Python quality checks.

**Files:**
- Modify: `.github/images/ci/Dockerfile`
- Modify: `.github/workflows/ci.yml`

**Step 1: Update Dockerfile**

Add uv installation. Use the official install script which gets the latest version:

```dockerfile
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    jq \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx
```

**Step 2: Update ci.yml**

Add three new jobs for Python quality checks. Keep the existing `lint` job unchanged:

```yaml
---
name: CI
"on": [push, pull_request]
jobs:
  lint:
    runs-on: claude-shim-runner
    container:
      image: registry.phoebe.fi/claude-shim/ci:latest
      credentials:
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    steps:
      - name: Checkout
        uses: actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8  # v6

      - name: Run shellcheck
        run: |
          find . -name '*.sh' -print0 | xargs -0 shellcheck

      - name: Validate JSON files
        run: |
          for f in $(find . -name '*.json' -not -path './.git/*'); do
            echo "Checking $f..."
            jq . "$f" > /dev/null
          done

  python-lint:
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
        run: uv run --project plugins/claude-code-hooks/hook ruff check

      - name: Ruff format check
        run: uv run --project plugins/claude-code-hooks/hook ruff format --check

  python-typecheck:
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
        run: uv run --project plugins/claude-code-hooks/hook pyright

  python-test:
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
        run: uv run --project plugins/claude-code-hooks/hook pytest -v
```

**Step 3: Commit**

```bash
git add .github/images/ci/Dockerfile .github/workflows/ci.yml
git commit -m "ci: add Python quality checks and uv to CI pipeline"
```

---

### Task 8: Marketplace & README Updates

Register the new plugin in the marketplace catalog and update the README.

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

**Step 1: Update marketplace.json**

Add the new plugin to the `plugins` array and bump `metadata.version`:

```json
{
  "name": "claude-shim-marketplace",
  "owner": {
    "name": "elahti"
  },
  "metadata": {
    "description": "Claude Code plugins for project management, security auditing, and automation",
    "version": "0.9.0"
  },
  "plugins": [
    {
      "name": "github-project-tools",
      "source": "./plugins/github-project-tools",
      "description": "GitHub issue creation and implementation with project board lifecycle management",
      "version": "0.8.0",
      "strict": true
    },
    {
      "name": "trivy-audit",
      "source": "./plugins/trivy-audit",
      "description": "Trivy security audit coordinator — CVE analysis, version staleness, config audits with agent team",
      "version": "0.2.0",
      "strict": true
    },
    {
      "name": "claude-code-hooks",
      "source": "./plugins/claude-code-hooks",
      "description": "Config-driven quality checks for edited files — formatting, linting, auto-fix via PostToolUse hooks",
      "version": "0.1.0"
    }
  ]
}
```

**Step 2: Update README.md**

Add the new plugin section after the Trivy Audit section and update the marketplace structure tree.

After the `---` following Trivy Audit, add:

```markdown
---

### Claude Code Hooks

**Description:** Config-driven quality checks for edited files — formatting, linting, auto-fix via PostToolUse hooks

**Install:**
```bash
/plugin install claude-code-hooks@claude-shim-marketplace
```

**Setup:** Create `.claude-shim.json` in your repo root:

```json
{
  "quality-checks": {
    "include": [
      {
        "pattern": "**/*.{js,jsx,ts,tsx}",
        "commands": [
          "npx prettier --write",
          "npx eslint --fix",
          "npx eslint"
        ]
      }
    ],
    "exclude": [
      "node_modules"
    ]
  }
}
```

**Requires:** [uv](https://docs.astral.sh/uv/) on PATH. The hook fails closed if uv is unavailable.
```

Update the marketplace structure tree to include the new plugin directory.

**Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "chore: add claude-code-hooks to marketplace and README"
```

---

### Task 9: Final Verification

Run all checks end-to-end and verify everything works together.

**Step 1: Run all Python tests**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest -v`

Expected: all 28 tests PASS.

**Step 2: Run all Python quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check && uv run ruff format --check && uv run pyright`

Expected: all clean.

**Step 3: Run existing CI checks locally**

Run shellcheck:
```bash
find . -name '*.sh' -print0 | xargs -0 shellcheck
```

Validate all JSON:
```bash
for f in $(find . -name '*.json' -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/.venv/*'); do echo "Checking $f..."; jq . "$f" > /dev/null; done
```

Expected: all pass.

**Step 4: Verify plugin structure**

Confirm these files exist with correct content:
- `plugins/claude-code-hooks/.claude-plugin/plugin.json`
- `plugins/claude-code-hooks/hooks/hooks.json`
- `plugins/claude-code-hooks/hook/pyproject.toml`
- `plugins/claude-code-hooks/hook/uv.lock`
- `plugins/claude-code-hooks/hook/src/claude_code_hooks/__init__.py`
- `plugins/claude-code-hooks/hook/src/claude_code_hooks/main.py`
- `plugins/claude-code-hooks/hook/src/claude_code_hooks/config.py`
- `plugins/claude-code-hooks/hook/src/claude_code_hooks/matcher.py`
- `plugins/claude-code-hooks/hook/src/claude_code_hooks/runner.py`
- `plugins/claude-code-hooks/hook/tests/__init__.py`
- `plugins/claude-code-hooks/hook/tests/test_config.py`
- `plugins/claude-code-hooks/hook/tests/test_matcher.py`
- `plugins/claude-code-hooks/hook/tests/test_runner.py`
- `plugins/claude-code-hooks/hook/tests/test_main.py`
