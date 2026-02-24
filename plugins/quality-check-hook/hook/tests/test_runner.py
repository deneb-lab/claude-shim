import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from quality_check_hook.runner import run_commands


class TestRunCommands:
    def test_all_commands_succeed(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = run_commands(["cmd1", "cmd2"], str(test_file), cwd=str(tmp_path))

        assert result.success
        assert mock_run.call_count == 2

    def test_first_command_fails_stops_execution(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
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

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            run_commands(["npx prettier --write"], str(test_file), cwd=str(tmp_path))

        call_args = mock_run.call_args
        assert str(test_file) in call_args[0][0]

    def test_empty_commands_returns_success(self, tmp_path: Path) -> None:
        result = run_commands([], str(tmp_path / "test.ts"), cwd=str(tmp_path))
        assert result.success

    def test_command_output_included_in_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.ts"
        test_file.write_text("content")

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
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

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="slow-cmd", timeout=30)
            result = run_commands(["slow-cmd"], str(test_file), cwd=str(tmp_path))

        assert not result.success
        assert "timed out" in result.error_message.lower()

    def test_ansible_lint_fix_nonzero_continues_execution(self, tmp_path: Path) -> None:
        """ansible-lint --fix may exit non-zero after successful fixes; runner should continue."""
        test_file = tmp_path / "main.yml"
        test_file.write_text("content")

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="Modified 1 file.\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            result = run_commands(
                ["ansible-lint --fix", "ansible-lint"],
                str(test_file),
                cwd=str(tmp_path),
            )

        assert result.success
        assert mock_run.call_count == 2

    def test_virtual_env_stripped_from_subprocess_env(self, tmp_path: Path) -> None:
        """Subprocess should not inherit VIRTUAL_ENV from the hook's own venv."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        with (
            patch.dict("os.environ", {"VIRTUAL_ENV": "/some/venv", "PATH": "/usr/bin"}),
            patch("quality_check_hook.runner.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            run_commands(["ruff check"], str(test_file), cwd=str(tmp_path))

        env_passed = mock_run.call_args.kwargs["env"]
        assert "VIRTUAL_ENV" not in env_passed
        assert env_passed["PATH"] == "/usr/bin"
