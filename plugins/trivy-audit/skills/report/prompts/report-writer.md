# Report Writer

You are assembling the final Trivy security audit results from sections written by three analysis teammates. Your job is to read their section files, create an action plan, and publish everything as GitHub Issues in the Deneb project.

## Instructions

1. Read the three section files:
   - `/tmp/trivy-audit/report-cves.md` — Critical & High CVEs section
   - `/tmp/trivy-audit/report-staleness.md` — Version Staleness section
   - `/tmp/trivy-audit/report-config.md` — Config Audit Failures section

2. Write the Summary by counting across all three:
   - Total critical and high CVEs, how many have fixes
   - Number of outdated components and their risk levels
   - Number of config audit failures by classification
   - One-sentence "top priority" recommendation

3. Create the Action Plan by cross-referencing all sections:
   - Group related items: if upgrading component X fixes CVEs Y and Z, that's one action item
   - Sort by severity (Critical > High > Medium > Low), then by CVSS score within same severity
   - Each action item gets a stable slug (e.g., `upgrade-trivy-operator`, `harden-oauth2-proxy-security-context`)
   - Each action item should reference the specific CVEs it fixes and the upgrade risk

4. Create or update GitHub Issues (see workflow below).

## GitHub Issue Workflow

### Check for existing open audit

```bash
scripts/trivy-audit-gh.sh list-open-parents
```

If the result array is non-empty, an open parent exists — go to the **Update existing** section. Otherwise, go to **Create fresh**.

### Create fresh

**Create sub-issues first** (one per action plan item, so you have issue numbers for the parent table):

For each action item, create an issue. Use a stable `action-id` slug derived from the action (component name + action type, e.g., `upgrade-trivy-operator`, `harden-oauth2-proxy-security-context`, `monitor-k0s-release`).

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

The output is the sub-issue URL (e.g., `https://github.com/elahti/deneb/issues/16`). Extract the issue number from the URL path.

**Create parent issue:**

After creating all sub-issues (so you have their issue numbers), build the parent body with both the Summary and the Action Plan table.

The Action Plan table is built from your action plan data. For each action item, sorted by severity (Critical > High > Medium > Low), then by CVSS score:

```
| <row_number> | [<title>](https://github.com/elahti/deneb/issues/<issue_number>) | <severity> | <risk> | Open |
```

All items start as `Open` since they were just created.

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

The output is the parent issue URL. Extract the parent issue number from the URL path.

**Important:** Create sub-issues first, then create the parent issue with the table, then link sub-issues to parent. This ensures you have issue numbers for the table links.

**Link sub-issues to parent** using the wrapper script. For each sub-issue:

First, get the parent node ID:

```bash
scripts/github-projects.sh issue-view "$PARENT_NUMBER" --json id --jq '.id'
```

Save the output as `PARENT_ID`.

Then, get the sub-issue node ID:

```bash
scripts/github-projects.sh issue-view "$SUB_NUMBER" --json id --jq '.id'
```

Save the output as `SUB_ID`.

Then, link the sub-issue to the parent:

```bash
scripts/trivy-audit-gh.sh link-sub-issue "$PARENT_ID" "$SUB_ID"
```

**Add all issues to the Deneb project** and set Status = "Todo":

For each issue (parent + all sub-issues):

First, get the issue node ID:

```bash
scripts/github-projects.sh issue-view <number> --json id --jq '.id'
```

Save the output as `ISSUE_ID`.

Then, add it to the project:

```bash
scripts/github-projects.sh add-to-project "$ISSUE_ID"
```

Save the output as `ITEM_ID`.

Then, set the status:

```bash
scripts/github-projects.sh set-status "$ITEM_ID" todo
```

### Update existing

**Update parent body:**

Rebuild the Action Plan table from your action plan data cross-referenced with existing sub-issue state. For each action item, sorted by severity (Critical > High > Medium > Low), then by CVSS score:
- If the sub-issue is CLOSED: status = `:white_check_mark: Done`
- If the sub-issue is OPEN: status = `Open`

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

**List existing sub-issues:**

First, get the parent node ID:

```bash
scripts/github-projects.sh issue-view <parent_number> --json id --jq '.id'
```

Save the output as `PARENT_ID`.

Then, get the sub-issues:

```bash
scripts/trivy-audit-gh.sh get-sub-issues "$PARENT_ID"
```

**Match by action-id:** For each existing sub-issue, extract the `<!-- action-id: slug -->` from its body using jq. Match against your action plan slugs.

- **Matched:** Update the sub-issue body with fresh data via `scripts/github-projects.sh issue-edit <number> --body "..."`
- **Unmatched new action items:** Create new sub-issue, link to parent, add to project (same as "Create fresh" flow above)

## After Creating/Updating Issues

1. Clean up temporary files:
   ```bash
   rm -rf /tmp/trivy-audit
   ```

2. Mark your task as completed and message the lead with:
   - Parent issue URL
   - Count of sub-issues created/updated
   - Brief summary (e.g., "Created 11 sub-issues: 3 upgrade, 2 harden, 2 monitor")

## Important Notes

- **Script invocation:** The resolved script path MUST be the literal first token of every bash command — e.g. `scripts/github-projects.sh issue-assign 14`. NEVER split the path into a variable like `SCRIPTS=... && $SCRIPTS/github-projects.sh ...`. Claude Code matches permissions by the first token; variable-wrapped paths produce a different fingerprint every time, forcing repeated approval prompts.
- **No command substitution** in bash commands — never use `$(...)`. Use `--body-file` for multi-line bodies (write to a named temp file in `/tmp/` with the Write tool first).
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **Generic GitHub operations** (issue-create, issue-view, issue-edit, add-to-project, set-status) go through `scripts/github-projects.sh`. **Trivy-specific operations** (list-open-parents, link-sub-issue, get-sub-issues) go through `scripts/trivy-audit-gh.sh`. Never call `gh` directly.
- The report skill **never** closes issues, sets dates, or changes status beyond initial "Todo". It only creates and updates issue content.
