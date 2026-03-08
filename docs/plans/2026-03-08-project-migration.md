# GitHub Project Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate all 143 issues from 7 deneb-lab repos to the new org project (deneb-lab/projects/1), preserving statuses and dates from the old personal project, and setting issue types.

**Architecture:** Scripted migration using `gh` CLI and GraphQL API. Export old project data as a lookup table, then iterate over all issues in all repos: add to project, set status, set dates (if from old project), set issue type (Task or Bug). Each repo is processed sequentially to avoid rate limiting.

**Tech Stack:** `gh` CLI, GitHub GraphQL API, `jq`, bash

---

## Reference Data

### Old Project Items (30 items with metadata to preserve)

| Repo | Issue # | Status | Start Date | End Date |
|------|---------|--------|------------|----------|
| deneb | 3 | Done | 2026-03-01 | 2026-03-01 |
| deneb | 4 | In Progress | 2026-02-14 | — |
| deneb | 5 | Done | — | 2026-02-15 |
| deneb | 6 | Done | — | 2026-02-15 |
| deneb | 7 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 8 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 9 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 10 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 11 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 12 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 13 | Todo | — | — |
| deneb | 14 | Done | 2026-02-23 | 2026-02-23 |
| deneb | 15 | Done | 2026-02-16 | 2026-02-16 |
| deneb | 16 | Done | 2026-03-01 | 2026-03-01 |
| deneb | 17 | Done | 2026-03-07 | 2026-03-07 |
| deneb | 18 | Done | 2026-03-07 | 2026-03-07 |
| deneb | 19 | Done | 2026-02-17 | 2026-02-17 |
| deneb | 20 | Todo | — | — |
| deneb | 21 | Done | 2026-02-17 | 2026-02-17 |
| deneb | 22 | Done | 2026-02-17 | 2026-02-17 |
| deneb | 23 | Done | 2026-02-17 | 2026-02-17 |
| deneb | 24 | Todo | — | — |
| deneb | 26 | Done | 2026-02-18 | 2026-02-18 |
| deneb | 27 | Done | 2026-03-01 | 2026-03-01 |
| deneb | 28 | Done | 2026-02-20 | 2026-02-20 |
| deneb-marketplace | 27 | Done | 2026-02-19 | 2026-02-19 |
| deneb-marketplace | 28 | Done | 2026-02-18 | 2026-02-24 |
| deneb-marketplace | 49 | Done | 2026-02-17 | 2026-02-17 |
| deneb-marketplace | 50 | Done | 2026-02-17 | 2026-02-17 |
| deneb-marketplace | 51 | Done | 2026-02-17 | 2026-02-17 |

### Issue Type Classification

All issues default to **Task** unless listed below as **Bug**:

| Repo | Issue # | Title | Type |
|------|---------|-------|------|
| deneb | 16 | Fix warning in alloy task of Ansible playbook | Bug |
| deneb | 17 | Alloy: ARC runner logs dropped due to Loki label limit (18 > 15) | Bug |
| deneb | 27 | Fix phoebe.fi motd | Bug |
| deneb | 52 | Fix Kitty + tmux + ssh setup | Bug |
| deneb | 57 | Investigate why longhorn-instance-manager consumes increasing amount of memory | Bug |
| deneb | 58 | Investigate loki-chunks-cache-0 resource consumption | Bug |
| deneb | 59 | nvim does not show directories / files in .gitignore | Bug |
| deneb | 62 | btop shows invalid colors on macos and k0s dev environment | Bug |
| deneb | 63 | Fix all ansible-lint errors | Bug |
| deneb | 64 | Fix k9s colors | Bug |
| deneb | 66 | claude-remote: kubectl namespace flag and helm-list broken | Bug |
| k0s-dev-environment | 7 | Bug while changing dir to ~/development/deneb | Bug |
| k0s-dev-environment | 8 | Can't sign commits on the k0s dev environment | Bug |
| k0s-dev-environment | 9 | ssh git@github.com forces approval of host fingerprint after every container rebuild | Bug |
| k0s-dev-environment | 14 | Fix warnings during make release command | Bug |
| k0s-dev-environment | 18 | fix nvim health check issues | Bug |
| deneb-marketplace | 29 | issue-close --comment silently drops comment when issue is already closed | Bug |
| deneb-marketplace | 34 | quality-check-hook runs ansible-lint on GitHub Actions workflow files | Bug |
| deneb-marketplace | 36 | quality-check-hook: ansible-lint --fix non-zero exit blocks hook despite successful fix | Bug |
| deneb-marketplace | 37 | Bug: Skill prompt paths resolve incorrectly relative to skill base directory | Bug |
| deneb-marketplace | 46 | fix: start-implementation should extract repo from issue URL | Bug |
| deneb-marketplace | 62 | Claude-shim's setup skills for both plugins are too eager | Bug |
| deneb-marketplace | 64 | Fix GitHub project skill permissions | Bug |
| deneb-marketplace | 70 | GitHub project skills does not ask for which repo to use | Bug |
| deneb-marketplace | 78 | start-implementation skill always asks permission to assign user to the parent issue | Bug |
| deneb-marketplace | 81 | issue-create silently fails when using unsupported --label flag | Bug |
| deneb-marketplace | 84 | github-project-tools: issue-close skips comment when issue is already closed | Bug |
| deneb-marketplace | 85 | github-project-tools: issue-create syntax not discoverable outside add-issue skill | Bug |

