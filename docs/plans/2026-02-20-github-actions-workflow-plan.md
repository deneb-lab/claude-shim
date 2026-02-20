# GitHub Actions Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add CI to claude-shim using self-hosted ARC runners from the Deneb server.

**Architecture:** Three deliverables across two repos: (1) CI Docker image and GitHub Actions workflow in claude-shim, (2) ARC runner scale set configuration in deneb. The workflow runs shellcheck and jq validation on every push/PR.

**Tech Stack:** GitHub Actions, ARC (Actions Runner Controller), Docker, shellcheck, jq

---

### Task 1: Create CI Docker image (claude-shim)

**Files:**
- Create: `.github/images/ci/Dockerfile`

**Step 1: Create the Dockerfile**

```dockerfile
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    jq \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*
```

**Step 2: Commit**

```bash
git add .github/images/ci/Dockerfile
git commit -m "feat: add CI Docker image with shellcheck and jq"
```

**Note:** The image must be built and pushed manually before the workflow can run:
```bash
docker buildx build --platform linux/amd64 \
  -t registry.phoebe.fi/claude-shim/ci:latest \
  .github/images/ci/ --push
```

---

### Task 2: Create GitHub Actions workflow (claude-shim)

**Files:**
- Create: `.github/workflows/ci.yml`

**Reference:** Deneb's CI workflow at `deneb:.github/workflows/ci.yml`

**Step 1: Create the workflow file**

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

**Step 2: Validate the workflow YAML**

The workflow file is plain YAML (not Ansible), so validate with:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

**Step 3: Run shellcheck locally to verify all scripts pass**

```bash
find . -name '*.sh' -print0 | xargs -0 shellcheck
```

If any scripts fail, fix them before committing.

**Step 4: Validate all JSON files locally**

```bash
for f in $(find . -name '*.json' -not -path './.git/*'); do echo "Checking $f..."; jq . "$f" > /dev/null; done
```

**Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: add GitHub Actions CI workflow with shellcheck and jq validation"
```

---

### Task 3: Add ARC runner configuration (deneb)

**Files:**
- Modify: `roles/arc/defaults/main.yml:48` (after the last `arc_runners` entry)

**Step 1: Create feature branch in deneb**

```bash
cd /workspace/deneb
git checkout -b feat/github-actions-workflow
```

**Step 2: Add runner entry to `arc_runners` list**

Add after the `devcontainer-runner` entry in `roles/arc/defaults/main.yml`:

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

**Step 3: Validate with ansible-lint**

```bash
ansible-lint roles/arc/defaults/main.yml
```

**Step 4: Commit**

```bash
git add roles/arc/defaults/main.yml
git commit -m "feat(arc): add claude-shim-runner scale set"
```

**Note:** After merging, the user must deploy with:
```bash
ansible-playbook playbooks/site.yml --tags k8s --ask-become-pass --ask-vault-pass
```

---

### Task 4: Fix any shellcheck issues in existing scripts

**Files:**
- Potentially modify: `plugins/github-project-tools/scripts/github-projects.sh`
- Potentially modify: `plugins/trivy-audit/scripts/github-projects.sh`
- Potentially modify: `plugins/trivy-audit/scripts/trivy-audit-gather.sh`
- Potentially modify: `plugins/trivy-audit/scripts/trivy-audit-gh.sh`

**Step 1: Run shellcheck and capture output**

```bash
shellcheck plugins/github-project-tools/scripts/github-projects.sh
shellcheck plugins/trivy-audit/scripts/github-projects.sh
shellcheck plugins/trivy-audit/scripts/trivy-audit-gather.sh
shellcheck plugins/trivy-audit/scripts/trivy-audit-gh.sh
```

**Step 2: Fix any issues found**

Apply fixes. Scripts already use `# shellcheck disable=` for intentional suppressions — respect those.

**Step 3: Commit fixes (if any)**

```bash
git add plugins/
git commit -m "fix: resolve shellcheck warnings in plugin scripts"
```

---

### Task 5: Manual setup steps (user action required)

These steps cannot be automated by Claude:

1. **Build and push CI image:**
   ```bash
   docker buildx build --platform linux/amd64 \
     -t registry.phoebe.fi/claude-shim/ci:latest \
     .github/images/ci/ --push
   ```

2. **Set GitHub repo secrets** in `elahti/claude-shim` settings:
   - `REGISTRY_USERNAME` — registry.phoebe.fi username
   - `REGISTRY_PASSWORD` — registry.phoebe.fi password

3. **Deploy ARC runner** (after deneb changes are merged):
   ```bash
   ansible-playbook playbooks/site.yml --tags k8s --ask-become-pass --ask-vault-pass
   ```

4. **Verify:** Push a commit to claude-shim and confirm the CI workflow runs on the self-hosted runner.
