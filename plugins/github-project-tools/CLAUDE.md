# GitHub Project Tools Plugin

## Architecture

- `scripts/github-projects.sh` — Core shell script handling all GitHub API operations
- `skills/` — Three skills: `add-issue`, `start-implementation`, `end-implementation`
- Each skill has a `prompts/` directory with prompt files

## Shared Prompts

`preflight.md` and `conventions.md` are duplicated across all 3 skills. `setup.md` and `parse-issue-arg.md` are shared between `start-implementation` and `end-implementation`. When editing, update ALL copies and verify with `git diff`. CI enforces sync.

## Development

No build step — pure shell + markdown. Validate with:

```bash
shellcheck plugins/github-project-tools/scripts/github-projects.sh
```
