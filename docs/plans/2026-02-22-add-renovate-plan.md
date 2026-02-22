# Add Renovate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Renovate dependency update bot configuration to claude-shim.

**Architecture:** Single `renovate.json` at repo root, following the established pattern from other elahti repos. No code changes, just configuration.

**Tech Stack:** Renovate Bot, JSON

---

### Task 1: Create renovate.json

**Files:**
- Create: `renovate.json`

**Step 1: Create the config file**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:best-practices",
    "customManagers:dockerfileVersions",
    "helpers:pinGitHubActionDigestsToSemver"
  ],
  "labels": ["dependencies"],
  "lockFileMaintenance": {
    "enabled": true,
    "automerge": true
  },
  "platformAutomerge": true,
  "packageRules": [
    {
      "description": "Ignore private registry images",
      "matchDatasources": ["docker"],
      "matchPackagePatterns": ["^registry\\.phoebe\\.fi/"],
      "enabled": false
    },
    {
      "description": "Group all non-major updates into a single PR",
      "groupName": "all non-major dependencies",
      "matchUpdateTypes": ["minor", "patch", "digest", "pin"],
      "automerge": true
    },
    {
      "description": "Group all major updates into a single PR (requires manual review)",
      "groupName": "all major dependencies",
      "matchUpdateTypes": ["major"],
      "automerge": false
    }
  ],
  "rangeStrategy": "pin",
  "schedule": ["before 6am on monday"],
  "semanticCommits": "enabled",
  "timezone": "UTC",
  "vulnerabilityAlerts": {
    "automerge": true,
    "enabled": true,
    "labels": ["security"],
    "schedule": ["at any time"]
  }
}
```

**Step 2: Validate the JSON**

Run: `jq . renovate.json`
Expected: Valid JSON output, no parse errors.

**Step 3: Commit**

```bash
git add renovate.json
git commit -m "feat: add Renovate configuration for dependency updates"
```

### Task 2: Verify CI passes

**Step 1: Run the JSON validation that CI runs**

Run: `find . -name '*.json' -not -path './.git/*' -exec jq . {} \; > /dev/null`
Expected: No errors. The new `renovate.json` passes the same validation CI uses.

**Step 2: Verify shellcheck still passes**

Run: `find . -name '*.sh' -print0 | xargs -0 shellcheck`
Expected: No new errors (sanity check — we didn't touch any scripts).
