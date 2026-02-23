# Remove Command Substitution from All Skills — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate all `$()` command substitution from skill instructions so Claude Code never triggers its "command contains $() command substitution" permission prompt.

**Architecture:** Two script-level changes: (1) `set-date` resolves today's date internally instead of accepting a date parameter, (2) `issue-create` and `issue-edit` gain `--body-file` flag. Skills update their instructions to use the simpler APIs.

**Tech Stack:** Bash scripts, GitHub Projects GraphQL API, Markdown skill files

---

### Task 1: Update `cmd_set_date` in github-project-tools script

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:22` (usage header)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:295-305` (`cmd_set_date` function)

**Step 1: Change the usage comment**

In the header block (line 22), change:
```
#   set-date <item-id> <field-id> <date>  Set project date field
```
to:
```
#   set-date <item-id> <field-id>         Set project date field (always today)
```

**Step 2: Change `cmd_set_date` to resolve date internally**

Replace lines 295-305:
```bash
cmd_set_date() {
  local item="$1" field="$2"
  local date
  date=$(date +%Y-%m-%d)
  graphql '
    mutation($project: ID!, $item: ID!, $field: ID!, $date: Date!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $project, itemId: $item,
        fieldId: $field, value: {date: $date}
      }) { projectV2Item { id } }
    }' -f project="$PROJECT_ID" -f item="$item" \
       -f field="$field" -f date="$date"
}
```

**Step 3: Test manually**

Run: `plugins/github-project-tools/scripts/github-projects.sh --repo elahti/claude-shim set-date "PVTI_lAHOAC8LI84BPPkbzgl9Lu8" "PVTF_lAHOAC8LI84BPPkbzg9teuk"`
Expected: JSON response with `projectV2Item.id`

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat: set-date always uses today's date, remove date parameter"
```

---

### Task 2: Update `cmd_set_date` in trivy-audit script

**Files:**
- Modify: `plugins/trivy-audit/scripts/github-projects.sh:16` (usage header)
- Modify: `plugins/trivy-audit/scripts/github-projects.sh:239-249` (`cmd_set_date` function)

**Step 1: Change the usage comment**

Line 16, change:
```
#   set-date <item-id> <field-id> <date>  Set project date field
```
to:
```
#   set-date <item-id> <field-id>         Set project date field (always today)
```

**Step 2: Change `cmd_set_date` to resolve date internally**

Replace lines 239-249 with the same implementation as Task 1:
```bash
cmd_set_date() {
  local item="$1" field="$2"
  local date
  date=$(date +%Y-%m-%d)
  graphql '
    mutation($project: ID!, $item: ID!, $field: ID!, $date: Date!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $project, itemId: $item,
        fieldId: $field, value: {date: $date}
      }) { projectV2Item { id } }
    }' -f project="$PROJECT_ID" -f item="$item" \
       -f field="$field" -f date="$date"
}
```

**Step 3: Commit**

```bash
git add plugins/trivy-audit/scripts/github-projects.sh
git commit -m "feat: trivy-audit set-date always uses today's date"
```

---

### Task 3: Add `--body-file` to github-project-tools script

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:8` (usage header for issue-create)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:139-154` (`cmd_issue_create`)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:14` (usage header for issue-edit)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:156-167` (`cmd_issue_edit`)

**Step 1: Update usage headers**

Line 13, change:
```
#   issue-create --title T --body B       Create issue (optional --label)
```
to:
```
#   issue-create --title T --body B       Create issue (optional --label, --body-file)
```

Line 14, change:
```
#   issue-edit <number> --body B          Update issue body
```
to:
```
#   issue-edit <number> --body B          Update issue body (or --body-file)
```

**Step 2: Add `--body-file` to `cmd_issue_create`**

In the case block (line 142-146), add after the `--body)` case:
```bash
      --body-file) body=$(cat "$2"); shift 2 ;;
```

**Step 3: Add `--body-file` to `cmd_issue_edit`**

In the case block (line 160-162), add after the `--body)` case:
```bash
      --body-file) body=$(cat "$2"); shift 2 ;;
```

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat: add --body-file flag to issue-create and issue-edit"
```

