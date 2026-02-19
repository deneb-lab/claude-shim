# Port Skills from Deneb to Marketplace

## Context

Skills and supporting shell scripts currently live in the `elahti/deneb` repo under `.claude/skills/` and `scripts/`. This design covers moving them into the `elahti/claude-shim` marketplace monorepo as self-contained plugins, adding auto-detection for repo/project, adding per-plugin versioning, and removing the originals from deneb.

## Directory Structure

```
claude-shim/
├── .claude-plugin/
│   └── marketplace.json
├── CLAUDE.md
├── plugins/
│   ├── github-project-tools/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── scripts/
│   │   │   └── github-projects.sh
│   │   └── skills/
│   │       ├── github-add-issue/
│   │       │   └── SKILL.md
│   │       └── github-implement-issue/
│   │           └── SKILL.md
│   └── trivy-audit/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── scripts/
│       │   ├── github-projects.sh          (duplicate, self-contained)
│       │   ├── trivy-audit-gather.sh
│       │   └── trivy-audit-gh.sh
│       └── skills/
│           └── trivy-audit-report/
│               ├── SKILL.md
│               └── prompts/
│                   ├── config-auditor.md
│                   ├── cve-analyst.md
│                   ├── staleness-researcher.md
│                   └── report-writer.md
└── README.md
```

Key changes from current state:
- Plugin `trivy-audit-report` renamed to `trivy-audit` (skill stays `trivy-audit:report`)
- Scripts bundled into each plugin's `scripts/` directory
- `github-projects.sh` duplicated in both plugins (each self-contained)

## Script Modifications

### github-projects.sh

Remove hardcoded `REPO`, `PROJECT_ID`, `STATUS_FIELD`, and `STATUS_OPTIONS`. Replace with auto-detection:

1. **Repo detection:** `gh repo view --json nameWithOwner -q .nameWithOwner` with hardcoded override: if the git remote URL matches `phoebe.fi.*dotfiles`, use `elahti/deneb` instead.

2. **Project detection:** `gh project list --owner <owner> --format json --limit 1` to discover the project ID. Status field and option IDs discovered via `gh project field-list`.

3. **Lazy initialization:** Detect once per script invocation, stored in global variables.

### trivy-audit-gather.sh

No changes. `SERVER="esko@phoebe.fi"` stays hardcoded.

### trivy-audit-gh.sh

Same auto-detect pattern as github-projects.sh for REPO.

## SKILL.md Updates

1. **trivy-audit SKILL.md:** Update prompt file paths from `.claude/skills/trivy-audit-report/prompts/` to plugin-relative paths.
2. **github-add-issue SKILL.md:** Update default repo reference from hardcoded `elahti/deneb` to "the current repository (auto-detected)".
3. **All skill MDs:** Keep `scripts/github-projects.sh` references as-is (plugin-relative paths).

## Versioning

- **Per-plugin semver:** Each plugin has its own version in `plugin.json`.
- **marketplace.json** mirrors each plugin's version and has its own `metadata.version`.
- **Git tags:** `plugin-name/vMAJOR.MINOR.PATCH` (e.g., `github-project-tools/v0.2.0`).
- **Initial versions:**
  - `github-project-tools` → `0.2.0` (scripts bundled, auto-detect added)
  - `trivy-audit` → `0.1.0` (new plugin name)
  - Marketplace metadata → `0.2.0`
- No automation, no release notes file. Manual process.

## CLAUDE.md

Add a `CLAUDE.md` at the repo root documenting:
- Repo purpose and structure
- Plugin creation/update workflow
- SKILL.md frontmatter and naming conventions
- Script conventions (auto-detect, no hardcoded repos, bundled per-plugin)
- Versioning workflow (semver, bump plugin.json + marketplace.json, git tag)
- Shared script duplication policy
- Deneb-specific overrides (dotfiles→deneb, phoebe.fi)

## Marketplace Metadata Updates

- `marketplace.json`: Rename `trivy-audit-report` → `trivy-audit`, update source path, bump versions.
- `plugin.json` (trivy): Rename to `trivy-audit`, bump version.
- `README.md`: Update plugin name, remove external dependency notes, update directory tree.

## Deneb Cleanup

- Delete `.claude/skills/` entirely (3 skill directories with all contents).
- Delete `scripts/` entirely (3 shell scripts).
- Commit with message referencing the marketplace migration.
