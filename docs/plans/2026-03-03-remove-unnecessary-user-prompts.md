# Remove Unnecessary User Prompts from start-implementation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate redundant assignment, date-setting, and user prompts in the `start-implementation` skill when the user is already assigned or dates are already set.

**Architecture:** Skill-only changes to `start-implementation/SKILL.md`. Add pre-checks using existing CLI subcommands (`issue-get-assignees`, `get-start-date`) before performing operations. Follows the same pattern already used in `end-implementation`.

**Tech Stack:** Markdown (SKILL.md), existing CLI subcommands

---

### Task 1: Add `issue-get-assignees` to allowed-tools

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:4`

**Step 1: Edit the frontmatter**

In the `allowed-tools` line (line 4), add `Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *)` after the existing `issue-assign` entry.

The new allowed-tools line should contain all existing entries plus the new one. Insert it right after the `issue-assign *` entry for logical grouping.

**Step 2: Verify**

Read the file and confirm the frontmatter includes `issue-get-assignees`.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): add issue-get-assignees to start-implementation allowed-tools"
```

---

### Task 2: Check assignees before assigning issue (Phase 3, Step 1)

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:46-49`

**Step 1: Replace Phase 3, Step 1**

Replace the current step 1 (lines 46-49):

```markdown
1. Assign the issue to yourself:
   ```bash
   <cli> issue-assign <number>
   ```
```

With:

```markdown
1. Check if already assigned to the issue:
   ```bash
   <cli> issue-get-assignees <number>
   ```
   Check if the current user's login is in the returned JSON array. If already assigned, skip to step 2. Otherwise, assign:
   ```bash
   <cli> issue-assign <number>
   ```
```

This mirrors `end-implementation` Phase 2.3 step 2, but skips silently instead of asking.

**Step 2: Verify**

Read the modified section and confirm it matches the above.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): check assignees before assigning issue in start-implementation"
```

---

### Task 3: Check start date before setting it on the issue (Phase 3, Step 2)

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md` (Phase 3, Step 2)

**Step 1: Replace Phase 3, Step 2a-b**

Replace the current step 2a and 2b (which uses `get-project-item` then unconditionally calls `set-date`):

```markdown
   a. Check if the issue is already on the project board:
      ```bash
      <cli> get-project-item "$NODE_ID"
      ```
      - If the output is **non-empty**, that value is `ITEM_ID`.
      - If the output is **empty**, add the issue to the project:
        ```bash
        <cli> add-to-project "$NODE_ID"
        ```
        The output of `add-to-project` is `ITEM_ID`.

   b. Set the start date to today:
      ```bash
      <cli> set-date "$ITEM_ID" "$START_FIELD"
      ```
```

With:

```markdown
   a. Check if the issue is on the project board and whether a start date is already set:
      ```bash
      <cli> get-start-date "$NODE_ID"
      ```
      - If the output is **non-empty**: extract `ITEM_ID` from `.item_id` and `ISSUE_DATE` from `.date`. Proceed to (b).
      - If the output is **empty**: the issue is not on the project board. Add it:
        ```bash
        <cli> add-to-project "$NODE_ID"
        ```
        The output is `ITEM_ID`. `ISSUE_DATE` is implicitly `"null"`. Proceed to (b).

   b. If `ISSUE_DATE` is `"null"` (no start date set), set it to today:
      ```bash
      <cli> set-date "$ITEM_ID" "$START_FIELD"
      ```
```

This replaces `get-project-item` with `get-start-date` (which returns both `item_id` and `date`), and only sets the date if it's not already set. Step 2c (set status) remains unchanged.

**Step 2: Verify**

Read the modified section and confirm it matches the above.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): check start date before setting it on issue in start-implementation"
```

---

### Task 4: Check assignees before asking about parent assignment (Phase 3, Step 4)

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md` (Phase 3, Step 4)

**Step 1: Replace Phase 3, Step 4**

Replace the current step 4 (lines 100-106):

```markdown
4. **If a parent issue exists** (regardless of project board status), ask the user about assignment:
   - **Ask the user:** "Assign yourself to parent #PARENT_NUMBER (PARENT_TITLE)?"
   - **Only proceed if the user confirms.**
   - If confirmed:
     ```bash
     <cli> issue-assign <PARENT_NUMBER>
     ```
```

With:

```markdown
4. **If a parent issue exists** (regardless of project board status), check parent assignment:
   ```bash
   <cli> issue-get-assignees <PARENT_NUMBER>
   ```
   - If the current user is already in the assignees list, skip.
   - If the current user is **not** in the assignees list, **ask the user:** "Assign yourself to parent #PARENT_NUMBER (PARENT_TITLE)?"
   - **Only proceed if the user confirms.**
   - If confirmed:
     ```bash
     <cli> issue-assign <PARENT_NUMBER>
     ```
```

This mirrors `end-implementation` Phase 3 step 4.

**Step 2: Verify**

Read the modified section and confirm it matches the above.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): check assignees before asking about parent assignment in start-implementation"
```

---

### Task 5: Final verification

**Step 1: Review the complete file**

Read the entire `SKILL.md` and verify:
- All 4 changes are in place
- No broken markdown formatting
- Consistent style with the rest of the file
- `get-project-item` is no longer used (can optionally be removed from allowed-tools, but keeping it is harmless)

**Step 2: Verify shared prompts are not affected**

Per CLAUDE.md, only `prompts/` files are shared. SKILL.md is per-skill. No shared prompt updates needed.
