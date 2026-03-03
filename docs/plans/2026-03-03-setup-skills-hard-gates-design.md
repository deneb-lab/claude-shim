# Setup Skills Hard Gates — Design

**Issue:** [#62](https://github.com/elahti/deneb-marketplace/issues/62) — Claude-shim's setup skills for both plugins are too eager

**Date:** 2026-03-03

## Problem

Both `setup-github-project-tools` and `setup-quality-check-hook` sometimes write `.claude-shim.json` without waiting for user confirmation. The AI reads "present for confirmation" as a statement and proceeds to write because the writing instructions follow immediately. Auto-detection itself is fine — the problem is the config being written without explicit approval.

## Approach

Add `<HARD-GATE>` blocks (a pattern proven in the brainstorming skill) at key confirmation points. These force the AI to use `AskUserQuestion` and stop until the user explicitly approves.

## Changes

### `setup-github-project-tools/SKILL.md`

1. **Step 2 (Detect Repository):** Replace soft "Confirm with the user" with explicit `AskUserQuestion` requirement — "Yes, use this repository" / "No, let me specify a different one". If declined, ask for the correct `owner/repo`.

2. **Step 3 (Detect Project, single-project case):** Replace "Ask for confirmation" with `AskUserQuestion` — "Use this project?" Yes/No. If declined, tell user no other projects are available.

3. **Step 6 (Write Config):** Add `<HARD-GATE>` before the write instructions requiring `AskUserQuestion` with "Approve and write" / "Make changes" options. Do not write until user selects "Approve and write".

### `setup-quality-check-hook/SKILL.md`

1. **Step 5 (Present Proposed Config):** Add explicit `AskUserQuestion` with "Approve and write" / "Make changes" options at the end.

2. **Between Step 5 and Step 6:** Add `<HARD-GATE>` — do not proceed to Step 6 until user has explicitly approved via `AskUserQuestion`.

## Non-changes

- Auto-detection logic stays the same — detecting repos, projects, tooling is fine
- Field detection and status mapping confirmation flow is fine (already uses AskUserQuestion for ambiguous cases)
- No script or code changes needed — this is purely SKILL.md prompt wording
