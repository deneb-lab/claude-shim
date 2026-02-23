# Direct Script Invocation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Strengthen script invocation conventions so Claude Code never wraps script paths in variables, preserving permission fingerprints.

**Architecture:** Replace the first bullet point in 4 conventions blocks (3 shared copies in github-project-tools, 1 inline in trivy-audit report-writer.md) with a more explicit instruction that explains the permission-matching reason.

**Tech Stack:** Markdown prompt files only — no code changes.

---

### Task 1: Update github-project-tools conventions (3 shared copies)

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/conventions.md:1`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/conventions.md:1`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/conventions.md:1`

**Step 1: Replace the first bullet in all 3 files**

In each file, replace line 1:

```
- **All bash commands** must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.
```

With:

```
- **Script invocation:** The resolved script path MUST be the literal first token of every bash command — e.g. `scripts/github-projects.sh issue-assign 14`. NEVER split the path into a variable like `SCRIPTS=... && $SCRIPTS/github-projects.sh ...`. Claude Code matches permissions by the first token; variable-wrapped paths produce a different fingerprint every time, forcing repeated approval prompts.
```

**Step 2: Verify all 3 copies are identical**

Run: `diff` between the three files to confirm they match.

**Step 3: Commit**

```
git add plugins/github-project-tools/skills/*/prompts/conventions.md
git commit -m "feat(github-project-tools): strengthen script invocation convention"
```

### Task 2: Update trivy-audit report-writer inline conventions

**Files:**
- Modify: `plugins/trivy-audit/skills/report/prompts/report-writer.md:234`

**Step 1: Replace the first bullet in the inline conventions block**

In report-writer.md, near line 234, replace:

```
- **All bash commands** must start with the script or command being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output in subsequent commands.
```

With:

```
- **Script invocation:** The resolved script path MUST be the literal first token of every bash command — e.g. `scripts/github-projects.sh issue-assign 14`. NEVER split the path into a variable like `SCRIPTS=... && $SCRIPTS/github-projects.sh ...`. Claude Code matches permissions by the first token; variable-wrapped paths produce a different fingerprint every time, forcing repeated approval prompts.
```

**Step 2: Commit**

```
git add plugins/trivy-audit/skills/report/prompts/report-writer.md
git commit -m "feat(trivy-audit): strengthen script invocation convention"
```

### Task 3: Bump versions and release

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`
- Modify: `plugins/trivy-audit/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Bump github-project-tools patch version**

Read `plugins/github-project-tools/.claude-plugin/plugin.json`, bump the patch version (e.g. `0.10.0` -> `0.10.1`). Update the matching entry in `.claude-plugin/marketplace.json`.

**Step 2: Bump trivy-audit patch version**

Read `plugins/trivy-audit/.claude-plugin/plugin.json`, bump the patch version (e.g. `0.3.0` -> `0.3.1`). Update the matching entry in `.claude-plugin/marketplace.json`.

**Step 3: Bump marketplace metadata version**

Bump `metadata.version` in `.claude-plugin/marketplace.json`.

**Step 4: Commit and tag**

```
git add plugins/github-project-tools/.claude-plugin/plugin.json plugins/trivy-audit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump github-project-tools to 0.10.1 and trivy-audit to 0.3.1"
git tag github-project-tools/v0.10.1
git tag trivy-audit/v0.3.1
```
