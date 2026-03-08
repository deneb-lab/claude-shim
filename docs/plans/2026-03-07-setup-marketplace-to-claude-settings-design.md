# Design: Add marketplace entry step to setup-quality-check-hook

**Issue:** [#83](https://github.com/elahti/deneb-marketplace/issues/83)

## Summary

Add a new Step 7 to the `setup-quality-check-hook` SKILL.md that prompts the user to add `extraKnownMarketplaces` entry to `.claude/settings.json`.

## What changes

**File:** `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md`

New Step 7 added after existing Step 6.

## Step 7: Configure Marketplace

1. Check if `.claude/settings.json` exists in the repository root.
2. If it exists, read it and check for `extraKnownMarketplaces.claude-shim-marketplace`:
   - **Entry exists with `autoUpdate: true`** — continue silently.
   - **Entry exists with `autoUpdate: false`** — ask user: "Marketplace auto-update is disabled. Enable it?" If yes, set `autoUpdate` to `true` and write back. If no, continue.
   - **Entry missing** — proceed to step 3.
3. If file doesn't exist or entry is missing, ask user: "Add claude-shim-marketplace to `.claude/settings.json` so this repository can discover plugins automatically?"
   - **Yes** — read existing file (or start with `{}`), merge in the `extraKnownMarketplaces` block preserving all other keys, write the file.
   - **No** — continue without changes.
4. The marketplace entry to add:
   ```json
   {
     "extraKnownMarketplaces": {
       "claude-shim-marketplace": {
         "source": {
           "source": "github",
           "repo": "deneb-lab/claude-shim"
         },
         "autoUpdate": true
       }
     }
   }
   ```
5. If any changes were made to `.claude/settings.json`, commit the file.

## What doesn't change

- No script changes
- No new prompt files
- No changes to other skills or plugins
- Steps 1–6 remain identical
