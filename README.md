# Claude Shim Marketplace

Claude Code plugins for project management, security auditing, and automation.

## Installation

Add this marketplace to Claude Code:

```bash
/plugin marketplace add elahti/claude-shim
```

## Available Plugins

### GitHub Project Tools

**Description:** GitHub issue creation and implementation with project board lifecycle management

**Install:**
```bash
/plugin install github-project-tools@claude-shim-marketplace
```

**Skills:**
- `github-projects:add-issue` — Create a GitHub issue from conversation context and add it to the project board
- `github-projects:start-implementation` — Start implementing a GitHub issue (assigns, sets dates/status, creates draft PR, presents context)
- `github-projects:end-implementation` — Close a GitHub issue (sets end date, done status, closes issue, updates parent lifecycle)

---

### Trivy Audit

**Description:** Trivy security audit coordinator — spawns an agent team for CVE analysis, version staleness research, config audits, and GitHub issue creation

**Install:**
```bash
/plugin install trivy-audit@claude-shim-marketplace
```

**Skills:**
- `trivy-audit:report` — Run a comprehensive security audit using an agent team with 4 specialized analysts

## Marketplace Structure

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
│   │       ├── github-projects-add-issue/
│   │       │   └── SKILL.md
│   │       ├── github-projects-start-implementation/
│   │       │   └── SKILL.md
│   │       └── github-projects-end-implementation/
│   │           └── SKILL.md
│   └── trivy-audit/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── scripts/
│       │   ├── github-projects.sh
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

## Versioning

Each plugin follows semantic versioning independently. Plugin versions are tracked in both `plugin.json` and `marketplace.json`. Git tags use the format `plugin-name/vX.Y.Z`.

## License

MIT
