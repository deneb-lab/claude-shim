#!/usr/bin/env bash
# Gather Trivy audit data from the deneb server via claude-remote gateway
# Saves files to /tmp/trivy-audit/ for the trivy-audit skill to process

set -euo pipefail

SERVER="esko@phoebe.fi"
REMOTE="claude-remote"
OUTDIR="/tmp/trivy-audit"

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

echo "Gathering vulnerability reports..." >&2
ssh "$SERVER" "$REMOTE" kubectl get vulnerabilityreports -A -o json \
    > "$OUTDIR/vuln-reports.json" 2>/dev/null || {
    echo "Error: Failed to get vulnerability reports" >&2
    exit 1
}

echo "Gathering config audit reports..." >&2
ssh "$SERVER" "$REMOTE" kubectl get configauditreports -A -o json \
    > "$OUTDIR/config-audits.json" 2>/dev/null || {
    echo "Error: Failed to get config audit reports" >&2
    exit 1
}

echo "Gathering Helm releases..." >&2
ssh "$SERVER" "$REMOTE" helm-list \
    > "$OUTDIR/helm-releases.json" 2>/dev/null || {
    echo "Error: Failed to get Helm releases" >&2
    exit 1
}

echo "Gathering k0s version..." >&2
ssh "$SERVER" "$REMOTE" k0s-version \
    > "$OUTDIR/k0s-version.txt" 2>/dev/null || {
    echo "Error: Failed to get k0s version" >&2
    exit 1
}

# Step 1: Extract critical and high CVEs per pod (intermediate)
echo "Extracting critical and high vulnerabilities..." >&2
jq '[.items[] | {
    namespace: .metadata.namespace,
    resource_kind: .metadata.labels["trivy-operator.resource.kind"],
    resource_name: .metadata.labels["trivy-operator.resource.name"],
    container: .metadata.labels["trivy-operator.container.name"],
    image: (.report.artifact.repository + ":" + .report.artifact.tag),
    summary: .report.summary,
    vulnerabilities: [.report.vulnerabilities[] |
        select(.severity == "CRITICAL" or .severity == "HIGH") | {
            vulnerabilityID,
            severity,
            score,
            title,
            resource,
            installedVersion,
            fixedVersion,
            primaryLink
        }]
} | select(.vulnerabilities | length > 0)]' \
    "$OUTDIR/vuln-reports.json" > "$OUTDIR/vuln-critical-high.json"

# Step 2: Deduplicate CVEs — flatten and group by CVE ID, aggregate images
# Produces a flat array directly readable by the agent
echo "Deduplicating vulnerabilities..." >&2
jq -f /dev/stdin "$OUTDIR/vuln-critical-high.json" > "$OUTDIR/vulns-deduped.json" <<'JQFILTER'
[.[] | .image as $img | .namespace as $ns | .vulnerabilities[] | {
    vuln_id: .vulnerabilityID,
    severity: .severity,
    score: .score,
    title: .title,
    resource: .resource,
    installed: .installedVersion,
    fixed: .fixedVersion,
    link: .primaryLink,
    image: $img,
    namespace: $ns
}] | group_by(.vuln_id) | map({
    vuln_id: .[0].vuln_id,
    severity: .[0].severity,
    score: ([.[].score] | map(select(. != null)) | if length > 0 then max else 0 end),
    title: .[0].title,
    resource: .[0].resource,
    installed: ([.[].installed] | unique | join(", ")),
    fixed: .[0].fixed,
    link: .[0].link,
    images: [.[] | {image, namespace}] | unique
}) | sort_by(-(if .score then .score else 0 end))
JQFILTER

# Step 3: Extract and group config audit failures by check ID
# Produces a flat array directly readable by the agent
echo "Extracting and grouping config audit failures..." >&2
jq -f /dev/stdin "$OUTDIR/config-audits.json" > "$OUTDIR/config-grouped.json" <<'JQFILTER'
[.items[] | .metadata.namespace as $ns |
    .metadata.labels["trivy-operator.resource.kind"] as $rk |
    .metadata.labels["trivy-operator.resource.name"] as $rn |
    .report.checks[] | select(.success == false) | {
        check_id: .checkID,
        severity: .severity,
        title: .title,
        description: .description,
        category: .category,
        resource: $rn,
        kind: $rk,
        namespace: $ns
    }
] | group_by(.check_id) | map({
    check_id: .[0].check_id,
    severity: .[0].severity,
    title: .[0].title,
    description: .[0].description,
    count: length,
    resources: [.[] | "\(.namespace)/\(.kind)/\(.resource)"] | unique
}) | sort_by(
    if .severity == "CRITICAL" then 0
    elif .severity == "HIGH" then 1
    elif .severity == "MEDIUM" then 2
    else 3 end
)
JQFILTER

# Summary counts
echo "" >&2
unique_cves=$(jq 'length' "$OUTDIR/vulns-deduped.json")
crit_count=$(jq '[.[] | select(.severity == "CRITICAL")] | length' "$OUTDIR/vulns-deduped.json")
high_count=$(jq '[.[] | select(.severity == "HIGH")] | length' "$OUTDIR/vulns-deduped.json")
check_count=$(jq 'length' "$OUTDIR/config-grouped.json")
fail_count=$(jq '[.[].count] | add' "$OUTDIR/config-grouped.json")

echo "Summary: $unique_cves unique CVEs ($crit_count critical, $high_count high), $check_count check types ($fail_count total failures)" >&2
echo "" >&2
echo "Files saved to $OUTDIR/:" >&2
echo "  vulns-deduped.json   - Unique CVEs, deduplicated and sorted by score (READ THIS)" >&2
echo "  config-grouped.json  - Config failures grouped by check ID (READ THIS)" >&2
echo "  helm-releases.json   - Helm releases" >&2
echo "  k0s-version.txt      - k0s version" >&2
echo "  vuln-critical-high.json  - Per-pod CVEs (intermediate, for debugging)" >&2
echo "  vuln-reports.json        - Raw vulnerability reports" >&2
echo "  config-audits.json       - Raw config audit reports" >&2
