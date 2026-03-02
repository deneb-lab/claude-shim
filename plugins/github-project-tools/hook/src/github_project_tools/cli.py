from __future__ import annotations

import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from github_project_tools.config import GitHubProjectToolsConfig, load_config


def run_gh(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
        **kwargs,  # type: ignore[arg-type]
    )


def graphql(
    query: str,
    variables: dict[str, str],
    jq_filter: str | None = None,
) -> subprocess.CompletedProcess[str]:
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-f", f"{key}={value}"])
    if jq_filter:
        args.extend(["--jq", jq_filter])
    return run_gh(args)


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


def parse_project_url(url: str) -> tuple[str, str]:
    """Parse a project URL and return (owner, project_number).

    Handles both user and org URLs:
    - https://github.com/users/elahti/projects/1
    - https://github.com/orgs/my-org/projects/42
    """
    match = re.match(r"https://github\.com/(?:users|orgs)/([^/]+)/projects/(\d+)", url)
    if not match:
        msg = f"Invalid project URL: {url}"
        raise ValueError(msg)
    return match.group(1), match.group(2)


def load_config_or_fail(cwd: Path) -> GitHubProjectToolsConfig:
    config = load_config(cwd)
    if config is None:
        print(
            "No github-project-tools config found. Run the setup skill to create one.",
            file=sys.stderr,
        )
        sys.exit(1)
    return config


# Cache for project ID lookups
_project_id_cache: dict[str, str] = {}


def get_project_id(config: GitHubProjectToolsConfig) -> str:
    """Get the GraphQL project ID by querying the project URL from config."""
    if config.project in _project_id_cache:
        return _project_id_cache[config.project]

    owner, number = parse_project_url(config.project)
    result = run_gh(
        [
            "project",
            "view",
            number,
            "--owner",
            owner,
            "--format",
            "json",
            "--jq",
            ".id",
        ]
    )
    project_id = result.stdout.strip()
    if not project_id or result.returncode != 0:
        print(
            f"get_project_id: failed to get project ID for {config.project}",
            file=sys.stderr,
        )
        sys.exit(1)
    _project_id_cache[config.project] = project_id
    return project_id


# --- No-config commands ---


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


def cmd_repo_detect(repo_override: str | None) -> int:
    repo = detect_repo(repo_override)
    print(repo)
    return 0


