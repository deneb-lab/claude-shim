# Remove Draft PR Creation from start-implementation

## Summary

Remove the draft PR creation step from the `start-implementation` skill and the `pr-create-draft` subcommand from `github-projects.sh`. Draft PR creation during implementation start is premature — the branch may not have commits yet, and creating an empty draft PR adds noise.

## Changes

### 1. SKILL.md (`plugins/github-project-tools/skills/start-implementation/SKILL.md`)
- Remove "creates draft PR" from the `description` frontmatter
- Remove "optionally create a draft PR" from the intro sentence
- Delete Phase 3 step 5 (the draft PR prompt). Renumber step 6 to step 5.

### 2. Script (`plugins/github-project-tools/scripts/github-projects.sh`)
- Remove `pr-create-draft` from usage/help comment
- Delete `cmd_pr_create_draft` function
- Remove `pr-create-draft)` case from dispatch

### 3. Version bump
- `plugin.json`: `0.7.0` -> `0.8.0`
- `marketplace.json`: github-project-tools version and metadata version to `0.8.0`
