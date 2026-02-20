# Consolidate Shared Logic Across github-project-tools Skills — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract duplicated prose from three SKILL.md files into shared prompt snippets, add missing preflight to add-issue, and add an `issue-view-full` convenience subcommand to the script.

**Architecture:** Create a `prompts/` directory at the plugin level with four markdown snippets (preflight, setup, parse-issue-arg, conventions). Each SKILL.md replaces its duplicated block with a one-line reference. The script gets one new subcommand.

**Tech Stack:** Markdown (SKILL.md prompt files), Bash (github-projects.sh)

---

### Task 1: Create `prompts/preflight.md`

**Files:**
- Create: `plugins/github-project-tools/prompts/preflight.md`

**Step 1: Write the shared preflight snippet**

Extract the Phase 0 block that appears identically in `start-implementation/SKILL.md:11-18` and `end-implementation/SKILL.md:17-24`. This will also be referenced by `add-issue` (which currently lacks preflight).

```markdown
1. Find the bundled script at `~/.claude/plugins/**/github-project-tools/scripts/github-projects.sh`
2. Run preflight checks:
   ` ` `bash
   scripts/github-projects.sh preflight
   ` ` `
3. If preflight fails, stop and show the error message to the user. Do not proceed.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/prompts/preflight.md
git commit -m "feat(github-project-tools): extract shared preflight prompt snippet"
```

---

### Task 2: Create `prompts/setup.md`

**Files:**
- Create: `plugins/github-project-tools/prompts/setup.md`

**Step 1: Write the shared setup snippet**

Extract the Phase 1 setup block from `start-implementation/SKILL.md:20-32` and `end-implementation/SKILL.md:30-40`. Include the REPO_OVERRIDE preamble sentence from `start-implementation/SKILL.md:22` since both skills need it.

```markdown
The script auto-detects the current repository from the git remote. When `REPO_OVERRIDE` is set (see issue-fetching phase), pass `--repo $REPO_OVERRIDE` before the subcommand in every script invocation to override auto-detection.

1. Get project fields (date field IDs):
   ` ` `bash
   scripts/github-projects.sh get-project-fields
   ` ` `
   This returns JSON with `start` and `end` field IDs. Save these as `START_FIELD` and `END_FIELD`.

   If this command fails because no project is found, note that **no project is available**. Skip all project operations (get-project-item, add-to-project, set-date, set-status) in later phases. Continue with issue-only operations.

2. The `set-status` subcommand accepts the literal arguments `todo`, `in-progress`, and `done` directly — no manual mapping of project-specific status names is needed.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/prompts/setup.md
git commit -m "feat(github-project-tools): extract shared setup prompt snippet"
```

---

### Task 3: Create `prompts/parse-issue-arg.md`

**Files:**
- Create: `plugins/github-project-tools/prompts/parse-issue-arg.md`

**Step 1: Write the shared URL-parsing snippet**

Extract the argument-parsing block from `start-implementation/SKILL.md:36-47` and `end-implementation/SKILL.md:48-59`. These are nearly verbatim identical.

```markdown
Parse the argument. The user provides either:
- A plain issue number like `42`
- A full GitHub URL like `https://github.com/owner/repo/issues/42`

Extract the issue number from whichever format is provided.

**If a full URL was provided**, also extract the `owner/repo` from the URL path. Save this as `REPO_OVERRIDE` (e.g., `elahti/deneb`). When `REPO_OVERRIDE` is set, **prepend `--repo $REPO_OVERRIDE` before the subcommand in every subsequent script invocation**. For example:
` ` `bash
scripts/github-projects.sh --repo elahti/deneb issue-view-full 42
` ` `

If only a plain issue number was provided, do not use `--repo` — the script will auto-detect the repository from the git remote.
```

Note: use `issue-view-full` in the example (the new subcommand from Task 5).

**Step 2: Commit**

```bash
git add plugins/github-project-tools/prompts/parse-issue-arg.md
git commit -m "feat(github-project-tools): extract shared parse-issue-arg prompt snippet"
```

---

### Task 4: Create `prompts/conventions.md`

**Files:**
- Create: `plugins/github-project-tools/prompts/conventions.md`

**Step 1: Write the shared conventions snippet**

Merge the 3-rule footer from `add-issue/SKILL.md:79-83` with the 5-rule footer from `start-implementation/SKILL.md:203-209` and `end-implementation/SKILL.md:140-146`. The superset is 5 rules.

```markdown
- **All bash commands** must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `scripts/github-projects.sh` — never call `gh` directly.
- **Date field IDs** are looked up at runtime via `get-project-fields` — they may change if the project is recreated.
- **Project is optional.** If no project is detected during setup, skip all project operations (get-project-item, add-to-project, set-date, set-status) but still perform issue operations (assign, view, close, parent check).
```

Note: rule 5 uses a generalized list of issue operations (not skill-specific).

**Step 2: Commit**

```bash
git add plugins/github-project-tools/prompts/conventions.md
git commit -m "feat(github-project-tools): extract shared conventions prompt snippet"
```

---

### Task 5: Add `issue-view-full` subcommand to script

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:129-133` (add new function after `cmd_issue_view`)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:9-26` (add to usage comment)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:328-351` (add to dispatch)

