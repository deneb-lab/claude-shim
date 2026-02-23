# Claude Shim Marketplace

Claude Code plugin marketplace monorepo. Plugins are self-contained directories under `plugins/`.

## Repository Structure

- `.claude-plugin/marketplace.json` — Plugin catalog (lists all plugins with versions)
- `plugins/<name>/.claude-plugin/plugin.json` — Plugin metadata
- `plugins/<name>/skills/<skill-name>/SKILL.md` — Skill definitions
- `plugins/<name>/skills/<skill-name>/prompts/` — Prompt files referenced by the skill
- `plugins/<name>/scripts/` — Shell scripts bundled with the plugin

## Adding a New Plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json`:
   ```json
   {
     "name": "<name>",
     "description": "...",
     "version": "0.1.0",
     "author": { "name": "elahti" },
     "repository": "https://github.com/elahti/claude-shim",
     "license": "MIT",
     "keywords": [...]
   }
   ```
2. Create skills under `plugins/<name>/skills/<skill-name>/SKILL.md`
3. Add the plugin to `.claude-plugin/marketplace.json` in the `plugins` array

## Skill Conventions

- **Frontmatter:** Every SKILL.md starts with YAML frontmatter: `name` and `description`
- **Naming:** Bare action name in frontmatter and directory (e.g., `add-issue`, `report`). Cross-references use fully-qualified `plugin-name:skill-name` form (e.g., `github-project-tools:add-issue`).
- **Paths:** Reference scripts as `scripts/<name>.sh` (plugin-relative)
- **Prompts:** Prompt files go in `prompts/` subdirectory **inside each skill directory** (next to SKILL.md), never at the plugin root. Claude Code resolves relative paths from the skill directory, not the plugin root.
- **Shared prompts:** When multiple skills in a plugin use the same prompt file, each skill gets its own copy. When editing a shared prompt, **update every copy across all skills that use it.** Use `git diff` to verify all copies stay identical. Shared prompt groups:
  - `github-project-tools`: `preflight.md` and `conventions.md` are shared by all 3 skills; `setup.md` and `parse-issue-arg.md` are shared by `start-implementation` and `end-implementation`

## Script Conventions

- Scripts auto-detect the current GitHub repo via `gh repo view --json nameWithOwner`
- Scripts auto-detect the GitHub project via `gh project list --owner <owner>`
- Never hardcode repository names or project IDs (exception: documented overrides)
- Each plugin bundles its own scripts — if a script is shared, duplicate it
- All GitHub operations go through wrapper scripts, never call `gh` directly from skills

### Deneb-Specific Overrides

- **dotfiles → deneb:** When the git remote URL matches `phoebe.fi.*dotfiles`, scripts use `elahti/deneb` as the target repo
- **Trivy server:** `trivy-audit-gather.sh` connects to `esko@phoebe.fi` (hardcoded, deneb-specific)

## Versioning

- **Per-plugin semver:** Each plugin has its own version in `plugin.json`
- **marketplace.json** mirrors each plugin's version and has its own `metadata.version`
- **Version sync rule:** When bumping a plugin version, ALWAYS update BOTH files together:
  1. `plugins/<name>/.claude-plugin/plugin.json`
  2. The matching entry in `.claude-plugin/marketplace.json`
  These must never diverge. The `/plugin` view reads from marketplace.json.
- **Release process** (when cutting a release):
  1. Bump versions in both files (see rule above)
  2. Bump `metadata.version` in marketplace.json if the catalog changed
  3. Commit: `"Release <plugin-name> v<version>: <summary>"`
  4. Tag: `git tag <plugin-name>/v<version>`
  5. Push: `git push origin <plugin-name>/v<version>`
- **No release notes file.** Use git tags and commit messages.

## Commit Conventions

- Plugin changes: `"feat(<plugin-name>): <description>"` or `"fix(<plugin-name>): <description>"`
- Marketplace metadata: `"chore: <description>"`
- Releases: `"Release <plugin-name> v<version>: <summary>"`
