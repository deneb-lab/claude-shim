# Partial Reconfiguration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to reconfigure only specific parts of `.claude-shim.json` via the setup skill, instead of re-running the entire setup workflow.

**Architecture:** Single-file change to the setup SKILL.md. Step 1 is rewritten from a binary Keep/Reconfigure choice to a multi-select menu with cascade rules. Step 6 gains merge logic. A new section handles fetching status options when only status mappings are reconfigured.

**Tech Stack:** Markdown (SKILL.md prompt file)

---

## Chunk 1: Rewrite setup SKILL.md

### Task 1: Rewrite Step 1 — Multi-select menu with cascades

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:17-28`

- [ ] **Step 1: Replace Step 1 content**

Replace the current Step 1 ("Check for Existing Config") with the new partial reconfiguration logic. The new Step 1:

1. Runs `<cli> read-config`
2. **If config exists (exit 0):** Shows a summary of current config and presents a multi-select menu via AskUserQuestion
3. **If no config (exit 1):** Proceeds to Step 2 (full setup, same as today)

Replace lines 17-28 of SKILL.md (the entire `## Step 1` section) with:

````markdown
## Step 1: Check for Existing Config

Run:
```bash
<cli> read-config
```

- **If the command fails** (exit code 1): No existing config. Proceed to Step 2 and run all steps through Step 6.

- **If the command succeeds** (exit code 0, outputs JSON): Save the full config object as `EXISTING_CONFIG`. Show the user a summary:

  ```
  Current configuration:
    Repo:            <repo>
    Project:         <project URL>
    Status mappings: <for each stage, show "Name (default), Name2" — mark the default, list others>
    Issue types:     <comma-separated names, mark default>
  ```

  Then present a multi-select via AskUserQuestion using `multiSelect: true`: "What would you like to reconfigure?"

  Options:
  1. **Repository** (also reconfigures: project, fields, status mappings)
  2. **Project** (also reconfigures: fields, status mappings)
  3. **Status mappings**
  4. **Issue types**

  The user selects one or more options. Compute the union of all steps to run based on this cascade table:

  | Option | Runs steps |
  |--------|-----------|
  | Repository | 2, 3, 4, 5 |
  | Project | 3, 4, 5 |
  | Status mappings | 5 |
  | Issue types | 5.5 |

  For example, selecting "Repository" and "Issue types" runs Steps 2, 3, 4, 5, and 5.5. Selecting only "Status mappings" runs Step 5 alone.

  If the user selects zero options, tell them "No sections selected — config unchanged." and stop.

  **For each step below (Steps 2–5.5):** only execute the step if it is in the computed set. Skip steps not in the set — their values come from `EXISTING_CONFIG`.
````

- [ ] **Step 2: Verify the edit**

Read the modified SKILL.md and confirm:
- Step 1 has the multi-select menu with all 4 options
- Cascade table matches the spec exactly
- Zero-selection edge case is handled
- Steps 2-5.5 are conditional on the computed set

- [ ] **Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): rewrite Step 1 with partial reconfiguration menu"
```

### Task 2: Add status-only reconfiguration support

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:89-122`

When only "Status mappings" is selected, Step 5 needs the status field's `.options` array — but Step 4 (which normally provides it) is skipped. Add a preamble to Step 5 that fetches options from the existing config when Step 4 was skipped.

- [ ] **Step 1: Add conditional preamble to Step 5**

Insert the following at the beginning of Step 5 (after the `## Step 5: Detect Status Mappings` heading and before the current content), so it runs only when Step 4 was skipped:

````markdown
**If Step 4 was skipped** (status-only reconfiguration): The status field's `.options` array is not available from Step 4. Obtain it as follows:

1. Extract `OWNER` and `PROJECT_NUMBER` from `EXISTING_CONFIG`'s `project` URL (e.g., `https://github.com/orgs/deneb-lab/projects/1` → owner `deneb-lab`, number `1`).
2. Fetch the project's fields:
   ```bash
   <cli> project-field-list --owner "$OWNER" "$PROJECT_NUMBER"
   ```
3. Extract `STATUS_FIELD_ID` from `EXISTING_CONFIG`'s `fields.status.id`.
4. Find the field in the response whose `.id` matches `STATUS_FIELD_ID`. Use its `.options` array for the rest of this step.

**If Step 4 ran normally:** Use the `STATUS_FIELD_ID` and `.options` array already obtained in Step 4. Proceed as below.
````

- [ ] **Step 2: Verify the edit**

Read Step 5 of the modified SKILL.md and confirm:
- The conditional preamble is present
- It correctly references `EXISTING_CONFIG` for the project URL and status field ID
- The `project-field-list` command uses the correct arguments
- The original Step 5 content (auto-matching, multi-select per stage) is unchanged after the preamble

- [ ] **Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): add status-only reconfiguration support to Step 5"
```

### Task 3: Rewrite Step 6 with merge logic

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:140-186`

Step 6 currently builds a fresh config. For partial reconfiguration, it must merge newly detected values into `EXISTING_CONFIG`.

- [ ] **Step 1: Add merge rules to Step 6**

Insert the following after the existing config JSON template in Step 6 (after the closing ` ``` ` of the JSON block, before "Non-default items..."):

````markdown
**Partial reconfiguration merge:** When `EXISTING_CONFIG` exists (from Step 1), start from `EXISTING_CONFIG` and replace only the sections that were reconfigured:

| Option selected | Config keys replaced |
|----------------|---------------------|
| Repository | `repo` |
| Project | `project`, `fields.start-date`, `fields.end-date`, `fields.status` (entire object including `id` and mappings) |
| Status mappings | `fields.status.todo`, `fields.status.in-progress`, `fields.status.done` (preserves `fields.status.id`) |
| Issue types | `fields.issue-types` |

Keys not in the table above retain their values from `EXISTING_CONFIG`. When no existing config exists (full setup), build the entire object from scratch as shown above.
````

- [ ] **Step 2: Verify the edit**

Read Step 6 of the modified SKILL.md and confirm:
- The merge rules table is present
- It matches the spec exactly (Repository → `repo`, Project → `project` + all fields, Status mappings → only mapping lists preserving `id`, Issue types → `fields.issue-types`)
- The full-setup path (no existing config) is still documented
- The HARD-GATE (user approval before writing) is still present and unchanged

- [ ] **Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): add merge logic to Step 6 for partial reconfiguration"
```

### Task 4: Final review

- [ ] **Step 1: Read the complete modified SKILL.md**

Read the entire file end-to-end. Verify:
- Step 1 has multi-select menu with 4 options and cascade table
- Step 1's final instruction ("For each step below...") makes Steps 2-5.5 conditional on the computed set
- Step 5 has the conditional preamble for status-only reconfiguration
- Step 6 has merge rules table
- All other content (Phase 0, Steps 2-4, Step 5 auto-matching, Step 5.5, Step 7, Important Notes) is unchanged
- No broken markdown formatting

- [ ] **Step 2: Commit final state if any fixes were needed**

If fixes were made during review:
```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "fix(github-project-tools): polish partial reconfiguration SKILL.md"
```
