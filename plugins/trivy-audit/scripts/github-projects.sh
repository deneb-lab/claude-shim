#!/usr/bin/env bash
# shellcheck disable=SC2016  # GraphQL queries use $var syntax (not bash expansions)
# Shared GitHub Projects operations
# Usage: scripts/github-projects.sh <subcommand> [args...]
#
# Subcommands:
#   issue-view <number> [gh-flags...]     View issue (passthrough to gh issue view)
#   issue-create --title T --body B       Create issue (optional --label)
#   issue-edit <number> --body B          Update issue body
#   issue-close <number>                  Close issue as completed
#   get-project-item <node-id>            Get project item ID for an issue
#   get-project-fields                    Get date field IDs
#   get-start-date <node-id>              Get project item ID + start date
#   add-to-project <node-id>              Add issue to project, returns item ID
#   set-status <item-id> <status>         Set project status (todo|in-progress|done)
#   set-date <item-id> <field-id>         Set project date field (always today)
#   get-parent <node-id>                  Get parent issue (id, number, title, state)
#   count-open-sub-issues <node-id>       Count open sub-issues of a parent
#   table-set-status <parent#> <sub#> <s> Update Action Plan table status column

set -euo pipefail

# --- Auto-detection (lazy init) ---

REPO=""
PROJECT_NUMBER=""
PROJECT_ID=""
STATUS_FIELD=""
declare -A STATUS_OPTIONS=()

detect_repo() {
  if [[ -n "$REPO" ]]; then return; fi
  local remote_url
  remote_url=$(git remote get-url origin 2>/dev/null || echo "")
  # Override: dotfiles repo → deneb
  if [[ "$remote_url" == *"phoebe.fi"*"dotfiles"* ]]; then
    REPO="elahti/deneb"
    return
  fi
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner) || {
    echo "detect_repo: failed to detect repository (is gh authenticated?)" >&2; exit 1;
  }
  [[ -n "$REPO" ]] || { echo "detect_repo: no repository found" >&2; exit 1; }
}

detect_project() {
  if [[ -n "$PROJECT_ID" ]]; then return; fi
  detect_repo
  local owner="${REPO%%/*}"
  # Picks the first project for the owner
  local project_json
  project_json=$(gh project list --owner "$owner" --format json --limit 1)
  PROJECT_NUMBER=$(echo "$project_json" | jq -r '.projects[0].number')
  PROJECT_ID=$(echo "$project_json" | jq -r '.projects[0].id')
  [[ "$PROJECT_NUMBER" != "null" && -n "$PROJECT_NUMBER" ]] || {
    echo "detect_project: no projects found for owner '$owner'" >&2; exit 1;
  }
}

detect_status_field() {
  if [[ -n "$STATUS_FIELD" ]]; then return; fi
  detect_project
  local owner="${REPO%%/*}"
  local fields_json
  fields_json=$(gh project field-list "$PROJECT_NUMBER" --owner "$owner" --format json)
  STATUS_FIELD=$(echo "$fields_json" | jq -r '.fields[] | select(.name == "Status") | .id')
  [[ -n "$STATUS_FIELD" ]] || {
    echo "detect_status_field: no Status field found in project $PROJECT_NUMBER" >&2; exit 1;
  }
  # Populate STATUS_OPTIONS from the Status field's single-select options
  while IFS= read -r line; do
    local name id
    name=$(echo "$line" | jq -r '.name')
    id=$(echo "$line" | jq -r '.id')
    local key
    key=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    STATUS_OPTIONS["$key"]="$id"
  done < <(echo "$fields_json" | jq -c '.fields[] | select(.name == "Status") | .options[]')
}

init() {
  detect_repo
  detect_project
  detect_status_field
}

graphql() {
  local query="$1"; shift
  gh api graphql -f query="$query" "$@"
}

# --- Issue operations ---

cmd_issue_view() {
  gh issue view "$1" --repo "$REPO" "${@:2}"
}

cmd_issue_create() {
  local title="" body="" label=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --title) title="$2"; shift 2 ;;
      --body) body="$2"; shift 2 ;;
      --label) label="$2"; shift 2 ;;
      *) echo "issue-create: unknown arg: $1" >&2; exit 1 ;;
    esac
  done
  [[ -n "$title" ]] || { echo "issue-create: --title required" >&2; exit 1; }
  [[ -n "$body" ]] || { echo "issue-create: --body required" >&2; exit 1; }
  local -a cmd=(gh issue create --repo "$REPO" --title "$title" --body "$body")
  [[ -n "$label" ]] && cmd+=(--label "$label")
  "${cmd[@]}"
}

cmd_issue_edit() {
  local number="$1"; shift
  local body=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --body) body="$2"; shift 2 ;;
      *) echo "issue-edit: unknown arg: $1" >&2; exit 1 ;;
    esac
  done
  [[ -n "$body" ]] || { echo "issue-edit: --body required" >&2; exit 1; }
  gh issue edit "$number" --repo "$REPO" --body "$body"
}

