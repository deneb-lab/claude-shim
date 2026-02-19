# Port Skills from Deneb — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate skills and scripts from `elahti/deneb` into `elahti/claude-shim` marketplace as self-contained plugins with auto-detection and per-plugin versioning, then remove originals from deneb.

**Architecture:** Monorepo marketplace where each plugin bundles its own scripts. Shell scripts auto-detect the current GitHub repo and project via `gh` CLI instead of hardcoding values. Shared scripts are duplicated across plugins for independence.

**Tech Stack:** Bash, `gh` CLI, `jq`, Git

**Source repos:**
- Marketplace: `/workspace/claude-shim__worktrees/feat-port-skills-from-deneb` (branch: `feat/port-skills-from-deneb`)
- Deneb: `/workspace/deneb` (will receive a cleanup commit)

---

### Task 1: Rename trivy-audit-report plugin to trivy-audit

**Files:**
- Rename: `plugins/trivy-audit-report/` → `plugins/trivy-audit/`

**Step 1: Rename the directory**

```bash
cd /workspace/claude-shim__worktrees/feat-port-skills-from-deneb
git mv plugins/trivy-audit-report plugins/trivy-audit
```

**Step 2: Verify the rename**

```bash
ls plugins/trivy-audit/skills/trivy-audit-report/SKILL.md
ls plugins/trivy-audit/.claude-plugin/plugin.json
```

Expected: Both files exist. The inner `skills/trivy-audit-report/` directory keeps its name (skill name stays `trivy-audit:report`).

**Step 3: Commit**

```bash
git add -A && git commit -m "Rename trivy-audit-report plugin to trivy-audit"
```

---

### Task 2: Bundle scripts into github-project-tools plugin

**Files:**
- Create: `plugins/github-project-tools/scripts/github-projects.sh`

**Step 1: Create the scripts directory and copy the script**

```bash
mkdir -p plugins/github-project-tools/scripts
cp /workspace/deneb/scripts/github-projects.sh plugins/github-project-tools/scripts/
chmod +x plugins/github-project-tools/scripts/github-projects.sh
```

**Step 2: Rewrite the script header to use auto-detection**

Replace the hardcoded constants (lines 23–31 of the original):

```bash
REPO="elahti/deneb"
PROJECT_ID="PVT_kwHOAC8LI84BPPkb"
STATUS_FIELD="PVTSSF_lAHOAC8LI84BPPkbzg9tWIc"

declare -A STATUS_OPTIONS=(
  [todo]="f75ad846"
  [in-progress]="47fc9ee4"
  [done]="98236657"
)
```

With lazy-init auto-detection functions:

```bash
# --- Auto-detection (lazy init) ---

REPO=""
PROJECT_NUMBER=""
PROJECT_ID=""
STATUS_FIELD=""
declare -A STATUS_OPTIONS=()

detect_repo() {
  if [[ -n "$REPO" ]]; then return; fi
  local remote_url
  remote_url=$(git remote get-url origin 2>/dev/null || echo "")
  # Override: dotfiles repo → deneb
  if [[ "$remote_url" == *"phoebe.fi"*"dotfiles"* ]]; then
    REPO="elahti/deneb"
    return
  fi
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
}

detect_project() {
  if [[ -n "$PROJECT_ID" ]]; then return; fi
  detect_repo
  local owner="${REPO%%/*}"
  local project_json
  project_json=$(gh project list --owner "$owner" --format json --limit 1)
  PROJECT_NUMBER=$(echo "$project_json" | jq -r '.projects[0].number')
  PROJECT_ID=$(echo "$project_json" | jq -r '.projects[0].id')
}

detect_status_field() {
  if [[ -n "$STATUS_FIELD" ]]; then return; fi
  detect_project
  local owner="${REPO%%/*}"
  local fields_json
  fields_json=$(gh project field-list "$PROJECT_NUMBER" --owner "$owner" --format json)
  STATUS_FIELD=$(echo "$fields_json" | jq -r '.fields[] | select(.name == "Status") | .id')
  # Populate STATUS_OPTIONS from the Status field's single-select options
  local options_json
  options_json=$(echo "$fields_json" | jq -r '.fields[] | select(.name == "Status") | .options[]')
  while IFS= read -r line; do
    local name id
    name=$(echo "$line" | jq -r '.name')
    id=$(echo "$line" | jq -r '.id')
    local key
    key=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    STATUS_OPTIONS["$key"]="$id"
  done < <(echo "$fields_json" | jq -c '.fields[] | select(.name == "Status") | .options[]')
}

init() {
  detect_repo
  detect_project
  detect_status_field
}
```

