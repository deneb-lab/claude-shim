# Design: Consolidate shared logic across github-project-tools skills

**Issue:** #7
**Parent:** elahti/deneb#31
**Date:** 2026-02-20

## Problem

The three skills in `github-project-tools` (`add-issue`, `start-implementation`, `end-implementation`) have significant duplicated prose in their SKILL.md files. When one skill is updated, the others drift. `add-issue` also lacks preflight checks that the other two skills have.

## Design

### Shared prompts directory

Create `plugins/github-project-tools/prompts/` with four markdown snippets:

```
plugins/github-project-tools/
  prompts/
    preflight.md        # Phase 0: find script + run preflight
    setup.md            # Phase 1: get-project-fields, save field IDs
    parse-issue-arg.md  # Parse issue number vs full URL, set REPO_OVERRIDE
    conventions.md      # Important Notes footer (all 5 rules)
```

### Snippet contents

**`preflight.md`** — The 3-step preflight block:
1. Find the bundled script at `~/.claude/plugins/**/github-project-tools/scripts/github-projects.sh`
2. Run `scripts/github-projects.sh preflight`
3. If preflight fails, stop and show the error message

Used by: all 3 skills (adds missing preflight to `add-issue`).

**`setup.md`** — The project setup block:
1. Call `scripts/github-projects.sh get-project-fields`
2. Save `START_FIELD` and `END_FIELD` from the JSON output
3. Note: if no project found, skip all project operations in later phases
4. Note: `set-status` accepts literal `todo`/`in-progress`/`done`

Used by: `start-implementation`, `end-implementation`.

**`parse-issue-arg.md`** — The argument parsing block:
1. Parse plain number (`42`) vs full URL (`https://github.com/owner/repo/issues/42`)
2. Extract issue number from either format
3. If full URL, extract `owner/repo` as `REPO_OVERRIDE`
4. When `REPO_OVERRIDE` is set, prepend `--repo $REPO_OVERRIDE` to every script invocation

Used by: `start-implementation`, `end-implementation`.

**`conventions.md`** — The Important Notes footer (all 5 rules):
1. All bash commands must start with the script being invoked (no `VAR=$(scripts/...)`)
2. JSON processing: extract values in-context (no `echo | jq`)
3. All GitHub operations go through `scripts/github-projects.sh`
4. Date field IDs are looked up at runtime via `get-project-fields`
5. Project is optional: skip project ops but still do issue ops

Used by: all 3 skills.

### How skills reference snippets

Each SKILL.md replaces its duplicated block with a reference:

```markdown
## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).
```

### Script change: `issue-view-full` subcommand

Add an `issue-view-full <number>` subcommand to `github-projects.sh` that is equivalent to:

```bash
gh issue view <number> --repo "$REPO" --json id,number,title,body,state
```

Every skill that fetches issue details uses exactly this field set. The subcommand avoids repeating `--json id,number,title,body,state` in every skill.

### Changes per skill

**`add-issue`:**
- Add Phase 0 referencing `prompts/preflight.md` (new)
- Replace Important Notes with reference to `prompts/conventions.md`

**`start-implementation`:**
- Replace Phase 0 with reference to `prompts/preflight.md`
- Replace Phase 1 with reference to `prompts/setup.md`
- Replace URL-parsing block in Phase 2 with reference to `prompts/parse-issue-arg.md`
- Replace `issue-view <n> --json id,number,title,body,state` with `issue-view-full <n>`
- Replace Important Notes with reference to `prompts/conventions.md`

**`end-implementation`:**
- Replace Phase 0 with reference to `prompts/preflight.md`
- Replace Phase 1 with reference to `prompts/setup.md`
- Replace URL-parsing block in Phase 2 with reference to `prompts/parse-issue-arg.md`
- Replace `issue-view <n> --json id,number,title,body,state` with `issue-view-full <n>`
- Replace Important Notes with reference to `prompts/conventions.md`

## Not changing

- Parent lifecycle logic between start/end (asymmetric by design)
- `get-project-item` vs `get-start-date` (different callers, different return shapes)
- `set-status` vs `set-date` (incompatible GraphQL value types)
