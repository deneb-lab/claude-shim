# Claude Shim Marketplace

Claude Code plugin marketplace monorepo. Plugins are self-contained directories under `plugins/`.

## Repository Structure

- `.claude-plugin/marketplace.json` — Plugin catalog (lists all plugins with versions)
- `plugins/<name>/.claude-plugin/plugin.json` — Plugin metadata
- `plugins/<name>/skills/<skill-name>/SKILL.md` — Skill definitions
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
4. Update `README.md`

## Skill Conventions

- **Frontmatter:** Every SKILL.md starts with YAML frontmatter: `name` and `description`
- **Naming:** `plugin-prefix:action-name` (e.g., `github:add-issue`, `trivy-audit:report`)
- **Paths:** Reference scripts as `scripts/<name>.sh` (plugin-relative)
- **Prompts:** Sub-agent prompts go in `prompts/` subdirectory next to SKILL.md

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
- **Bump process:**
  1. Update `version` in `plugins/<name>/.claude-plugin/plugin.json`
  2. Update the matching `version` in `.claude-plugin/marketplace.json` plugins array
  3. Bump `metadata.version` in marketplace.json if the catalog changed
  4. Commit: `"Release <plugin-name> v<version>: <summary>"`
  5. Tag: `git tag <plugin-name>/v<version>`
- **No release notes file.** Use git tags and commit messages.

## Commit Conventions

- Plugin changes: `"feat(<plugin-name>): <description>"` or `"fix(<plugin-name>): <description>"`
- Marketplace metadata: `"chore: <description>"`
- Releases: `"Release <plugin-name> v<version>: <summary>"`
