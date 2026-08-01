#!/usr/bin/env python3
"""
Scan container images from image_versions.json and find vulnerabilities from Black Duck report.
Generates Renovate rules for container image updates.

Usage:
    python3 security-tooling/scan_container_images.py
"""

import json
import sys
from collections import defaultdict


def load_image_versions(filepath="image_versions.json"):
    """Load image versions configuration"""
    with open(filepath, 'r') as f:
        return json.load(f)


def load_blackduck_report(filepath="security-tooling/blackduck_report.json"):
    """Load Black Duck vulnerability report"""
    with open(filepath, 'r') as f:
        return json.load(f)


def find_image_vulnerabilities(blackduck_report):
    """Extract container image vulnerabilities from Black Duck report"""
    image_vulns = defaultdict(list)

    for vuln in blackduck_report.get('vulnerabilities', []):
        ecosystem = vuln.get('ecosystem', '')
        if ecosystem == 'container':
            component = vuln['component']
            image_vulns[component].append(vuln)

    return image_vulns


def get_image_owner(image_config, image_name, image_type):
    """Get owner for an image"""
    if image_type == 'prebuilt':
        return image_config['prebuilt_images'].get(image_name, {}).get('owner', 'platform-team@company.com')
    else:
        return image_config['custom_images'].get(image_name, {}).get('owner', 'devops-team@company.com')


def generate_renovate_rule_for_image(image_name, image_data, vulns, image_type):
    """Generate a Renovate package rule for a container image"""

    current_version = image_data.get('tag', '')
    recommended_version = vulns[0]['recommended_version'] if vulns else None

    if not recommended_version:
        return None

    # Build CVE list
    cve_list = [v['vulnerability_id'] for v in vulns]
    severity_list = [v['severity'] for v in vulns]
    highest_severity = 'HIGH' if 'HIGH' in severity_list else ('MEDIUM' if 'MEDIUM' in severity_list else 'LOW')

    # Create rule description
    if len(cve_list) == 1:
        description = f"Black Duck - {image_name} {cve_list[0]} ({highest_severity})"
    else:
        description = f"Black Duck - {image_name} multiple CVEs ({highest_severity})"

    # Build PR title
    if len(cve_list) == 1:
        pr_title = f"fix(security): update {image_name} to {recommended_version} to fix {cve_list[0]}"
    else:
        pr_title = f"fix(security): update {image_name} to {recommended_version} to fix {len(cve_list)} CVEs"

    # Build PR body notes
    pr_body = [
        f"### 🔒 Security Update - Container Image ({image_type.upper()})",
        "",
        f"**Image**: {image_data.get('full_image', image_name)}",
        f"**Current Version**: {current_version}",
        f"**Recommended Version**: {recommended_version}",
        ""
    ]

    if image_type == 'custom':
        pr_body.extend([
            f"**Base Image**: {image_data.get('base_image', 'N/A')}",
            f"**Dockerfile**: {image_data.get('dockerfile', 'N/A')}",
            ""
        ])

    pr_body.append("**Vulnerabilities Fixed**:")
    pr_body.append("")

    for vuln in vulns:
        pr_body.extend([
            f"#### {vuln['vulnerability_id']} ({vuln['severity']})",
            f"- **CVSS Score**: {vuln['cvss_score']}",
            f"- **Description**: {vuln['description']}",
            ""
        ])

    pr_body.extend([
        f"**Remediation**: {vulns[0]['remediation']}",
        "",
        "---",
        "",
        "**File to Update**: `image_versions.json`"
    ])

    if image_type == 'custom':
        pr_body.append("**Action Required**: Rebuild container image with updated base image")

    pr_body.extend([
        "",
        "This PR was created based on Black Duck container image scan findings."
    ])

    rule = {
        "description": description,
        "matchFileNames": ["image_versions.json"],
        "matchPackageNames": [image_name],
        "enabled": True,
        "prTitle": pr_title,
        "prBodyNotes": pr_body,
        "labels": [
            "security",
            f"{highest_severity.lower()}-priority",
            "blackduck",
            "container-image",
            image_type
        ] + [cve.lower() for cve in cve_list],
        "reviewers": [image_data.get('owner', 'devops-team@company.com')]
    }

    return rule


def main():
    print("=" * 70)
    print("CONTAINER IMAGE VULNERABILITY SCANNER")
    print("=" * 70)
    print()

    # Load configurations
    image_config = load_image_versions()
    blackduck_report = load_blackduck_report()

    # Find image vulnerabilities
    image_vulns = find_image_vulnerabilities(blackduck_report)

    if not image_vulns:
        print("✅ No container image vulnerabilities found!")
        return 0

    print(f"Found vulnerabilities in {len(image_vulns)} container image(s)")
    print()

    # Generate Renovate rules
    renovate_rules = []

    # Process prebuilt images
    for image_name, vulns in image_vulns.items():
        # Check if it's a prebuilt image
        if image_name in image_config.get('prebuilt_images', {}):
            image_data = image_config['prebuilt_images'][image_name]
            print(f"📦 {image_name} (PREBUILT)")
            print(f"   Current: {image_data['tag']}")
            print(f"   Owner: {image_data['owner']}")
            print(f"   CVEs: {len(vulns)}")
            for v in vulns:
                print(f"     - {v['vulnerability_id']} ({v['severity']})")

            rule = generate_renovate_rule_for_image(image_name, image_data, vulns, 'prebuilt')
            if rule:
                renovate_rules.append(rule)
            print()

    # Process custom images
    for image_name, vulns in image_vulns.items():
        # Extract just the image name from full path
        short_name = image_name.split('/')[-1] if '/' in image_name else image_name

        if short_name in image_config.get('custom_images', {}):
            image_data = image_config['custom_images'][short_name]
            print(f"🔨 {short_name} (CUSTOM)")
            print(f"   Full Image: {image_data['full_image']}")
            print(f"   Current: {image_data['tag']}")
            print(f"   Base Image: {image_data['base_image']}")
            print(f"   Owner: {image_data['owner']}")
            print(f"   CVEs: {len(vulns)}")
            for v in vulns:
                print(f"     - {v['vulnerability_id']} ({v['severity']})")

            rule = generate_renovate_rule_for_image(short_name, image_data, vulns, 'custom')
            if rule:
                renovate_rules.append(rule)
            print()

    # Generate output
    output = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated from Black Duck container image scan findings",
        "packageRules": renovate_rules
    }

    # Save to file
    output_file = "security-tooling/generated/renovate-container-images.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 70)
    print(f"✅ Generated {len(renovate_rules)} Renovate rule(s)")
    print(f"📁 Saved to: {output_file}")
    print("=" * 70)
    print()

    # Print summary
    print("📊 Summary:")
    print(f"  • Total vulnerable images: {len(image_vulns)}")
    print(f"  • Total CVEs: {sum(len(v) for v in image_vulns.values())}")
    print(f"  • Renovate rules generated: {len(renovate_rules)}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
