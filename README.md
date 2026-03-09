# Claude Shim Marketplace

Collection of quality-of-life Claude Code hooks. Battle-tested and used in commercial projects.

## Installation

Register the marketplace in Claude Code:

```
/plugin marketplace add deneb-lab/claude-shim-marketplace
```

Install plugins:

```
/plugin add deneb-lab/claude-shim-marketplace/quality-check-hook
/plugin add deneb-lab/claude-shim-marketplace/github-project-tools
```

## Available Plugins

### quality-check-hook

Config-driven quality checks for edited files. Runs automatically when Claude edits a file. Commands from all matching patterns run in order, stopping on first failure. Gitignored files are skipped and they don't need to be configured in `exclude` list.

**Installation:**

Requires [uv](https://github.com/astral-sh/uv) to be installed.

Run `/quality-check-hook:setup-quality-check-hook` to auto-detect your project's tooling and generate a config. Also see claude-shim's own [.claude-shim.json](https://github.com/deneb-lab/claude-shim/blob/main/.claude-shim.json).

**Example:**

In the example below editing `src/app.ts` runs all three commands: `prettier --write` → `eslint --fix` → `tsc --noEmit`.

```json
{
  "quality-checks": {
    "include": [
      {
        "pattern": "**/*.{js,ts}",
        "commands": [
          "npx prettier --write",
          "npx eslint --fix"
        ]
      },
      {
        "pattern": "**/*.ts",
        "commands": [
          "npx tsc --noEmit"
        ]
      }
    ],
    "exclude": [
      "dist"
    ]
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
| `github-project-tools:start-implementing-issue` | Start implementing a GitHub issue — assigns, sets dates/status, and presents issue context |
| `github-project-tools:end-implementing-issue` | Close a GitHub issue — sets end date, done status, closes issue, updates parent lifecycle |
| `github-project-tools:mass-update-issues` | Update an issue and all its sub-issues — sets status, dates, and close state on the project board |
| `github-project-tools:setup-github-project-tools` | Set up or modify github-project-tools configuration in `.claude-shim.json` |

## License

MIT
