from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

COMMAND_TIMEOUT_SECONDS = 30


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    return env


@dataclass
class CommandResult:
    success: bool
    error_message: str = ""


def run_commands(commands: list[str], file_path: str, *, cwd: str) -> CommandResult:
    if not commands:
        return CommandResult(success=True)

    env = _clean_env()

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
                env=env,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                error_message=f"Command timed out after {COMMAND_TIMEOUT_SECONDS}s: {command}",
            )

        if result.returncode != 0:
            if command.startswith("ansible-lint --fix"):
                continue
            output = (result.stdout + result.stderr).strip()
            return CommandResult(
                success=False,
                error_message=f"Command failed: {command}\n{output}",
            )

    return CommandResult(success=True)
