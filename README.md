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
- `github:add-issue` — Create a GitHub issue from conversation context and add it to the project board
- `github:implement-issue` — Implement a GitHub issue with full lifecycle management (dates, statuses, closing)

**Dependencies:** Requires `scripts/github-projects.sh` in the target project.

---

### Trivy Audit Report

**Description:** Trivy security audit coordinator — spawns an agent team for CVE analysis, version staleness research, config audits, and GitHub issue creation

**Install:**
```bash
/plugin install trivy-audit-report@claude-shim-marketplace
```

**Skills:**
- `trivy-audit:report` — Run a comprehensive security audit using an agent team with 4 specialized analysts

**Dependencies:** Requires `scripts/trivy-audit-gather.sh`, `scripts/trivy-audit-gh.sh`, and `scripts/github-projects.sh` in the target project.

## Marketplace Structure

```
claude-shim/
├── .claude-plugin/
│   └── marketplace.json              # Plugin catalog
├── plugins/
│   ├── github-project-tools/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       ├── github-add-issue/
│   │       │   └── SKILL.md
│   │       └── github-implement-issue/
│   │           └── SKILL.md
│   └── trivy-audit-report/
│       ├── .claude-plugin/
│       │   └── plugin.json
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

Each plugin follows semantic versioning. The marketplace catalog (`marketplace.json`) references specific versions. Git tags use the format `plugin-name/vX.Y.Z`.

## License

MIT
