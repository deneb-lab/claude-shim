# Direct Script Invocation — Design

## Problem

Claude Code resolves relative `scripts/` paths in SKILL.md to absolute paths at runtime, but sometimes wraps them in variable assignments like `SCRIPTS=... && $SCRIPTS/github-projects.sh ...`. This breaks Claude Code's permission fingerprinting — the first token of the bash command determines the permission match. Variable-wrapped paths produce a different fingerprint each time, forcing repeated approval prompts.

## Solution

Strengthen the existing "start with script path" convention in all conventions blocks to explicitly explain the permission-matching reason and provide a concrete bad example.

## Files to Change

4 locations across 2 plugins:

1. `plugins/github-project-tools/skills/add-issue/prompts/conventions.md` — line 1
2. `plugins/github-project-tools/skills/start-implementation/prompts/conventions.md` — line 1
3. `plugins/github-project-tools/skills/end-implementation/prompts/conventions.md` — line 1
4. `plugins/trivy-audit/skills/report/prompts/report-writer.md` — line 234 (inline conventions)

## Change

Replace the first bullet in each conventions block:

**Before:**
> All bash commands must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.

**After:**
> **Script invocation:** The resolved script path MUST be the literal first token of every bash command — e.g. `scripts/github-projects.sh issue-assign 14`. NEVER split the path into a variable like `SCRIPTS=... && $SCRIPTS/github-projects.sh ...`. Claude Code matches permissions by the first token; variable-wrapped paths produce a different fingerprint every time, forcing repeated approval prompts.

## Out of Scope

- `quality-check-hook` — no conventions.md, different usage pattern (setup wizard)
- SKILL.md code blocks — already use direct `scripts/` references correctly
