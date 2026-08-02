#!/bin/bash
# Script to generate renovate-merged.json locally (mimics GitHub Actions workflow)

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║        Generating renovate-merged.json Locally                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

# Step 1: Generate Black Duck rules (Go/npm packages - Type 1 & 2)
echo "1️⃣  Generating Black Duck rules (Go/npm)..."
python3 security-tooling/generate_renovate_rules.py \
    security-tooling/blackduck_report.json \
    > /dev/null 2>&1
echo "   ✓ security-tooling/generated/renovate-blackduck-generated.json"
echo

# Step 2: Generate container image rules (Type 5)
echo "2️⃣  Generating container image rules..."
python3 security-tooling/scan_container_images.py > /dev/null 2>&1 || true
if [ -f "security-tooling/generated/renovate-container-images.json" ]; then
    echo "   ✓ security-tooling/generated/renovate-container-images.json"
else
    echo "   ⚠️  No container image rules generated"
fi
echo

# Step 3: Generate Dockerfile OS package rules (Type 3 & 4)
echo "3️⃣  Generating Dockerfile OS package rules..."
python3 security-tooling/generate_dockerfile_rules.py \
    security-tooling/blackduck_report.json \
    security-tooling/component_ownership.json \
    -o security-tooling/generated/renovate-dockerfile-regex.json \
    > /dev/null 2>&1
echo "   ✓ security-tooling/generated/renovate-dockerfile-regex.json"
echo

# Step 4: Detect base image vulnerabilities
echo "4️⃣  Detecting base image vulnerabilities..."
python3 security-tooling/detect_base_image_vulns.py > /dev/null 2>&1 || true
if [ -f "security-tooling/generated/vuln-categorization.json" ]; then
    base_image_count=$(python3 -c "import json; data=json.load(open('security-tooling/generated/vuln-categorization.json')); print(len(data.get('base_image_vulns', [])))")
    if [ "$base_image_count" -gt "0" ]; then
        echo "   Found $base_image_count base image vulnerability(ies)"
        echo "   Generating Renovate regex for base image upgrades..."
        python3 security-tooling/generate_upgrade_regex.py > /dev/null 2>&1
        echo "   ✓ security-tooling/generated/renovate-base-image-upgrades.json"
    else
        echo "   No base image vulnerabilities found"
    fi
else
    echo "   ⚠️  No vuln-categorization.json found"
fi
echo

# Step 5: Generate reviewer assignments
echo "5️⃣  Generating reviewer assignments..."
python3 security-tooling/manage_reviewers.py generate-renovate \
    security-tooling/blackduck_report.json \
    --output security-tooling/generated/renovate-reviewers.json \
    > /dev/null 2>&1
echo "   ✓ security-tooling/generated/renovate-reviewers.json"
echo

# Step 6: Generate base image rules (Type 6 - prebuilt images)
echo "6️⃣  Generating base image rules..."
python3 security-tooling/generate_base_image_rules.py \
    > /dev/null 2>&1
echo "   ✓ security-tooling/generated/renovate-base-image-rules.json"
echo

# Step 7: Merge all configurations (matches GitHub Actions workflow)
echo "7️⃣  Merging all configurations..."
python3 security-tooling/merge_renovate_config.py > /dev/null 2>&1 || python3 << 'PYEND'
import json

# Read base Black Duck rules
with open('security-tooling/generated/renovate-blackduck-generated.json') as f:
    blackduck_rules = json.load(f)

# Read container image rules (optional)
container_rules = {}
try:
    with open('security-tooling/generated/renovate-container-images.json') as f:
        container_rules = json.load(f)
except FileNotFoundError:
    pass

# Read Dockerfile OS-level package rules (optional)
dockerfile_rules = {}
try:
    with open('security-tooling/generated/renovate-dockerfile-regex.json') as f:
        dockerfile_rules = json.load(f)
except FileNotFoundError:
    pass

# Read base image upgrade rules (optional)
base_image_upgrade_rules = {}
try:
    with open('security-tooling/generated/renovate-base-image-upgrades.json') as f:
        base_image_upgrade_rules = json.load(f)
