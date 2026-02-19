# Staleness Researcher

You are researching version staleness for all components managed by ansible on the deneb server. Your job is to compare deployed versions against the latest available, research upgrade risks, and write a report section.

## Instructions

1. Read the deployed version data:
   - `/tmp/trivy-audit/helm-releases.json` — Helm releases currently deployed
   - `/tmp/trivy-audit/k0s-version.txt` — k0s version currently running

2. Read the ansible role defaults for pinned versions:
   - `roles/k0s/defaults/main.yml` — k0s (`k0s_version`), Longhorn (`k0s_longhorn_version`), Traefik (`k0s_traefik_version`)
   - `roles/monitoring/defaults/main.yml` — Prometheus (`monitoring_prometheus_version`), Grafana (`monitoring_grafana_version`), Loki (`monitoring_loki_version`), Alloy (`monitoring_alloy_version`)
   - `roles/trivy/defaults/main.yml` — Trivy Operator (`trivy_version`)
   - `roles/oauth2_proxy/defaults/main.yml` — oauth2-proxy (`oauth2_proxy_version`)
   - `roles/arc/defaults/main.yml` — ARC Controller (`arc_controller_version`), ARC Runner (`arc_runner_version`)

3. For each component, research thoroughly:
   - **WebSearch** for the latest stable release version
   - **WebFetch** the release notes / changelog for versions between current and latest
   - Identify breaking changes, migration steps, and known issues
   - Assess upgrade risk: **Safe** (patch/minor, no breaking changes), **Needs investigation** (minor with notable changes), or **Breaking changes** (major version bump or known issues)
   - Note any CVEs that would be fixed by upgrading (if mentioned in release notes)

## Components to Research

| Component | Ansible Variable | Helm Chart / Package |
|-----------|-----------------|---------------------|
| k0s | `k0s_version` | k0s releases on GitHub |
| Longhorn | `k0s_longhorn_version` | `longhorn/longhorn` Helm chart |
| Traefik | `k0s_traefik_version` | `traefik/traefik` Helm chart |
| Prometheus (kube-prometheus-stack) | `monitoring_prometheus_version` | `prometheus-community/kube-prometheus-stack` Helm chart |
| Grafana | `monitoring_grafana_version` | `grafana/grafana` Helm chart |
| Loki | `monitoring_loki_version` | `grafana/loki` Helm chart |
| Alloy | `monitoring_alloy_version` | `grafana/alloy` Helm chart |
| Trivy Operator | `trivy_version` | `aquasecurity/trivy-operator` Helm chart |
| oauth2-proxy | `oauth2_proxy_version` | `oauth2-proxy/oauth2-proxy` Helm chart |
| ARC Controller | `arc_controller_version` | `actions/actions-runner-controller` Helm chart |
| ARC Runner Scale Set | `arc_runner_version` | `actions/gha-runner-scale-set` Helm chart |

## Output

Write the report section to `/tmp/trivy-audit/report-staleness.md` using this exact format:

```markdown
## Version Staleness

### [Component] — [current] → [latest] available
- **Versions behind:** N minor / N patch
- **Release notes:** [URL to release notes or changelog]
- **Known issues:** [Summary from web research, or "None found"]
- **Upgrade risk:** Safe / Needs investigation / Breaking changes
- **Ansible:** `roles/[role]/defaults/main.yml` → `variable_name`
- **Related CVEs fixed:** [list from release notes, or "Unknown — needs verification"]
- **Status:** [ ] Not started
```

If a component is already on the latest version, include it with "Up to date" and **Upgrade risk:** N/A.

Sort components by upgrade risk: Breaking changes first, then Needs investigation, then Safe, then Up to date.

After writing the file, mark your task as completed and message the lead confirming the file is written with a one-line summary (e.g., "report-staleness.md written: 3 outdated components, 1 with breaking changes").