**Step 3: Update all command functions to call `init` lazily**

Add `init` call at the top of the main dispatch block (just before the `case` statement), so detection runs once per invocation:

```bash
# --- Main dispatch ---

init

case "${1:-}" in
```

**Step 4: Update `cmd_get_project_fields` to use auto-detected values**

Replace the hardcoded `gh project field-list 1 --owner elahti`:

```bash
cmd_get_project_fields() {
  detect_project
  local owner="${REPO%%/*}"
  gh project field-list "$PROJECT_NUMBER" --owner "$owner" --format json \
    | jq '{
        start: (.fields[] | select(.name == "Start date") | .id),
        end: (.fields[] | select(.name == "End date") | .id)
      }'
}
```

**Step 5: Update `cmd_set_status` to use auto-detected STATUS_OPTIONS**

No change needed — the function already reads from the `STATUS_OPTIONS` associative array, which is now populated dynamically.

**Step 6: Update all GraphQL functions using PROJECT_ID**

The functions `cmd_get_project_item`, `cmd_get_start_date`, `cmd_add_to_project`, `cmd_set_status`, `cmd_set_date` all reference `$PROJECT_ID`. No code changes needed — the variable is now set by `detect_project()` instead of hardcoded.

**Step 7: Verify syntax**

```bash
bash -n plugins/github-project-tools/scripts/github-projects.sh
```

Expected: No output (success).

**Step 8: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "Add github-projects.sh to github-project-tools with auto-detection