except FileNotFoundError:
    pass

# Read base image rules with reviewers
base_image_rules = {}
try:
    with open('security-tooling/generated/renovate-base-image-rules.json') as f:
        base_image_rules = json.load(f)
except FileNotFoundError:
    pass

# Read reviewer assignments
reviewer_rules = {}
try:
    with open('security-tooling/generated/renovate-reviewers.json') as f:
        reviewer_config = json.load(f)
        for rule in reviewer_config.get('packageRules', []):
            for pkg in rule.get('matchPackageNames', []):
                reviewer_rules[pkg] = rule
except FileNotFoundError:
    pass

# Merge Black Duck package rules with reviewer assignments
final_rules = []
for bd_rule in blackduck_rules.get('packageRules', []):
    pkg_names = bd_rule.get('matchPackageNames', [])
    for pkg_name in pkg_names:
        if pkg_name in reviewer_rules:
            rev_rule = reviewer_rules[pkg_name]
            bd_rule['reviewers'] = rev_rule.get('reviewers', [])
            bd_rule['addLabels'] = bd_rule.get('labels', []) + rev_rule.get('addLabels', [])
    final_rules.append(bd_rule)

# Add other rule types
final_rules.extend(container_rules.get('packageRules', []))
final_rules.extend(dockerfile_rules.get('packageRules', []))
final_rules.extend(base_image_upgrade_rules.get('packageRules', []))
final_rules.extend(base_image_rules.get('packageRules', []))

# Create merged config with base structure
merged = {
    "$schema": "https://docs.renovatebot.com/renovate-schema.json",
    "extends": ["config:base"],
    "description": "Renovate configuration with Black Duck vulnerability remediation ONLY",
    "dependencyDashboard": True,
    "dependencyDashboardAutoclose": False,
    "enabledManagers": ["gomod", "npm", "docker-compose", "dockerfile", "regex"],
    "prHourlyLimit": 0,
    "prConcurrentLimit": 0,
    "branchConcurrentLimit": 0,
    "separateMinorPatch": True,
    "separateMultipleMajor": True,
    "separateMajorMinor": True,
    "rangeStrategy": "update-lockfile",
    "semanticCommits": "enabled",
    "commitMessagePrefix": "fix(deps):",
    "commitMessageTopic": "{{depName}}",
    "commitMessageExtra": "to {{#if isMajor}}v{{{newMajor}}}{{else}}{{#if isSingleVersion}}v{{{newVersion}}}{{else}}{{{newValue}}}{{/if}}{{/if}}",
    "labels": ["dependencies", "security"],
    "assignees": [],
    "reviewers": [],
    "vulnerabilityAlerts": {"enabled": False},
    "packageRules": []
}

# Add regex managers
if dockerfile_rules.get('regexManagers'):
    merged['regexManagers'] = dockerfile_rules.get('regexManagers', [])
if base_image_upgrade_rules.get('regexManagers'):
    if 'regexManagers' not in merged:
        merged['regexManagers'] = []
    merged['regexManagers'].extend(base_image_upgrade_rules.get('regexManagers', []))

# Add global disable rule FIRST
merged['packageRules'].append({
    "description": "Disable all updates by default - only Black Duck findings will be enabled",
    "matchPackagePatterns": ["*"],
    "matchManagers": ["gomod", "npm"],
    "enabled": False
})

# Add merged package rules AFTER disable rule
merged['packageRules'].extend(final_rules)

# Write merged config
with open('renovate-merged.json', 'w') as f:
    json.dump(merged, f, indent=2)

print(f"   ✓ renovate-merged.json")
print(f"\n📊 Summary:")
print(f"   Package rules: {len(merged['packageRules'])}")
print(f"   Regex managers: {len(merged.get('regexManagers', []))}")
PYEND
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Success! Generated: renovate-merged.json"
echo ""
echo "You can now:"
echo "  • View the config: cat renovate-merged.json | jq"
echo "  • Check reviewers: grep -A5 '\"reviewers\"' renovate-merged.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
