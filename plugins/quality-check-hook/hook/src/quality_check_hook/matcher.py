from __future__ import annotations

from wcmatch import glob as wcglob

from quality_check_hook.config import QualityChecks

GLOB_FLAGS = wcglob.GLOBSTAR | wcglob.BRACE | wcglob.DOTGLOB


def _matches(pattern: str, file_path: str) -> bool:
    return bool(wcglob.globmatch(file_path, pattern, flags=GLOB_FLAGS))


def _is_excluded(file_path: str, exclude: list[str]) -> bool:
    for pattern in exclude:
        if _matches(pattern, file_path):
            return True
        # Bare directory names (no glob chars) match as prefixes
        if not any(c in pattern for c in "*?[{") and file_path.startswith(
            pattern + "/"
        ):
            return True
    return False


def collect_commands(file_path: str, checks: QualityChecks) -> list[str]:
    if _is_excluded(file_path, checks.exclude):
        return []

    commands: list[str] = []
    for entry in checks.include:
        if _matches(entry.pattern, file_path):
            commands.extend(entry.commands)

    return commands