cmd_issue_close() {
  gh issue close "$1" --repo "$REPO" --reason completed
}

# --- GraphQL queries ---

cmd_get_project_item() {
  graphql '
    query($id: ID!) {
      node(id: $id) {
        ... on Issue {
          projectItems(first: 10) { nodes { id project { id } } }
        }
      }
    }' -f id="$1" \
    --jq ".data.node.projectItems.nodes[] | select(.project.id == \"$PROJECT_ID\") | .id"
}

cmd_get_project_fields() {
  detect_project
  local owner="${REPO%%/*}"
  gh project field-list "$PROJECT_NUMBER" --owner "$owner" --format json \
    | jq '{
        start: (.fields[] | select(.name == "Start date") | .id),
        end: (.fields[] | select(.name == "End date") | .id)
      }'
}

cmd_get_start_date() {
  graphql '
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
    }' -f id="$1" \
    --jq ".data.node.projectItems.nodes[] | select(.project.id == \"$PROJECT_ID\") | {item_id: .id, date: (.fieldValueByName.date // null)}"
}

cmd_get_parent() {
  graphql '
    query($id: ID!) {
      node(id: $id) {
        ... on Issue { parent { id number title state } }
      }
    }' -f id="$1" --jq '.data.node.parent'
}

cmd_count_open_sub_issues() {
  graphql '
    query($id: ID!) {
      node(id: $id) {
        ... on Issue {
          subIssues(first: 50) { nodes { state } }
        }
      }
    }' -f id="$1" \
    --jq '[.data.node.subIssues.nodes[] | select(.state == "OPEN")] | length'
}

cmd_table_set_status() {
  local parent_number="$1" sub_number="$2" new_status="$3"
  local body
  body=$(gh issue view "$parent_number" --repo "$REPO" --json body --jq '.body')
  local updated
  updated=$(awk -v n="$sub_number" -v s="$new_status" '
    BEGIN { pat1 = "/issues/" n ")"; pat2 = "#" n ")" }
    (index($0, pat1) > 0 || index($0, pat2) > 0) {
      if (match($0, /\| [^|]* \|$/))
        $0 = substr($0, 1, RSTART - 1) "| " s " |"
    }
    { print }
  ' <<< "$body")
  gh issue edit "$parent_number" --repo "$REPO" --body "$updated"
}

# --- GraphQL mutations ---

cmd_add_to_project() {
  graphql '
    mutation($project: ID!, $content: ID!) {
      addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
        item { id }
      }
    }' -f project="$PROJECT_ID" -f content="$1" \
    --jq '.data.addProjectV2ItemById.item.id'
}

cmd_set_status() {
  local item="$1" status_key="$2"
  local option_id="${STATUS_OPTIONS[$status_key]:-}"
  [[ -n "$option_id" ]] || { echo "set-status: unknown status '$status_key' (valid: ${!STATUS_OPTIONS[*]})" >&2; exit 1; }
  graphql '
    mutation($project: ID!, $item: ID!, $field: ID!, $value: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $project, itemId: $item,
        fieldId: $field, value: {singleSelectOptionId: $value}
      }) { projectV2Item { id } }
    }' -f project="$PROJECT_ID" -f item="$item" \
       -f field="$STATUS_FIELD" -f value="$option_id"
}

cmd_set_date() {
  local item="$1" field="$2"
  local date
  date=$(date +%Y-%m-%d)
  graphql '
    mutation($project: ID!, $item: ID!, $field: ID!, $date: Date!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $project, itemId: $item,
        fieldId: $field, value: {date: $date}
      }) { projectV2Item { id } }
    }' -f project="$PROJECT_ID" -f item="$item" \
       -f field="$field" -f date="$date"
}

# --- Main dispatch ---

init

case "${1:-}" in
  issue-view)         shift; cmd_issue_view "$@" ;;
  issue-create)       shift; cmd_issue_create "$@" ;;
  issue-edit)         shift; cmd_issue_edit "$@" ;;
  issue-close)        shift; cmd_issue_close "$@" ;;
  get-project-item)   shift; cmd_get_project_item "$@" ;;
  get-project-fields) shift; cmd_get_project_fields "$@" ;;
  get-start-date)     shift; cmd_get_start_date "$@" ;;
  add-to-project)     shift; cmd_add_to_project "$@" ;;
  set-status)         shift; cmd_set_status "$@" ;;
  set-date)           shift; cmd_set_date "$@" ;;
  get-parent)         shift; cmd_get_parent "$@" ;;
  count-open-sub-issues) shift; cmd_count_open_sub_issues "$@" ;;
  table-set-status)   shift; cmd_table_set_status "$@" ;;
  *)
    echo "Usage: $0 <subcommand> [args...]" >&2
    echo "Run '$0 <subcommand> --help' for subcommand help" >&2
    exit 1
    ;;
esac
