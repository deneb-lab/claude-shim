Parse the argument. The user provides either:
- A plain issue number like `42`
- A full GitHub URL like `https://github.com/owner/repo/issues/42`

Extract the issue number from whichever format is provided.

**If a full URL was provided**, also extract the `owner/repo` from the URL path. Save this as `REPO_OVERRIDE` (e.g., `owner/repo`). When `REPO_OVERRIDE` is set, **prepend `--repo $REPO_OVERRIDE` before the subcommand in every subsequent script invocation**. For example:
```bash
<resolved-path> --repo owner/repo issue-view-full 42
```

If only a plain issue number was provided, keep the existing `REPO_OVERRIDE` from setup (if set). The URL-derived repo takes precedence over the config repo, which takes precedence over auto-detection.