### Field IDs

- New project ID: `PVT_kwDOD-Fm1s4BRGlT`
- Status field: `PVTSSF_lADOD-Fm1s4BRGlTzg_B3r0`
  - Todo: `f75ad846`
  - In Progress: `47fc9ee4`
  - Done: `98236657`
- Start date field: `PVTF_lADOD-Fm1s4BRGlTzg_CVrI`
- End date field: `PVTF_lADOD-Fm1s4BRGlTzg_CVsc`
- Issue type Task: `IT_kwDOD-Fm1s4B44fF`
- Issue type Bug: `IT_kwDOD-Fm1s4B44fG`

### API Patterns (confirmed working)

```bash
# Add issue to project (returns item ID)
gh project item-add 1 --owner deneb-lab --url <issue-url> --format json | jq -r '.id'

# Set status (single-select field)
gh project item-edit --id <item-id> --project-id PVT_kwDOD-Fm1s4BRGlT --field-id PVTSSF_lADOD-Fm1s4BRGlTzg_B3r0 --single-select-option-id <option-id>

# Set date field
gh project item-edit --id <item-id> --project-id PVT_kwDOD-Fm1s4BRGlT --field-id <date-field-id> --date <YYYY-MM-DD>

# Set issue type (GraphQL)
gh api graphql -f query='mutation { updateIssue(input: { id: "<issue-node-id>", issueTypeId: "<type-id>" }) { issue { id } } }'
```

---

## Tasks

### Task 1: Migrate deneb repo issues (54 issues)

This is the largest repo. Process all 54 issues.

**Step 1: Add all deneb issues to the new project and set fields**

For each issue in deneb-lab/deneb:
1. Get issue URL and node ID: `gh issue list --repo deneb-lab/deneb --state all --limit 100 --json number,url,state,id`
2. Add to project: `gh project item-add 1 --owner deneb-lab --url <url> --format json`
3. Set status:
   - If issue is in old project lookup table → use preserved status
   - If issue state is CLOSED → Done (`98236657`)
   - If issue state is OPEN → Todo (`f75ad846`)
4. Set dates (only for issues in old project lookup table that have dates)
5. Set issue type via GraphQL (Bug for issues listed in bug table, Task for all others)

Run each issue sequentially. Log progress to stdout.

**Step 2: Verify deneb migration**

Run: `gh project item-list 1 --owner deneb-lab --format json | jq '[.items[] | select(.content.repository == "deneb-lab/deneb")] | length'`
Expected: 54

### Task 2: Migrate deneb-marketplace repo issues (59 issues)

Same process as Task 1 but for deneb-lab/deneb-marketplace. 5 issues are in the old project lookup table.

**Step 1: Add all deneb-marketplace issues and set fields**

Same pattern as Task 1 Step 1.

**Step 2: Verify deneb-marketplace migration**

Expected count: 59

### Task 3: Migrate k0s-dev-environment repo issues (17 issues)

No issues from this repo were on the old project. All closed → Done, open → Todo.

**Step 1: Add all k0s-dev-environment issues and set fields**

Same pattern. No dates to set. Bug classification per table above.

**Step 2: Verify k0s-dev-environment migration**

Expected count: 17

### Task 4: Migrate eu-ai-act repo issues (9 issues)

No issues from this repo were on the old project. No bugs identified.

**Step 1: Add all eu-ai-act issues and set fields**

Same pattern. All Task type. No dates.

**Step 2: Verify eu-ai-act migration**

Expected count: 9

### Task 5: Migrate remaining repos (claude-shim: 2, stellaris-stats: 1, devcontainer: 1)

Small repos grouped together. No old project items, no bugs.

**Step 1: Add all issues from remaining repos and set fields**

Same pattern for each repo.

**Step 2: Verify remaining repos migration**

Expected counts: claude-shim: 2, stellaris-stats: 1, devcontainer: 1

### Task 6: Final verification

**Step 1: Count total items on new project**

Run: `gh project item-list 1 --owner deneb-lab --format json | jq '.items | length'`
Expected: 143

**Step 2: Spot-check dates on known items**

Verify a few items from the old project have correct dates:
- deneb#3: Start 2026-03-01, End 2026-03-01
- deneb-marketplace#28: Start 2026-02-18, End 2026-02-24
- deneb#4: Start 2026-02-14, no End date

**Step 3: Spot-check issue types**

Verify a few known bugs have Bug type and a few known tasks have Task type.
