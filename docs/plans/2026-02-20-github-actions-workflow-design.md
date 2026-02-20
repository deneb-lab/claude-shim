# GitHub Actions Workflow for claude-shim

## Context

claude-shim has no CI/CD. Issue [deneb#34](https://github.com/elahti/deneb/issues/34) adds a GitHub Actions workflow using self-hosted ARC runners from the Deneb server, matching the pattern already established in the deneb repo.

## Design

### CI Docker Image

**File:** `claude-shim:.github/images/ci/Dockerfile`

Lightweight Debian-based image with only the tools needed for linting:

```dockerfile
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    jq \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*
```

- **Registry:** `registry.phoebe.fi/claude-shim/ci:latest`
- **Build:** `docker buildx build --platform linux/amd64 -t registry.phoebe.fi/claude-shim/ci:latest .github/images/ci/ --push`

### GitHub Actions Workflow

**File:** `claude-shim:.github/workflows/ci.yml`

```yaml
---
name: CI
"on": [push, pull_request]
jobs:
  lint:
    runs-on: claude-shim-runner
    container:
      image: registry.phoebe.fi/claude-shim/ci:latest
      credentials:
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    steps:
      - name: Checkout
        uses: actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8  # v6

      - name: Run shellcheck
        run: |
          find . -name '*.sh' -print0 | xargs -0 shellcheck

      - name: Validate JSON files
        run: |
          for f in $(find . -name '*.json' -not -path './.git/*'); do
            echo "Checking $f..."
            jq . "$f" > /dev/null
          done
```

- **Triggers:** Every push and pull request
- **Checks:** shellcheck on all `.sh` files, jq validation on all `.json` files
- **Check-only:** CI fails on issues, does not auto-fix

### ARC Runner Configuration (deneb side)

**File:** `deneb:roles/arc/defaults/main.yml` — add to `arc_runners`:

```yaml
  - name: claude-shim-runner
    repo: elahti/claude-shim
    min_runners: 1
    max_runners: 2
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "2Gi"
```

After editing, the user runs:
```bash
ansible-playbook playbooks/site.yml --tags k8s --ask-become-pass --ask-vault-pass
```

### Prerequisites

- `REGISTRY_USERNAME` and `REGISTRY_PASSWORD` secrets set in `elahti/claude-shim` GitHub repo settings
- Existing GitHub PAT in `arc-runners` namespace already covers `elahti/*` repos
- CI image must be built and pushed before the first workflow run

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CI behavior | Check only | Standard CI pattern; developers fix locally |
| CI image | Own image | Independent from deneb, includes only needed tools |
| Base image | debian:trixie-slim | Same Debian version as deneb's CI image |
| Linters | shellcheck + jq | Matches repo file types (shell + JSON), no new tooling |
| Triggers | push + pull_request | Same as deneb, catches issues early |
| Dockerfile path | .github/images/ci/ | Same convention as deneb |
| Runner sizing | 256Mi/2Gi, 1-2 runners | Lightweight CI, matches deneb-runner sizing |
