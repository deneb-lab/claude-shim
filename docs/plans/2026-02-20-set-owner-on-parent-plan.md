# Set Owner on Parent Issue Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically assign the current user to the parent issue when starting implementation on a sub-issue.

**Architecture:** Single addition to `start-implementation/SKILL.md` Phase 3. No script changes — reuses existing `issue-assign` subcommand which is idempotent.

**Tech Stack:** Markdown (SKILL.md prompt engineering)

---

### Task 1: Add parent assignment step to SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:66-73`

**Step 1: Edit the skill file**

In Phase 3 ("Set Start State"), insert a new step 2 between the current step 1 ("Assign the issue to yourself") and step 2 ("If a project is available"). The new step assigns the current user to the parent issue if one exists.

Add after line 73 (the closing of step 1's code block) and before line 75 (current step 2):

```markdown
2. **If a parent issue exists** (detected in Phase 2, step 4), assign yourself to the parent issue:
   ```bash
   scripts/github-projects.sh issue-assign <parent_number>
   ```
   This is idempotent — no error if already assigned.
```

Then renumber the subsequent steps: current step 2 becomes step 3, current step 3 becomes step 4, current step 4 becomes step 5, current step 5 becomes step 6.

**Step 2: Verify the edit**

Read the modified file and confirm:
- New step 2 is correctly placed after step 1 (assign child issue) and before step 3 (project operations)
- All subsequent steps are renumbered correctly (3, 4, 5, 6)
- The `<parent_number>` placeholder matches the convention used elsewhere in the skill (e.g., `PARENT_NUMBER` from Phase 2)
- No other content was accidentally modified

**Step 3: Bump plugin version**

Update the version in two files:
- `plugins/github-project-tools/.claude-plugin/plugin.json`: bump patch version
- `.claude-plugin/marketplace.json`: match the new version in the plugins array, bump `metadata.version`

Read both files first to determine current versions.

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat(github-project-tools): assign current user to parent issue in start-implementation"
```
