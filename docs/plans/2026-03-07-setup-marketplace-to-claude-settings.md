# Setup Marketplace to Claude Settings — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Step 7 to `setup-quality-check-hook` SKILL.md that prompts users to add `extraKnownMarketplaces` entry to `.claude/settings.json`.

**Architecture:** Single file edit — append a new step to an existing skill definition. No scripts, no code, no tests.

**Tech Stack:** Markdown (SKILL.md)

---

### Task 1: Add Step 7 to SKILL.md

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md:148-153` (after Step 6's closing message)

**Step 1: Add Step 7 section**

Append the following markdown after the Step 6 closing blockquote (after line 153) in `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md`:

````markdown

## Step 7: Configure Marketplace

Check if `.claude/settings.json` exists in the repository root.

**If the file exists**, read it and check for `extraKnownMarketplaces.claude-shim-marketplace`:

- **Entry exists with `autoUpdate: true`** — continue silently. No action needed.
- **Entry exists with `autoUpdate: false`** — use AskUserQuestion: "Marketplace auto-update is currently disabled in `.claude/settings.json`. Enable it?" If yes, set `autoUpdate` to `true`, preserve all other keys, and write the file back. If no, continue without changes.
- **Entry missing** — proceed to the prompt below.

**If the file does not exist or the entry is missing**, use AskUserQuestion: "Add claude-shim-marketplace to `.claude/settings.json` so this repository can discover plugins automatically?"

- **Yes** — read the existing file (or start with `{}`), merge in the marketplace entry below, preserve all other keys, and write the file.
- **No** — continue without changes.

The marketplace entry:

```json
{
  "extraKnownMarketplaces": {
    "claude-shim-marketplace": {
      "source": {
        "source": "github",
        "repo": "elahti/claude-shim"
      },
      "autoUpdate": true
    }
  }
}
```

If any changes were made to `.claude/settings.json`, commit the file with message: `"chore: add claude-shim-marketplace to .claude/settings.json"`.
````

**Step 2: Review the full SKILL.md**

Read the file end-to-end and verify:
- Step 7 follows naturally after Step 6
- Formatting is consistent with Steps 1–6 (heading level, bullet style, code blocks)
- No duplicate content

**Step 3: Commit**

```bash
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): add marketplace entry step to setup skill"
```
