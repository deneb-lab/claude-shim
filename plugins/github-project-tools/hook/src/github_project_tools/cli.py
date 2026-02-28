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


def detect_repo(repo_override: str | None) -> str:
    if repo_override is not None:
        return repo_override
    result = run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    if result.returncode != 0:
        print(
            "detect_repo: failed to detect repository (is gh authenticated?)",
            file=sys.stderr,
        )
        sys.exit(1)
    repo = result.stdout.strip()
    if not repo:
        print("detect_repo: no repository found", file=sys.stderr)
        sys.exit(1)
    return repo


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


def cmd_issue_view(repo: str, number: str, extra_args: list[str]) -> int:
    result = run_gh(["issue", "view", number, "--repo", repo, *extra_args])
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_issue_view_full(repo: str, number: str) -> int:
    result = run_gh(
        [
            "issue",
            "view",
            number,
            "--repo",
            repo,
            "--json",
            "id,number,title,body,state",
        ]
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_issue_create(repo: str, args: list[str]) -> int:
    title = ""
    body = ""
    label = ""
    i = 0
    while i < len(args):
        if args[i] == "--title":
            title = args[i + 1]
            i += 2
        elif args[i] == "--body":
            body = args[i + 1]
            i += 2
        elif args[i] == "--body-file":
            body = Path(args[i + 1]).read_text()
            i += 2
        elif args[i] == "--label":
            label = args[i + 1]
            i += 2
        else:
            print(f"issue-create: unknown arg: {args[i]}", file=sys.stderr)
            return 1
    if not title:
        print("issue-create: --title required", file=sys.stderr)
        return 1
    if not body:
        print("issue-create: --body required", file=sys.stderr)
        return 1
    cmd = ["issue", "create", "--repo", repo, "--title", title, "--body", body]
    if label:
        cmd.extend(["--label", label])
    result = run_gh(cmd)
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_issue_edit(repo: str, number: str, args: list[str]) -> int:
    body = ""
    i = 0
    while i < len(args):
        if args[i] == "--body":
            body = args[i + 1]
            i += 2
        elif args[i] == "--body-file":
            body = Path(args[i + 1]).read_text()
            i += 2
        else:
            print(f"issue-edit: unknown arg: {args[i]}", file=sys.stderr)
            return 1
    if not body:
        print("issue-edit: --body required", file=sys.stderr)
        return 1
    result = run_gh(["issue", "edit", number, "--repo", repo, "--body", body])
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_issue_close(repo: str, number: str, args: list[str]) -> int:
    comment = ""
    comment_file = ""
    i = 0
    while i < len(args):
        if args[i] == "--comment":
            comment = args[i + 1]
            i += 2
        elif args[i] == "--comment-file":
            comment_file = args[i + 1]
            i += 2
        else:
            print(f"issue-close: unknown arg: {args[i]}", file=sys.stderr)
            return 1

    # --comment-file overrides --comment
    if comment_file:
        comment = Path(comment_file).read_text()

    # Check current issue state
    state_result = run_gh(
        ["issue", "view", number, "--repo", repo, "--json", "state", "--jq", ".state"]
    )
    state = state_result.stdout.strip()

    if state == "OPEN":
        cmd = ["issue", "close", number, "--repo", repo, "--reason", "completed"]
        if comment:
            cmd.extend(["--comment", comment])
        run_gh(cmd)
    else:
        print(f"Issue #{number} is already closed — skipping close.", file=sys.stderr)
        if comment:
            if comment_file:
                run_gh(
                    [
                        "issue",
                        "comment",
                        number,
                        "--repo",
                        repo,
                        "--body-file",
                        comment_file,
                    ]
                )
            else:
                run_gh(["issue", "comment", number, "--repo", repo, "--body", comment])
    return 0


def cmd_issue_assign(repo: str, number: str) -> int:
    result = run_gh(["issue", "edit", number, "--repo", repo, "--add-assignee", "@me"])
    if result.stdout:
        print(result.stdout, end="")
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

    # Issue subcommands require repo detection
    issue_cmds = {
        "issue-view",
        "issue-view-full",
        "issue-create",
        "issue-edit",
        "issue-close",
        "issue-assign",
    }
    if subcmd in issue_cmds:
        resolved_repo = detect_repo(repo)

        if subcmd == "issue-view":
            return cmd_issue_view(resolved_repo, sub_args[0], sub_args[1:])
        if subcmd == "issue-view-full":
            return cmd_issue_view_full(resolved_repo, sub_args[0])
        if subcmd == "issue-create":
            return cmd_issue_create(resolved_repo, sub_args)
        if subcmd == "issue-edit":
            return cmd_issue_edit(resolved_repo, sub_args[0], sub_args[1:])
        if subcmd == "issue-close":
            return cmd_issue_close(resolved_repo, sub_args[0], sub_args[1:])
        if subcmd == "issue-assign":
            return cmd_issue_assign(resolved_repo, sub_args[0])

    print(f"Unknown subcommand: {subcmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
