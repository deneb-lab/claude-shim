# Claude Shim Marketplace

Claude Code plugins for project management and automation.

## Installation

Install all plugins from this marketplace:

```
/plugin marketplace add elahti/claude-shim
```

Or install a single plugin:

```
/plugin add elahti/claude-shim/github-project-tools
/plugin add elahti/claude-shim/quality-check-hook
```

## Available Plugins

### github-project-tools (v0.10.2)

GitHub issue creation and implementation with project board lifecycle management.

**Skills:**

| Skill | Description |
|---|---|
| `github-project-tools:add-issue` | Create a GitHub issue from conversation context and add it to the project board |
| `github-project-tools:start-implementation` | Start implementing a GitHub issue -- assigns, sets dates/status, and presents issue context |
| `github-project-tools:end-implementation` | Close a GitHub issue -- sets end date, done status, closes issue, updates parent lifecycle |

The plugin auto-detects the current GitHub repository and project board. All GitHub operations go through a bundled wrapper script (`gh` CLI required).

### quality-check-hook (v0.5.1)

Config-driven quality checks for edited files -- formatting, linting, and auto-fix via PostToolUse hooks.

The hook runs automatically whenever Claude edits a file. It matches the file path against patterns in `.claude-shim.json` and runs the configured commands (formatters, linters, fixers) in order. On failure, Claude is blocked from proceeding until the issue is resolved.

**Skills:**

| Skill | Description |
|---|---|
| `quality-check-hook:setup-quality-check-hook` | Set up or modify `.claude-shim.json` quality checks for the current repository |

**Requires:** [uv](https://docs.astral.sh/uv/) on PATH. The hook fails closed if `uv` is unavailable.

#### Setup

Run the setup skill to auto-detect your project's tooling and generate a config, or create `.claude-shim.json` manually in your repository root:

```json
{
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
  "quality-checks": {
    "include": [
      {
        "pattern": "**/*.{js,jsx,ts,tsx}",
        "commands": [
          "npx prettier --write",
          "npx eslint --fix",
          "npx eslint"
        ]
      }
    ],
    "exclude": [
      "dist"
    ]
  }
}
```

**How it works:**

- Commands run in order per file: format first, then auto-fix, then lint-check
- Each command gets the edited file path appended as the last argument
- Execution stops on the first failing command (exit code 2 blocks Claude)
- Gitignored files are automatically skipped -- no need to add them to the exclude list
- Each command has a 30-second timeout

The setup skill auto-detects Biome, Prettier, ESLint, Ruff, Ansible, yamllint, ShellCheck, and jq.

## Marketplace Structure

```
.claude-plugin/
  marketplace.json          # Plugin catalog
plugins/
  github-project-tools/
    .claude-plugin/
      plugin.json           # Plugin metadata and version
    scripts/
      github-projects.sh    # GitHub CLI wrapper
    skills/
      add-issue/
        SKILL.md
      start-implementation/
        SKILL.md
      end-implementation/
        SKILL.md
  quality-check-hook/
    .claude-plugin/
      plugin.json
    hook/                   # Python hook (managed by uv)
    hooks/
      hooks.json            # PostToolUse hook registration
    scripts/
      setup-quality-check-hook.sh
    skills/
      setup-quality-check-hook/
        SKILL.md
```

## Versioning

Each plugin follows independent semver. Versions are tracked in both the plugin's `plugin.json` and the top-level `marketplace.json`.

Releases are tagged as `<plugin-name>/v<version>` (e.g., `github-project-tools/v0.10.2`).

## License

MIT
