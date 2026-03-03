# Remove Unnecessary User Prompts from start-implementation

## Problem

The `start-implementation` skill unconditionally assigns the user, sets start dates, and asks about parent assignment — even when those operations are redundant (user already assigned, date already set). This creates unnecessary user prompts and API calls.

## Approach

Skill-only changes to `start-implementation/SKILL.md`. No CLI changes needed — the required subcommands (`issue-get-assignees`, `get-start-date`) already exist.

## Changes

### 1. Frontmatter

Add `issue-get-assignees` to `allowed-tools`.

### 2. Issue assignment (Phase 3, Step 1)

Call `issue-get-assignees <number>` before `issue-assign`. Skip silently if already assigned.

### 3. Issue start date (Phase 3, Step 2)

Replace `get-project-item` with `get-start-date "$NODE_ID"` which returns both `item_id` and `date`. If date is already set, skip `set-date`. If output is empty (not on board), fall back to `add-to-project` then `set-date`.

### 4. Parent assignment (Phase 3, Step 4)

Call `issue-get-assignees <PARENT_NUMBER>` before asking user. Skip silently if already assigned.

### No change needed

Parent start date (Phase 3, Step 3b) already checks for null date before setting.

## Behavior

Silent skip — no messages when skipping redundant operations.
