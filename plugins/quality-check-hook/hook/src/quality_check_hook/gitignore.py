from __future__ import annotations

import subprocess

GITIGNORE_CHECK_TIMEOUT_SECONDS = 5


def is_gitignored(file_path: str, *, cwd: str) -> bool:
    """Check if a file is ignored by .gitignore using git check-ignore.

    Returns True if the file is gitignored, False otherwise.
    Fails open: if git is unavailable or times out, returns False
    so quality checks still run.
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", file_path],
            cwd=cwd,
            capture_output=True,
            timeout=GITIGNORE_CHECK_TIMEOUT_SECONDS,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