---

### Task 4: Add `--body-file` to trivy-audit script

**Files:**
- Modify: `plugins/trivy-audit/scripts/github-projects.sh:8` (usage header for issue-create)
- Modify: `plugins/trivy-audit/scripts/github-projects.sh:9` (usage header for issue-edit)
- Modify: `plugins/trivy-audit/scripts/github-projects.sh:98-113` (`cmd_issue_create`)
- Modify: `plugins/trivy-audit/scripts/github-projects.sh:115-126` (`cmd_issue_edit`)

**Step 1: Update usage headers**

Line 8, change:
```
#   issue-create --title T --body B       Create issue (optional --label)
```
to:
```
#   issue-create --title T --body B       Create issue (optional --label, --body-file)
```

Line 9, change:
```
#   issue-edit <number> --body B          Update issue body
```
to:
```
#   issue-edit <number> --body B          Update issue body (or --body-file)
```

**Step 2: Add `--body-file` to `cmd_issue_create`**

In the case block (lines 101-105), add after the `--body)` case:
```bash
      --body-file) body=$(cat "$2"); shift 2 ;;
```

**Step 3: Add `--body-file` to `cmd_issue_edit`**

In the case block (lines 119-121), add after the `--body)` case:
```bash
      --body-file) body=$(cat "$2"); shift 2 ;;
```

**Step 4: Commit**

```bash
git add plugins/trivy-audit/scripts/github-projects.sh
git commit -m "feat: trivy-audit add --body-file flag to issue-create and issue-edit"
```

---

### Task 5: Update start-implementation SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:4` (allowed-tools frontmatter)
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:70` (set-date call)
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:91` (set-date call for parent)

**Step 1: Remove `Bash(date:*)` from allowed-tools**

Line 4, change:
```
allowed-tools: Bash(github-projects.sh:*), Bash(find:*), Bash(date:*), Bash(git:*), Bash(basename:*)
```
to:
```
allowed-tools: Bash(github-projects.sh:*), Bash(find:*), Bash(git:*), Bash(basename:*)
```

**Step 2: Update set-date calls**

Line 70, change:
```
      scripts/github-projects.sh set-date "$ITEM_ID" "$START_FIELD" "$(date +%Y-%m-%d)"
```
to:
```
      scripts/github-projects.sh set-date "$ITEM_ID" "$START_FIELD"
```

Line 91, change:
```
        scripts/github-projects.sh set-date "$PARENT_ITEM" "$START_FIELD" "$(date +%Y-%m-%d)"
```
to:
```
        scripts/github-projects.sh set-date "$PARENT_ITEM" "$START_FIELD"
```

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat: remove command substitution from start-implementation skill"
```

---

### Task 6: Update end-implementation SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:4` (allowed-tools frontmatter)
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:88` (set-date call)
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:125` (set-date call for parent)

**Step 1: Remove `Bash(date:*)` from allowed-tools**

Line 4, change:
```
allowed-tools: Bash(github-projects.sh:*), Bash(find:*), Bash(date:*)
```
to:
```
allowed-tools: Bash(github-projects.sh:*), Bash(find:*)
```

**Step 2: Update set-date calls**

Line 88, change:
```
      scripts/github-projects.sh set-date "$ITEM_ID" "$END_FIELD" "$(date +%Y-%m-%d)"
```
to:
```
      scripts/github-projects.sh set-date "$ITEM_ID" "$END_FIELD"
```

Line 125, change:
```
        scripts/github-projects.sh set-date "$PARENT_ITEM" "$END_FIELD" "$(date +%Y-%m-%d)"
```
to:
```
        scripts/github-projects.sh set-date "$PARENT_ITEM" "$END_FIELD"
```

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat: remove command substitution from end-implementation skill"
```

---

### Task 7: Update trivy-audit report-writer to use `--body-file`

**Files:**
- Modify: `plugins/trivy-audit/skills/report/prompts/report-writer.md:42-61` (sub-issue creation)
- Modify: `plugins/trivy-audit/skills/report/prompts/report-writer.md:78-101` (parent issue creation)
- Modify: `plugins/trivy-audit/skills/report/prompts/report-writer.md:165-182` (update existing parent)

**Step 1: Replace sub-issue creation heredoc (lines 42-62)**

Replace the code block with:

````markdown
First, use the Write tool to save the issue body to `/tmp/trivy-audit-sub-issue.md`:

```markdown
<!-- action-id: {slug} -->

