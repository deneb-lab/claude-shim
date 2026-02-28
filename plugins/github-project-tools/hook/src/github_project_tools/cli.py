from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from github_project_tools.config import load_config


def run_gh(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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

    # Placeholder for future subcommands
    _ = repo, sub_args
    print(f"Unknown subcommand: {subcmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
