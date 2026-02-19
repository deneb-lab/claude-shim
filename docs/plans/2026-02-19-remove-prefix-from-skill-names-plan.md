# Remove Prefix from Skill Names — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename skill directories and frontmatter to use bare action names, update cross-references to fully-qualified `plugin-name:skill-name` form, and bump versions.

**Architecture:** Mechanical renaming via `git mv` for directories, in-place edits for frontmatter and cross-references, documentation updates, and version bumps.

**Tech Stack:** Git, shell, markdown

---

### Task 1: Rename github-project-tools skill directories

**Files:**
- Rename: `plugins/github-project-tools/skills/github-projects-add-issue/` → `plugins/github-project-tools/skills/add-issue/`
- Rename: `plugins/github-project-tools/skills/github-projects-start-implementation/` → `plugins/github-project-tools/skills/start-implementation/`
- Rename: `plugins/github-project-tools/skills/github-projects-end-implementation/` → `plugins/github-project-tools/skills/end-implementation/`

**Step 1: Rename directories with git mv**

```bash
git mv plugins/github-project-tools/skills/github-projects-add-issue plugins/github-project-tools/skills/add-issue
git mv plugins/github-project-tools/skills/github-projects-start-implementation plugins/github-project-tools/skills/start-implementation
git mv plugins/github-project-tools/skills/github-projects-end-implementation plugins/github-project-tools/skills/end-implementation
```

**Step 2: Verify renames**

Run: `ls plugins/github-project-tools/skills/`
Expected: `add-issue/  end-implementation/  start-implementation/`

**Step 3: Commit**

```bash
git add -A plugins/github-project-tools/skills/
git commit -m "feat(github-project-tools): rename skill directories to bare names"
```

---

### Task 2: Rename trivy-audit skill directory

**Files:**
- Rename: `plugins/trivy-audit/skills/trivy-audit-report/` → `plugins/trivy-audit/skills/report/`

**Step 1: Rename directory with git mv**

```bash
git mv plugins/trivy-audit/skills/trivy-audit-report plugins/trivy-audit/skills/report
```

**Step 2: Verify rename**

Run: `ls plugins/trivy-audit/skills/`
Expected: `report/`

**Step 3: Commit**

```bash
git add -A plugins/trivy-audit/skills/
git commit -m "feat(trivy-audit): rename skill directory to bare name"
```

---

### Task 3: Update frontmatter names to bare names

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md:2`
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:2`
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:2`
- Modify: `plugins/trivy-audit/skills/report/SKILL.md:2`

**Step 1: Edit each frontmatter `name` field**

In `plugins/github-project-tools/skills/add-issue/SKILL.md`:
```
name: github-projects:add-issue  →  name: add-issue
```

In `plugins/github-project-tools/skills/start-implementation/SKILL.md`:
```
name: github-projects:start-implementation  →  name: start-implementation
```

In `plugins/github-project-tools/skills/end-implementation/SKILL.md`:
```
name: github-projects:end-implementation  →  name: end-implementation
```

In `plugins/trivy-audit/skills/report/SKILL.md`:
```
name: trivy-audit:report  →  name: report
```

**Step 2: Verify frontmatter**

Run: `grep '^name:' plugins/*/skills/*/SKILL.md`
Expected: Each shows only the bare name (no colon-prefixed qualifier).

**Step 3: Commit**

```bash
git add plugins/*/skills/*/SKILL.md
git commit -m "feat: update skill frontmatter names to bare names"
```

---

### Task 4: Update cross-references to fully-qualified form

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:127,129`

**Step 1: Edit cross-references in start-implementation SKILL.md**

Line 127 — change:
```
- **If yes:** Invoke `github-projects:end-implementation` via the Skill tool.
```
to:
```
- **If yes:** Invoke `github-project-tools:end-implementation` via the Skill tool.
```

Line 129 — change:
```
- **If no:** Tell the user they can run `/github-projects:end-implementation` later
```
to:
```
- **If no:** Tell the user they can run `/github-project-tools:end-implementation` later
```

**Step 2: Verify no stale references remain**

Run: `grep -r 'github-projects:' plugins/`
Expected: No matches.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): update cross-references to fully-qualified form"
```

---

### Task 5: Update README.md

**Files:**
- Modify: `README.md`

**Step 1: Update skill name references in the Skills lists**

Change the github-project-tools skills section to use `github-project-tools:` prefix:
```
- `github-project-tools:add-issue` — ...
- `github-project-tools:start-implementation` — ...
- `github-project-tools:end-implementation` — ...
```

Change the trivy-audit skill reference (already correct as `trivy-audit:report`).

**Step 2: Update the directory tree**

Change directory names in the tree:
```
│   │   └── skills/
│   │       ├── add-issue/
│   │       │   └── SKILL.md
│   │       ├── start-implementation/
│   │       │   └── SKILL.md
│   │       └── end-implementation/
│   │           └── SKILL.md
```

and:
```
│       └── skills/
│           └── report/
│               ├── SKILL.md
│               └── prompts/
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for renamed skills"
```

---

### Task 6: Update CLAUDE.md naming convention

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update the Skill Conventions section**

Change the naming convention line from:
```
- **Naming:** `plugin-prefix:action-name` (e.g., `github-projects:add-issue`, `trivy-audit:report`)
```
to:
```
- **Naming:** Bare action name in frontmatter and directory (e.g., `add-issue`, `report`). Cross-references use fully-qualified `plugin-name:skill-name` form (e.g., `github-project-tools:add-issue`).
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md naming convention for bare skill names"
```

---

### Task 7: Bump versions

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json:5` — version 0.3.0 → 0.4.0
- Modify: `plugins/trivy-audit/.claude-plugin/plugin.json:5` — version 0.1.0 → 0.2.0
- Modify: `.claude-plugin/marketplace.json:8` — metadata version 0.3.0 → 0.4.0
- Modify: `.claude-plugin/marketplace.json:15` — github-project-tools version 0.3.0 → 0.4.0
- Modify: `.claude-plugin/marketplace.json:22` — trivy-audit version 0.1.0 → 0.2.0

**Step 1: Edit plugin.json files**

In `plugins/github-project-tools/.claude-plugin/plugin.json`:
```
"version": "0.3.0"  →  "version": "0.4.0"
```

In `plugins/trivy-audit/.claude-plugin/plugin.json`:
```
"version": "0.1.0"  →  "version": "0.2.0"
```

**Step 2: Edit marketplace.json**

```
metadata.version: "0.3.0"  →  "0.4.0"
github-project-tools version: "0.3.0"  →  "0.4.0"
trivy-audit version: "0.1.0"  →  "0.2.0"
```

**Step 3: Verify versions are consistent**

Run: `grep '"version"' .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json`
Expected:
```
.claude-plugin/marketplace.json:    "version": "0.4.0"
.claude-plugin/marketplace.json:      "version": "0.4.0",
.claude-plugin/marketplace.json:      "version": "0.2.0",
plugins/github-project-tools/.claude-plugin/plugin.json:  "version": "0.4.0",
plugins/trivy-audit/.claude-plugin/plugin.json:  "version": "0.2.0",
```

**Step 4: Commit with release message**

```bash
git add .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
git commit -m "Release github-project-tools v0.4.0, trivy-audit v0.2.0: bare skill names"
```

**Step 5: Tag releases**

```bash
git tag github-project-tools/v0.4.0
git tag trivy-audit/v0.2.0
```