Replace hardcoded repo, project ID, and status field with runtime
auto-detection via gh CLI. Dotfiles repo overrides to elahti/deneb."
```

---

### Task 3: Bundle scripts into trivy-audit plugin

**Files:**
- Create: `plugins/trivy-audit/scripts/github-projects.sh` (duplicate from Task 2)
- Create: `plugins/trivy-audit/scripts/trivy-audit-gather.sh`
- Create: `plugins/trivy-audit/scripts/trivy-audit-gh.sh`

**Step 1: Create scripts directory and copy files**

```bash
mkdir -p plugins/trivy-audit/scripts
cp plugins/github-project-tools/scripts/github-projects.sh plugins/trivy-audit/scripts/
cp /workspace/deneb/scripts/trivy-audit-gather.sh plugins/trivy-audit/scripts/
cp /workspace/deneb/scripts/trivy-audit-gh.sh plugins/trivy-audit/scripts/
chmod +x plugins/trivy-audit/scripts/*.sh
```

**Step 2: Modify trivy-audit-gh.sh for auto-detection**

Replace the hardcoded `REPO="elahti/deneb"` (line 13) with the same `detect_repo` function used in github-projects.sh. Since trivy-audit-gh.sh is simpler (only needs REPO), add a minimal version:

```bash
# --- Auto-detection ---

REPO=""

detect_repo() {
  if [[ -n "$REPO" ]]; then return; fi
  local remote_url
  remote_url=$(git remote get-url origin 2>/dev/null || echo "")
  if [[ "$remote_url" == *"phoebe.fi"*"dotfiles"* ]]; then
    REPO="elahti/deneb"
    return
  fi
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
}

detect_repo
```

Place this block after `set -euo pipefail` and before the `graphql()` function.

**Step 3: trivy-audit-gather.sh — no changes**

The `SERVER="esko@phoebe.fi"` stays hardcoded per design.

**Step 4: Verify syntax of all scripts**

```bash
bash -n plugins/trivy-audit/scripts/github-projects.sh
bash -n plugins/trivy-audit/scripts/trivy-audit-gh.sh
bash -n plugins/trivy-audit/scripts/trivy-audit-gather.sh
```

Expected: No output (success) for all three.

**Step 5: Commit**

```bash
git add plugins/trivy-audit/scripts/
git commit -m "Add scripts to trivy-audit plugin

Bundle github-projects.sh (duplicate), trivy-audit-gather.sh, and
trivy-audit-gh.sh into the plugin. Add repo auto-detection to
trivy-audit-gh.sh."
```

---

### Task 4: Update SKILL.md files

**Files:**
- Modify: `plugins/trivy-audit/skills/trivy-audit-report/SKILL.md`
- Modify: `plugins/github-project-tools/skills/github-add-issue/SKILL.md`

**Step 1: Update trivy-audit SKILL.md prompt paths**

In `plugins/trivy-audit/skills/trivy-audit-report/SKILL.md`, replace all occurrences of `.claude/skills/trivy-audit-report/prompts/` with `prompts/` (4 occurrences on lines 41-43 and 73):

```
.claude/skills/trivy-audit-report/prompts/cve-analyst.md       → prompts/cve-analyst.md
.claude/skills/trivy-audit-report/prompts/staleness-researcher.md → prompts/staleness-researcher.md
.claude/skills/trivy-audit-report/prompts/config-auditor.md     → prompts/config-auditor.md
.claude/skills/trivy-audit-report/prompts/report-writer.md      → prompts/report-writer.md
```

**Step 2: Update github-add-issue SKILL.md default repo**

In `plugins/github-project-tools/skills/github-add-issue/SKILL.md`, replace:

```
The default repository is `elahti/deneb`. The user can specify a different repo.
The default project is https://github.com/users/elahti/projects/1.
```

With:

```
The default repository is the current git repository (auto-detected by the script). The user can specify a different repo.
The default project is auto-detected from the repo owner's GitHub projects.
```

**Step 3: Verify no stale path references remain**

```bash
grep -r "\.claude/skills/" plugins/
grep -r "elahti/deneb" plugins/
```

Expected: First command returns no results. Second command may return results in prompts (cve-analyst.md etc.) which reference Ansible roles in deneb — those are intentional and stay.

**Step 4: Commit**

```bash
git add plugins/trivy-audit/skills/trivy-audit-report/SKILL.md \
       plugins/github-project-tools/skills/github-add-issue/SKILL.md
git commit -m "Update skill paths and repo references for marketplace layout

Replace .claude/skills/ prompt paths with plugin-relative prompts/.
Replace hardcoded deneb repo references with auto-detected defaults."
```

---

### Task 5: Update marketplace metadata

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/trivy-audit/.claude-plugin/plugin.json`
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`

**Step 1: Update marketplace.json**

Replace the full content of `.claude-plugin/marketplace.json` with:

```json
{
  "name": "claude-shim-marketplace",
  "owner": {
    "name": "elahti"
  },
  "metadata": {
    "description": "Claude Code plugins for project management, security auditing, and automation",
    "version": "0.2.0"
  },
  "plugins": [
    {
      "name": "github-project-tools",
      "source": "./plugins/github-project-tools",
      "description": "GitHub issue creation and implementation with project board lifecycle management",
      "version": "0.2.0",
      "strict": true
    },
    {
      "name": "trivy-audit",
      "source": "./plugins/trivy-audit",
      "description": "Trivy security audit coordinator — CVE analysis, version staleness, config audits with agent team",
      "version": "0.1.0",
      "strict": true
    }
  ]
}
```

Changes: marketplace version `0.1.0` → `0.2.0`, `trivy-audit-report` → `trivy-audit`, source path updated, github-project-tools version `0.1.0` → `0.2.0`.

**Step 2: Update trivy-audit plugin.json**

Replace `plugins/trivy-audit/.claude-plugin/plugin.json`:

```json
{
  "name": "trivy-audit",
  "description": "Trivy security audit coordinator — CVE analysis, version staleness, config audits with agent team",
  "version": "0.1.0",
  "author": {
    "name": "elahti"
  },
  "repository": "https://github.com/elahti/claude-shim",
  "license": "MIT",
  "keywords": ["trivy", "security", "audit", "vulnerability", "kubernetes"]
}
```

Change: `name` from `trivy-audit-report` → `trivy-audit`.

**Step 3: Update github-project-tools plugin.json**

Update version in `plugins/github-project-tools/.claude-plugin/plugin.json`:

```json
{
  "name": "github-project-tools",
  "description": "GitHub issue creation and implementation with project board lifecycle management",
  "version": "0.2.0",
  "author": {
    "name": "elahti"
  },
  "repository": "https://github.com/elahti/claude-shim",
  "license": "MIT",
  "keywords": ["github", "issues", "project-management", "automation"]
}
```

Change: `version` from `0.1.0` → `0.2.0`.

**Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json \
       plugins/trivy-audit/.claude-plugin/plugin.json \
       plugins/github-project-tools/.claude-plugin/plugin.json
git commit -m "Update marketplace metadata: rename trivy plugin, bump versions

- Rename trivy-audit-report → trivy-audit in marketplace and plugin.json
- Bump github-project-tools to 0.2.0 (scripts bundled, auto-detect)
- Bump marketplace metadata to 0.2.0"
```

---

### Task 6: Update README.md

**Files:**
- Modify: `README.md`

**Step 1: Rewrite README.md**

Replace the full content with updated structure reflecting:
- Plugin name change (`trivy-audit` instead of `trivy-audit-report`)
- Remove "Dependencies" notes (scripts are now bundled)
- Updated directory tree showing `scripts/` directories
- Updated install commands

```markdown
# Claude Shim Marketplace

Claude Code plugins for project management, security auditing, and automation.

## Installation

Add this marketplace to Claude Code:

\`\`\`bash
/plugin marketplace add elahti/claude-shim
\`\`\`

## Available Plugins

### GitHub Project Tools

**Description:** GitHub issue creation and implementation with project board lifecycle management

**Install:**
\`\`\`bash
/plugin install github-project-tools@claude-shim-marketplace
\`\`\`

**Skills:**
- \`github:add-issue\` — Create a GitHub issue from conversation context and add it to the project board
- \`github:implement-issue\` — Implement a GitHub issue with full lifecycle management (dates, statuses, closing)

---

### Trivy Audit

**Description:** Trivy security audit coordinator — spawns an agent team for CVE analysis, version staleness research, config audits, and GitHub issue creation

**Install:**
\`\`\`bash
/plugin install trivy-audit@claude-shim-marketplace
\`\`\`

**Skills:**
- \`trivy-audit:report\` — Run a comprehensive security audit using an agent team with 4 specialized analysts

## Marketplace Structure

\`\`\`
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
\`\`\`

## Versioning

Each plugin follows semantic versioning independently. Plugin versions are tracked in both \`plugin.json\` and \`marketplace.json\`. Git tags use the format \`plugin-name/vX.Y.Z\`.

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "Update README for bundled scripts and trivy-audit rename"
```

---

### Task 7: Write CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Step 1: Write CLAUDE.md**

```markdown
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
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Add CLAUDE.md with marketplace development conventions"
```

---

### Task 8: Create git tags for initial versions

**Step 1: Create tags**

```bash
git tag github-project-tools/v0.2.0
git tag trivy-audit/v0.1.0
```

**Step 2: Verify tags**

```bash
git tag -l
```

Expected: Both tags listed pointing at HEAD (or appropriate commits).

Note: Do NOT push tags yet. The user will push when ready.

---

### Task 9: Deneb cleanup

**Working directory:** `/workspace/deneb`

**Files:**
- Delete: `.claude/skills/` (entire directory)
- Delete: `scripts/` (entire directory)

**Step 1: Delete skills and scripts from deneb**

```bash
cd /workspace/deneb
rm -rf .claude/skills scripts
```

**Step 2: Verify deletion**

```bash
ls .claude/skills 2>&1 || echo "skills directory removed"
ls scripts 2>&1 || echo "scripts directory removed"
```

Expected: Both commands print the "removed" message.

**Step 3: Commit in deneb**

```bash
git add -A
git commit -m "Remove skills and scripts — migrated to claude-shim marketplace

Skills and supporting scripts have been moved to the elahti/claude-shim
marketplace repo as self-contained plugins. Install via:
  /plugin marketplace add elahti/claude-shim"
```
