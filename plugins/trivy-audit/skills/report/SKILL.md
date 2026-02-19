---
name: report
description: Audit Trivy vulnerabilities, check version staleness, review config audits, and create GitHub issues in the Deneb project
---

# Trivy Security Audit — Agent Team Coordinator

Run a comprehensive security audit of the deneb server using an agent team. You are the **team lead** — your job is to coordinate, not analyze. You never read data files yourself.

## Phase 1: Gather Data

Run the gathering script:

```bash
bash scripts/trivy-audit-gather.sh
```

This collects data via `claude-remote` and saves pre-processed files to `/tmp/trivy-audit/`. Do NOT read these files — teammates will read them.

Verify the script succeeded by checking its exit code and summary output.

## Phase 2: Create Team & Tasks

1. Create the agent team:
   ```
   TeamCreate: team_name="trivy-audit", description="Trivy security audit"
   ```

2. Create 4 tasks:
   - **Task A:** "Analyze critical and high CVEs" — for cve-analyst
   - **Task B:** "Research version staleness" — for staleness-researcher
   - **Task C:** "Audit config failures" — for config-auditor
   - **Task D:** "Create/update GitHub issues" — for report-writer (blocked by A, B, C)

   Set Task D as blocked by Tasks A, B, and C using `addBlockedBy`.

## Phase 3: Spawn Analysis Teammates

Read the prompt files and spawn 3 teammates **in parallel**:

1. Read `prompts/cve-analyst.md`
2. Read `prompts/staleness-researcher.md`
3. Read `prompts/config-auditor.md`

Then spawn all 3 using the Task tool:

```
Task: name="cve-analyst", team_name="trivy-audit",
      subagent_type="general-purpose", mode="bypassPermissions",
      prompt=<contents of cve-analyst.md>

Task: name="staleness-researcher", team_name="trivy-audit",
      subagent_type="general-purpose", mode="bypassPermissions",
      prompt=<contents of staleness-researcher.md>

Task: name="config-auditor", team_name="trivy-audit",
      subagent_type="general-purpose", mode="bypassPermissions",
      prompt=<contents of config-auditor.md>
```

Assign tasks to teammates using TaskUpdate (set owner to teammate name).

## Phase 4: Wait for Analysis Teammates

Teammates will message you when they finish. Wait for all 3 to complete their tasks. Do NOT read their output files — the report-writer will do that.

If a teammate reports an issue, help them resolve it by sending a message with guidance.

## Phase 5: Spawn Report Writer

Once all 3 analysis tasks are completed:

1. Read `prompts/report-writer.md`
2. Spawn the report-writer:

```
Task: name="report-writer", team_name="trivy-audit",
      subagent_type="general-purpose", mode="bypassPermissions",
      prompt=<contents of report-writer.md>
```

3. Assign Task D (create/update GitHub issues) to report-writer.

## Phase 6: Cleanup

After report-writer confirms the issues are created:

1. Send shutdown requests to all teammates
2. After all teammates have shut down, clean up:
   ```
   TeamDelete
   ```
3. Tell the user the audit is complete and share the parent issue URL.

## Important Notes

- **You are a pure coordinator.** Never read `/tmp/trivy-audit/*.json` or `*.md` data files.
- **Teammates handle all analysis.** Trust their output.
- **Use `mode: "bypassPermissions"`** when spawning teammates so they can read files and run commands without prompting.
- **The gather script uses `claude-remote`** — all server access is read-only.
- **If a teammate fails**, you can spawn a replacement with the same prompt.
