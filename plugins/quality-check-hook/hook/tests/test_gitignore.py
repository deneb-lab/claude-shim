from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from quality_check_hook.gitignore import is_gitignored


class TestIsGitignored:
    def test_ignored_file_returns_true(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert is_gitignored("/repo/node_modules/pkg/index.js", cwd="/repo") is True

    def test_tracked_file_returns_false(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert is_gitignored("/repo/src/app.ts", cwd="/repo") is False

    def test_git_not_installed_returns_false(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            assert is_gitignored("/repo/src/app.ts", cwd="/repo") is False

    def test_timeout_returns_false(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            assert is_gitignored("/repo/src/app.ts", cwd="/repo") is False

    def test_not_a_git_repo_returns_false(self) -> None:
        """git check-ignore returns 128 when not in a git repo."""
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128)
            assert is_gitignored("/tmp/file.ts", cwd="/tmp") is False

    def test_passes_correct_args_to_subprocess(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            is_gitignored("/repo/src/app.ts", cwd="/repo")
            mock_run.assert_called_once_with(
                ["git", "check-ignore", "-q", "/repo/src/app.ts"],
                cwd="/repo",
                capture_output=True,
                timeout=5,
            )
