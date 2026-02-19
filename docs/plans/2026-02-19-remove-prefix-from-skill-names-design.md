# Design: Remove Prefix from Skill Names

## Goal

Decouple skill identity from directory and frontmatter naming. Directories and frontmatter use bare action names. Cross-references use the fully-qualified `plugin-name:skill-name` form.

## Changes

### 1. Directory Renames

| Current | New |
|---|---|
| `plugins/github-project-tools/skills/github-projects-add-issue/` | `add-issue/` |
| `plugins/github-project-tools/skills/github-projects-start-implementation/` | `start-implementation/` |
| `plugins/github-project-tools/skills/github-projects-end-implementation/` | `end-implementation/` |
| `plugins/trivy-audit/skills/trivy-audit-report/` | `report/` |

### 2. Frontmatter Edits

Strip the `prefix:` from the `name` field in each SKILL.md:

- `github-projects:add-issue` -> `add-issue`
- `github-projects:start-implementation` -> `start-implementation`
- `github-projects:end-implementation` -> `end-implementation`
- `trivy-audit:report` -> `report`

### 3. Cross-Reference Updates

In `start-implementation/SKILL.md`, update two references from `github-projects:end-implementation` to `github-project-tools:end-implementation` (using plugin name as qualifier).

### 4. Documentation Updates

- **README.md:** Update directory tree and skill name references.
- **CLAUDE.md:** Update naming convention from `plugin-prefix:action-name` to bare names.

### 5. Version Bumps

- `github-project-tools`: 0.3.0 -> 0.4.0
- `trivy-audit`: 0.1.0 -> 0.2.0
- `marketplace.json` metadata: 0.3.0 -> 0.4.0
