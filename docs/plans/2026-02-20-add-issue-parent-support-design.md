# Design: add-issue skill parent issue support

## Problem

The `add-issue` skill cannot set a parent issue. The `github-projects.sh` script lacks a `set-parent` subcommand. Users who specify a parent (e.g., "make #31 the parent") must resort to manual GraphQL calls.

## Scope

Two changes:

1. **`github-projects.sh`** — new `set-parent` subcommand
2. **`add-issue` SKILL.md** — new optional parent-linking phase

`start-implementation` and `end-implementation` already handle parent issues and need no changes.

## Design

### 1. `set-parent` subcommand

**Signature:**

```bash
scripts/github-projects.sh set-parent <child-node-id> <parent-node-id>
```

**Implementation:**

- New `cmd_set_parent()` function using the `addSubIssue` GraphQL mutation
- Needs `detect_repo` only (no project fields required)
- Returns the sub-issue node ID on success

**GraphQL mutation:**

```graphql
mutation($parent: ID!, $child: ID!) {
  addSubIssue(input: {issueId: $parent, subIssueId: $child}) {
    subIssue { id }
  }
}
```

**Dispatch entry:**

```bash
set-parent)  detect_repo; shift; cmd_set_parent "$@" ;;
```

### 2. `add-issue` skill — parent linking phase

**Current flow:** Phase 1 (Gather Context) -> Phase 2 (Create Issue) -> Phase 3 (Report)

**New flow:** Phase 1 (Gather Context) -> Phase 2 (Create Issue) -> Phase 2.5 (Link Parent) -> Phase 3 (Report)

**Phase 1 changes:** During context gathering, if the user mentioned a parent issue (e.g., `parent #31`, `make #31 the parent`, `parent https://github.com/owner/repo/issues/31`), extract the parent reference. Support both `#N` (same repo) and full GitHub URLs (cross-repo).

**Phase 2.5: Link Parent** (conditional — only runs if a parent was specified):

1. Resolve the parent node ID:
   - Same-repo (`#N`): `scripts/github-projects.sh issue-view <N> --json id --jq '.id'`
   - Cross-repo (full URL): `scripts/github-projects.sh issue-view <url> --json id --jq '.id'`
2. Call `scripts/github-projects.sh set-parent "$NODE_ID" "$PARENT_NODE_ID"`

**Phase 3 changes:** If a parent was linked, include in the report: "Linked as sub-issue of #N (title)."

## Approach rationale

- **Approach A (chosen):** Script takes node IDs only; skill handles resolution. Matches existing patterns — skills orchestrate, script wraps GraphQL.
- **Approach B (rejected):** Script resolves issue numbers internally. Over-engineers the script with argument parsing and cross-repo detection.
- **Approach C (rejected):** Separate `resolve-issue-id` helper. YAGNI — only `add-issue` needs this, and it already uses `issue-view` for ID resolution.
