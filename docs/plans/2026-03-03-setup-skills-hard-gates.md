# Setup Skills Hard Gates — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prevent both setup skills from writing `.claude-shim.json` without explicit user approval.

**Architecture:** Add `<HARD-GATE>` blocks and explicit `AskUserQuestion` requirements to two SKILL.md files. Prompt-only changes — no scripts, code, or tests.

**Tech Stack:** Markdown (SKILL.md prompt engineering)

---

### Task 1: Harden setup-github-project-tools Step 2 (Detect Repository)

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:30-39`

**Step 1: Edit Step 2 to require AskUserQuestion**

Replace the current line 39:
```
Confirm with the user: "Detected repository: `REPO`. Issues will be created and managed in this repository. Correct?"
```

With:
```
Use AskUserQuestion to confirm with the user: "Detected repository: `REPO`. Issues will be created and managed in this repository."
- **Yes, use this repository** — proceed to Step 3.
- **No, let me specify** — ask the user for the correct `owner/repo` value, save it as `REPO`, re-extract `OWNER`, and proceed to Step 3.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): require AskUserQuestion for repo confirmation in setup"
```

---

### Task 2: Harden setup-github-project-tools Step 3 (Detect Project, single-project case)

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:52`

**Step 1: Edit the single-project case to require AskUserQuestion**

Replace line 52:
```
- **If exactly one project:** Auto-select it. Tell the user: "Found project: `title` (`url`). Using this project." Ask for confirmation.
```

With:
```
- **If exactly one project:** Use AskUserQuestion to confirm: "Found one project: `title` (`url`)."
  - **Yes, use this project** — proceed.
  - **No** — tell the user "No other projects found for owner `OWNER`. Create another project first, then re-run this setup." Stop.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): require AskUserQuestion for single-project confirmation in setup"
```

---

### Task 3: Harden setup-github-project-tools Step 6 (Write Config)

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:116-143`

**Step 1: Add HARD-GATE before the write instructions**

Replace the current Step 6 content (lines 116-143) with:

```markdown
## Step 6: Write Config

Build the configuration object:
```json
{
  "github-project-tools": {
    "project": "<PROJECT_URL>",
    "fields": {
      "start-date": "<START_FIELD_ID>",
      "end-date": "<END_FIELD_ID>",
      "status": {
        "id": "<STATUS_FIELD_ID>",
        "todo": { "name": "<name>", "option-id": "<id>" },
        "in-progress": { "name": "<name>", "option-id": "<id>" },
        "done": { "name": "<name>", "option-id": "<id>" }
      }
    }
  }
}
```

Present the final config JSON to the user.

<HARD-GATE>
Do NOT write `.claude-shim.json` until the user has explicitly approved. Use AskUserQuestion:
- **Approve and write** — proceed to write the file.
- **Make changes** — ask what to change, update the config, and present again.
</HARD-GATE>

**Write to `.claude-shim.json`:**
- If the file exists: read it, add or replace the `github-project-tools` key, preserve all other keys (like `quality-checks`), write back.
- If the file doesn't exist: create it with just the `github-project-tools` key.

Use the Write tool to save the file.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): add hard gate before config write in setup"
```

---

### Task 4: Harden setup-quality-check-hook Step 5/6 (Present and Write Config)

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md:101-143`

**Step 1: Add AskUserQuestion requirement to Step 5 and HARD-GATE before Step 6**

Replace the end of Step 5 (lines 109-118) with:

```markdown
Ask the user to confirm, or tell you what to change. Iterate until they're satisfied.

The user may:
- Remove entries for languages they don't want checked
- Add entries for languages not auto-detected
- Change commands (e.g., add flags, change tools)
- Change patterns (e.g., exclude test files from formatting)
- Add or remove exclude patterns
- Override the package runner

When the user is satisfied, use AskUserQuestion for final confirmation:
- **Approve and write** — proceed to Step 6.
- **Make changes** — ask what to change, update the config, and present again.

<HARD-GATE>
Do NOT proceed to Step 6 until the user has explicitly selected "Approve and write" via AskUserQuestion. Presenting the config is NOT the same as getting approval.
</HARD-GATE>
```

**Step 2: Commit**

```bash
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): add hard gate before config write in setup"
```

---

### Task 5: Bump plugin versions

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`
- Modify: `plugins/quality-check-hook/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Check current versions**

Read all three files to get current version numbers.

**Step 2: Bump github-project-tools patch version**

Bump `version` in `plugins/github-project-tools/.claude-plugin/plugin.json` and the matching entry in `.claude-plugin/marketplace.json`.

**Step 3: Bump quality-check-hook patch version**

Bump `version` in `plugins/quality-check-hook/.claude-plugin/plugin.json` and the matching entry in `.claude-plugin/marketplace.json`.

**Step 4: Bump marketplace metadata version**

Bump `metadata.version` in `.claude-plugin/marketplace.json`.

**Step 5: Commit**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json plugins/quality-check-hook/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump versions for setup skill hard gates"
```
