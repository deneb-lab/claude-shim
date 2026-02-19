#!/usr/bin/env bash
# shellcheck disable=SC2016  # GraphQL queries use $var syntax (not bash expansions)
# Trivy-audit-specific GitHub operations
# Usage: scripts/trivy-audit-gh.sh <subcommand> [args...]
#
# Subcommands:
#   list-open-parents                     List open trivy-audit parent issues
#   get-sub-issues <parent-node-id>       List sub-issues of a parent
#   link-sub-issue <parent-id> <child-id> Link child issue to parent

set -euo pipefail

# --- Auto-detection ---

REPO=""

detect_repo() {
  if [[ -n "$REPO" ]]; then return; fi
  local remote_url
  remote_url=$(git remote get-url origin 2>/dev/null || echo "")
  if [[ "$remote_url" == *"phoebe.fi"*"dotfiles"* ]]; then
    REPO="elahti/deneb"
    return
  fi
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
}

detect_repo

graphql() {
  local query="$1"; shift
  gh api graphql -f query="$query" "$@"
}

# --- Trivy-specific queries ---

cmd_list_open_parents() {
  gh issue list --repo "$REPO" --label trivy-audit --state open \
    --json number,title,body \
    | jq '[.[] | select(.body | test("trivy-audit-parent"))]'
}

cmd_get_sub_issues() {
  graphql '
    query($id: ID!) {
      node(id: $id) {
        ... on Issue {
          subIssues(first: 50) { nodes { id number body state } }
        }
      }
    }' -f id="$1" --jq '.data.node.subIssues.nodes'
}

# --- Trivy-specific mutations ---

cmd_link_sub_issue() {
  graphql '
    mutation($parent: ID!, $child: ID!) {
      addSubIssue(input: {issueId: $parent, subIssueId: $child}) {
        issue { id }
      }
    }' -f parent="$1" -f child="$2"
}

# --- Main dispatch ---

case "${1:-}" in
  list-open-parents)     shift; cmd_list_open_parents "$@" ;;
  get-sub-issues)        shift; cmd_get_sub_issues "$@" ;;
  link-sub-issue)        shift; cmd_link_sub_issue "$@" ;;
  *)
    echo "Usage: $0 <subcommand> [args...]" >&2
    echo "Run '$0 <subcommand> --help' for subcommand help" >&2
    exit 1
    ;;
esac
