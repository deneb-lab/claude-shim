# Claude Shim Marketplace

Collection of quality-of-life Claude Code hooks.

## Installation

Register the marketplace in Claude Code:

```
/plugin marketplace add elahti/claude-shim
```

Install plugins:

```
/plugin add elahti/claude-shim/quality-check-hook
/plugin add elahti/claude-shim/github-project-tools
```

## Available Plugins

### quality-check-hook

Config-driven quality checks for edited files. Runs automatically when Claude edits a file. Commands from all matching patterns run in order, stopping on first failure. Gitignored files are skipped and they don't need to be configured in `exclude` list.

**Installation:**

Run `/quality-check-hook:setup-quality-check-hook` to auto-detect your project's tooling and generate a config. Also see claude-shim's own [.claude-shim.json](https://github.com/elahti/claude-shim/blob/main/.claude-shim.json).

**Example:**

In the example below editing `src/app.ts` runs all three commands: `prettier --write` → `eslint --fix` → `tsc --noEmit`.

```json
{
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
  "quality-checks": {
    "include": [
      { "pattern": "**/*.{js,ts}", "commands": ["npx prettier --write", "npx eslint --fix"] },
      { "pattern": "**/*.ts",      "commands": ["npx tsc --noEmit"] }
    ],
    "exclude": ["dist"]
  }
}
```

### github-project-tools

GitHub issue creation and implementation with project board lifecycle management. Requires `gh` CLI.

The plugin auto-detects the current GitHub repository and project board.

**Skills:**

| Skill | Description |
|---|---|
| `github-project-tools:add-issue` | Create a GitHub issue from conversation context and add it to the project board |
| `github-project-tools:start-implementation` | Start implementing a GitHub issue — assigns, sets dates/status, and presents issue context |
| `github-project-tools:end-implementation` | Close a GitHub issue — sets end date, done status, closes issue, updates parent lifecycle |

## License

MIT