**Severity:** Critical/High/Medium/Low | **Risk:** safe/needs investigation/breaking changes

## Remediation
[Specific steps]

## CVEs Fixed
- CVE-XXXX-XXXXX (severity, CVSS X.X)
- ...

## Ansible
`roles/[role]/defaults/main.yml` → `variable_name`
```

Then create the issue:

```bash
scripts/github-projects.sh issue-create \
  --label "trivy-audit" \
  --title "[Action title, e.g., Upgrade Trivy Operator 0.31.0 → 0.32.0]" \
  --body-file /tmp/trivy-audit-sub-issue.md
```
````

**Step 2: Replace parent issue creation heredoc (lines 78-101)**

Replace with:

````markdown
First, use the Write tool to save the parent issue body to `/tmp/trivy-audit-parent.md`:

```markdown
<!-- trivy-audit-parent -->

## Summary
- Total: X critical, Y high CVEs across Z images; N with fixes available
- N components outdated (K with breaking changes, M need investigation)
- P config audit failures (Q need fixing, R accepted risks)
- Top priority: [one-sentence recommendation]

## Action Plan
| # | Action | Severity | Risk | Status |
|---|--------|----------|------|--------|
| 1 | [Action title](https://github.com/elahti/deneb/issues/N) | Critical | safe | Open |
| 2 | [Action title](https://github.com/elahti/deneb/issues/N) | High | low | Open |
...

*Last scanned: YYYY-MM-DD*
```

Then create the issue:

```bash
scripts/github-projects.sh issue-create \
  --label "trivy-audit" \
  --title "Trivy Security Audit — YYYY-MM-DD" \
  --body-file /tmp/trivy-audit-parent.md
```
````

**Step 3: Replace update existing parent heredoc (lines 165-182)**

Replace with:

````markdown
First, use the Write tool to save the updated parent body to `/tmp/trivy-audit-parent-update.md`:

```markdown
<!-- trivy-audit-parent -->

## Summary
[Updated summary with fresh numbers]

## Action Plan
| # | Action | Severity | Risk | Status |
|---|--------|----------|------|--------|
| 1 | [Action title](https://github.com/elahti/deneb/issues/N) | Critical | safe | :white_check_mark: Done |
| 2 | [Action title](https://github.com/elahti/deneb/issues/N) | High | safe | Open |
...

*Last scanned: YYYY-MM-DD*
```

Then update the issue:

```bash
scripts/github-projects.sh issue-edit <parent_number> --body-file /tmp/trivy-audit-parent-update.md
```
````

**Step 4: Commit**

```bash
git add plugins/trivy-audit/skills/report/prompts/report-writer.md
git commit -m "feat: trivy-audit report-writer uses --body-file instead of heredoc substitution"
```

---

### Task 8: Update conventions and setup docs

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/conventions.md`
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/conventions.md`
- Modify: `plugins/trivy-audit/skills/report/prompts/report-writer.md:217-222` (Important Notes section)

**Step 1: Add no-command-substitution convention to all three conventions.md files**

Add after the first line (the "All bash commands" convention):
```
- **No command substitution** in bash commands — never use `$(...)`. If logic is needed, add it to the wrapper script. Use `--body-file` for multi-line content (write to a temp file with the Write tool first).
```

**Step 2: Update trivy-audit report-writer Important Notes**

Add the same convention after line 219:
```
- **No command substitution** in bash commands — never use `$(...)`. Use `--body-file` for multi-line bodies (write to a named temp file in `/tmp/` with the Write tool first).
```

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/prompts/conventions.md \
        plugins/github-project-tools/skills/end-implementation/prompts/conventions.md \
        plugins/github-project-tools/skills/add-issue/prompts/conventions.md \
        plugins/trivy-audit/skills/report/prompts/report-writer.md
git commit -m "docs: add no-command-substitution convention to all skills"
```