def cmd_project_list(args: list[str]) -> int:
    owner = ""
    i = 0
    while i < len(args):
        if args[i] == "--owner":
            if i + 1 >= len(args):
                print("project-list: --owner requires an argument", file=sys.stderr)
                return 1
            owner = args[i + 1]
            i += 2
        else:
            print(f"project-list: unknown arg: {args[i]}", file=sys.stderr)
            return 1
    if not owner:
        print("project-list: --owner required", file=sys.stderr)
        return 1
    result = run_gh(["project", "list", "--owner", owner, "--format", "json"])
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_project_field_list(args: list[str]) -> int:
    owner = ""
    number = ""
    i = 0
    while i < len(args):
        if args[i] == "--owner":
            if i + 1 >= len(args):
                print(
                    "project-field-list: --owner requires an argument", file=sys.stderr
                )
                return 1
            owner = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            number = args[i]
            i += 1
        else:
            print(f"project-field-list: unknown arg: {args[i]}", file=sys.stderr)
            return 1
    if not owner:
        print("project-field-list: --owner required", file=sys.stderr)
        return 1
    if not number:
        print("project-field-list: project number required", file=sys.stderr)
        return 1
    result = run_gh(
        ["project", "field-list", number, "--owner", owner, "--format", "json"]
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


# --- Issue subcommands ---


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


def cmd_issue_list(repo: str, extra_args: list[str]) -> int:
    result = run_gh(["issue", "list", "--repo", repo, *extra_args])
    if result.stdout:
        print(result.stdout, end="")
    return 0


# --- Config-driven project board subcommands ---


def cmd_get_project_item(config: GitHubProjectToolsConfig, node_id: str) -> int:
    project_id = get_project_id(config)
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              projectItems(first: 10) { nodes { id project { id } } }
            }
          }
        }""",
        {"id": node_id},
        jq_filter=(
            f'.data.node.projectItems.nodes[] | select(.project.id == "{project_id}") | .id'
        ),
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_get_start_date(config: GitHubProjectToolsConfig, node_id: str) -> int:
    project_id = get_project_id(config)
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              projectItems(first: 10) {
                nodes {
                  id
                  project { id }
                  fieldValueByName(name: "Start date") {
                    ... on ProjectV2ItemFieldDateValue { date }
                  }
                }
              }
            }
          }
        }""",
        {"id": node_id},
        jq_filter=(
            f'.data.node.projectItems.nodes[] | select(.project.id == "{project_id}")'
            " | {item_id: .id, date: (.fieldValueByName.date // null)}"
        ),
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_add_to_project(config: GitHubProjectToolsConfig, node_id: str) -> int:
    project_id = get_project_id(config)
    result = graphql(
        """
        mutation($project: ID!, $content: ID!) {
          addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
            item { id }
          }
        }""",
        {"project": project_id, "content": node_id},
        jq_filter=".data.addProjectV2ItemById.item.id",
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_set_status(
    config: GitHubProjectToolsConfig,
    item_id: str,
    status_key: str,
) -> int:
    status_map: dict[str, str] = {
        "todo": config.fields.status.todo.option_id,
        "in-progress": config.fields.status.in_progress.option_id,
        "done": config.fields.status.done.option_id,
    }
    option_id = status_map.get(status_key)
    if option_id is None:
        valid = ", ".join(status_map)
        print(
            f"set-status: unknown status '{status_key}' (valid: {valid})",
            file=sys.stderr,
        )
        return 1

    project_id = get_project_id(config)
    field_id = config.fields.status.id
    graphql(
        """
        mutation($project: ID!, $item: ID!, $field: ID!, $value: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $project, itemId: $item,
            fieldId: $field, value: {singleSelectOptionId: $value}
          }) { projectV2Item { id } }
        }""",
        {
            "project": project_id,
            "item": item_id,
            "field": field_id,
            "value": option_id,
        },
    )
    return 0


def cmd_set_date(
    config: GitHubProjectToolsConfig,
    item_id: str,
    field_id: str,
) -> int:
    project_id = get_project_id(config)
    today = datetime.now(UTC).date().isoformat()
    graphql(
        """
        mutation($project: ID!, $item: ID!, $field: ID!, $date: Date!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $project, itemId: $item,
            fieldId: $field, value: {date: $date}
          }) { projectV2Item { id } }
        }""",
        {
            "project": project_id,
            "item": item_id,
            "field": field_id,
            "date": today,
        },
    )
    return 0


# --- Repo-only subcommands ---


def cmd_get_parent(node_id: str) -> int:
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue { parent { id number title state } }
          }
        }""",
        {"id": node_id},
        jq_filter=".data.node.parent",
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_count_open_sub_issues(node_id: str) -> int:
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              subIssues(first: 50) { nodes { state } }
            }
          }
        }""",
        {"id": node_id},
        jq_filter='[.data.node.subIssues.nodes[] | select(.state == "OPEN")] | length',
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_set_parent(child_id: str, parent_id: str) -> int:
    result = graphql(
        """
        mutation($parent: ID!, $child: ID!) {
          addSubIssue(input: {issueId: $parent, subIssueId: $child}) {
            subIssue { id }
          }
        }""",
        {"parent": parent_id, "child": child_id},
        jq_filter=".data.addSubIssue.subIssue.id",
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0


def cmd_table_set_status(
    repo: str,
    parent_number: str,
    sub_number: str,
    new_status: str,
) -> int:
    """Update the status column in an Action Plan markdown table."""
    result = run_gh(
        [
            "issue",
            "view",
            parent_number,
            "--repo",
            repo,
            "--json",
            "body",
            "--jq",
            ".body",
        ]
    )
    body = result.stdout

    # Port the awk logic: match lines containing /issues/<sub_number>) or
    # #<sub_number>), then replace the last | ... | with | <status> |
    issue_pat = re.compile(
        rf"(?:/issues/{re.escape(sub_number)}\)|#{re.escape(sub_number)}\))"
    )
    trailing_col = re.compile(r"\| [^|]* \|$")

    lines = body.split("\n")
    updated_lines: list[str] = []
    for line in lines:
        if issue_pat.search(line):
            m = trailing_col.search(line)
            if m:
                line = line[: m.start()] + f"| {new_status} |"
        updated_lines.append(line)

    updated_body = "\n".join(updated_lines)
    run_gh(["issue", "edit", parent_number, "--repo", repo, "--body", updated_body])
    return 0


# --- Main dispatch ---


def main(argv: list[str] | None = None, cwd: Path | None = None) -> int:
    # Clear project ID cache between invocations (for testability)
    _project_id_cache.clear()

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
    if subcmd == "repo-detect":
        return cmd_repo_detect(repo)
    if subcmd == "project-list":
        return cmd_project_list(sub_args)
    if subcmd == "project-field-list":
        return cmd_project_field_list(sub_args)

    # Issue subcommands require repo detection
    issue_cmds = {
        "issue-view",
        "issue-view-full",
        "issue-create",
        "issue-edit",
        "issue-close",
        "issue-assign",
        "issue-list",
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
        if subcmd == "issue-list":
            return cmd_issue_list(resolved_repo, sub_args)

    # Config-driven project board subcommands
    config_cmds = {
        "get-project-item",
        "get-start-date",
        "add-to-project",
        "set-status",
        "set-date",
    }
    if subcmd in config_cmds:
        config = load_config_or_fail(working_dir)

        if subcmd == "get-project-item":
            return cmd_get_project_item(config, sub_args[0])
        if subcmd == "get-start-date":
            return cmd_get_start_date(config, sub_args[0])
        if subcmd == "add-to-project":
            return cmd_add_to_project(config, sub_args[0])
        if subcmd == "set-status":
            return cmd_set_status(config, sub_args[0], sub_args[1])
        if subcmd == "set-date":
            return cmd_set_date(config, sub_args[0], sub_args[1])

    # Repo-only subcommands (no config needed)
    repo_only_cmds = {
        "get-parent",
        "count-open-sub-issues",
        "set-parent",
        "table-set-status",
    }
    if subcmd in repo_only_cmds:
        resolved_repo = detect_repo(repo)

        if subcmd == "get-parent":
            return cmd_get_parent(sub_args[0])
        if subcmd == "count-open-sub-issues":
            return cmd_count_open_sub_issues(sub_args[0])
        if subcmd == "set-parent":
            return cmd_set_parent(sub_args[0], sub_args[1])
        if subcmd == "table-set-status":
            return cmd_table_set_status(
                resolved_repo, sub_args[0], sub_args[1], sub_args[2]
            )

    print(f"Unknown subcommand: {subcmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
