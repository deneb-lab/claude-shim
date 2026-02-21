from __future__ import annotations

import json
import sys
from pathlib import Path

from quality_check_hook.config import load_config
from quality_check_hook.matcher import collect_commands
from quality_check_hook.runner import run_commands


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
