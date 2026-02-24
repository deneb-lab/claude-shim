import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from quality_check_hook.main import handle_hook


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
        exit_code, _stdout, stderr = handle_hook(json.dumps(payload))

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

        exit_code, _stdout, stderr = handle_hook(json.dumps(payload))

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

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            exit_code, _stdout, _stderr = handle_hook(json.dumps(payload))

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

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="error found", stderr=""
            )
            exit_code, _stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 2
        assert "eslint" in stderr

    def test_invalid_config_returns_exit_2(self, tmp_path: Path) -> None:
        (tmp_path / ".claude-shim.json").write_text(
            json.dumps({"quality-checks": {"include": "bad"}})
        )
        payload = self._make_payload(str(tmp_path / "test.ts"), str(tmp_path))

        exit_code, _stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 2
        assert "Invalid" in stderr

    def test_edit_tool_extracts_file_path(self, tmp_path: Path) -> None:
        config = {
            "quality-checks": {"include": [{"pattern": "**/*.ts", "commands": ["cmd"]}]}
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

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            exit_code, _stdout, _stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0
        assert mock_run.call_count == 1

    def test_gitignored_file_skipped(self, tmp_path: Path) -> None:
        """Gitignored files should be skipped even if they match a pattern."""
        config = {
            "quality-checks": {
                "include": [{"pattern": "**/*.ts", "commands": ["eslint"]}]
            }
        }
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
        test_file = tmp_path / "generated" / "types.ts"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("content")
        payload = self._make_payload(str(test_file), str(tmp_path))

        with (
            patch("quality_check_hook.main.is_gitignored", return_value=True),
            patch("quality_check_hook.runner.subprocess.run") as mock_run,
        ):
            exit_code, _stdout, stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0
        assert stderr == ""
        assert mock_run.call_count == 0

    def test_non_gitignored_file_checked(self, tmp_path: Path) -> None:
        """Non-gitignored files should proceed through normal quality checks."""
        config = {
            "quality-checks": {
                "include": [{"pattern": "**/*.ts", "commands": ["eslint"]}]
            }
        }
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
        test_file = tmp_path / "src" / "app.ts"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("content")
        payload = self._make_payload(str(test_file), str(tmp_path))

        with (
            patch("quality_check_hook.main.is_gitignored", return_value=False),
            patch("quality_check_hook.runner.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            exit_code, _stdout, _stderr = handle_hook(json.dumps(payload))

        assert exit_code == 0
        assert mock_run.call_count == 1

    def test_missing_file_path_returns_success(self, tmp_path: Path) -> None:
        payload: dict[str, object] = {
            "session_id": "test",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {},
            "tool_response": {},
            "cwd": str(tmp_path),
        }
        exit_code, _stdout, _stderr = handle_hook(json.dumps(payload))
        assert exit_code == 0
