# Add Renovate to claude-shim

## Context

Issue #9. The claude-shim repo has no automated dependency update tooling. Dependencies that need tracking:

- GitHub Actions SHA pins in `.github/workflows/ci.yml`
- Dockerfile base image (`debian:trixie-slim`) and tools in `.github/images/ci/Dockerfile`
- Python dependencies in `plugins/quality-check-hook/hook/pyproject.toml`
- Lock file (`uv.lock`) maintenance

## Decision

Add `renovate.json` at repo root, following the established pattern from stellaris-stats, deneb, and devcontainer repos. Add `helpers:pinGitHubActionDigestsToSemver` preset for better GitHub Action update readability.

## Configuration

Single file: `renovate.json`

Presets:
- `config:best-practices` — Renovate recommended defaults
- `customManagers:dockerfileVersions` — tracks base images and curl-piped installers
- `helpers:pinGitHubActionDigestsToSemver` — shows semver tags alongside SHA pins

Behavior:
- Weekly schedule: Mondays before 6am UTC
- Non-major updates: grouped into one PR, automerged
- Major updates: grouped into one PR, manual review required
- Vulnerability alerts: immediate, automerged, labeled `security`
- Lock file maintenance: enabled, automerged
- Semantic commit messages enabled
- Private registry images (`registry.phoebe.fi`) disabled

## What gets tracked

| Dependency | Source | Manager |
|---|---|---|
| `actions/checkout` SHA pin | `.github/workflows/ci.yml` | GitHub Actions |
| `debian:trixie-slim` | `.github/images/ci/Dockerfile` | dockerfileVersions |
| `pydantic`, `wcmatch` | `pyproject.toml` | PEP 621 |
| `pyright`, `pytest`, `ruff` | `pyproject.toml` (dev) | PEP 621 |
| `uv` installer | `Dockerfile` | dockerfileVersions |
| `uv.lock` | lock file | Lock file maintenance |

## What gets ignored

- `registry.phoebe.fi/claude-shim/ci:latest` — private registry, disabled by package rule