**Step 1: Add the function**

After `cmd_issue_view` (line 133), add:

```bash
cmd_issue_view_full() {
  gh issue view "$1" --repo "$REPO" --json id,number,title,body,state
}
```

**Step 2: Add to the usage comment header**

After line 11 (`#   issue-view <number> [gh-flags...]     View issue (passthrough to gh issue view)`), add:

```
#   issue-view-full <number>              View issue (JSON: id,number,title,body,state)
```

**Step 3: Add to the dispatch case**

After the `issue-view)` line (line 330), add:

```bash
  issue-view-full)      detect_repo; shift; cmd_issue_view_full "$@" ;;
```

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat(github-project-tools): add issue-view-full convenience subcommand"
```

---

### Task 6: Update `add-issue/SKILL.md`

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md`

**Step 1: Add Phase 0 preflight reference**

Insert a new Phase 0 section between the intro (line 8) and Phase 1 (line 10):

```markdown
## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).
```

Renumber existing phases: Phase 1 stays "Phase 1", Phase 2 stays "Phase 2", etc. (no renumbering needed since preflight is Phase 0).

**Step 2: Replace Important Notes footer**

Replace lines 79-83 (the 3-rule Important Notes section) with:

```markdown
## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
```

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/add-issue/SKILL.md
git commit -m "feat(github-project-tools): add preflight and shared conventions to add-issue"
```

---

### Task 7: Update `start-implementation/SKILL.md`

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md`

**Step 1: Replace Phase 0 with snippet reference**

Replace lines 11-18 (Phase 0 content) with:

```markdown
## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).
```

**Step 2: Replace Phase 1 with snippet reference**

Replace lines 20-32 (Phase 1 content) with:

```markdown
## Phase 1: Setup

Follow the steps in [prompts/setup.md](prompts/setup.md).
```

**Step 3: Replace URL-parsing block in Phase 2 with snippet reference**

Replace lines 36-47 (the argument parsing block, steps 1's full text through the `--repo` example) with:

```markdown
1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).
```

**Step 4: Replace `issue-view` with `issue-view-full`**

Replace line 51:
```
   scripts/github-projects.sh issue-view <number> --json id,number,title,body,state
```
with:
```
   scripts/github-projects.sh issue-view-full <number>
```

**Step 5: Replace Important Notes footer with snippet reference**

Replace lines 203-209 with:

```markdown
## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
```

**Step 6: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): use shared prompts in start-implementation"
```

---

### Task 8: Update `end-implementation/SKILL.md`

**Files:**
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md`

**Step 1: Replace Phase 0 with snippet reference**

Replace lines 17-24 (Phase 0 content) with:

```markdown
## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).
```

**Step 2: Replace Phase 1 setup with snippet reference**

Replace lines 30-40 (the setup content inside the conditional Phase 1) with a reference. Keep the conditional preamble about handoff:

```markdown
## Phase 1: Setup (conditional)

**If state from `start-implementation` is already in the conversation context** (NODE_ID, ITEM_ID, field IDs, and parent info are known), **skip to Phase 3.**

Otherwise, follow the steps in [prompts/setup.md](prompts/setup.md).
```

**Step 3: Replace URL-parsing block in Phase 2 with snippet reference**

Replace lines 48-59 (the argument parsing text) with:

```markdown
1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).
```

**Step 4: Replace `issue-view` with `issue-view-full`**

Replace line 63:
```
   scripts/github-projects.sh issue-view <number> --json id,number,title,body,state
```
with:
```
   scripts/github-projects.sh issue-view-full <number>
```

**Step 5: Replace Important Notes footer with snippet reference**

Replace lines 140-146 with:

```markdown
## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
```

**Step 6: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): use shared prompts in end-implementation"
```

---

### Task 9: Version bump and release commit

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json` (bump version)
- Modify: `.claude-plugin/marketplace.json` (bump plugin version + metadata version)

**Step 1: Bump plugin version**

In `plugins/github-project-tools/.claude-plugin/plugin.json`, change `"version": "0.6.0"` to `"version": "0.7.0"`.

**Step 2: Bump marketplace.json**

In `.claude-plugin/marketplace.json`:
- Change the github-project-tools plugin `"version": "0.6.0"` to `"version": "0.7.0"`
- Change `"metadata" > "version": "0.6.0"` to `"version": "0.7.0"`

**Step 3: Commit and tag**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v0.7.0: consolidate shared logic across skills"
git tag github-project-tools/v0.7.0
```
