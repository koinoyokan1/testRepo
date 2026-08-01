#!/usr/bin/env python3
"""
Generate Renovate package rules from Black Duck vulnerability findings.

This script reads Black Duck JSON reports and generates Renovate configuration
that creates separate PRs for each vulnerability fix.
"""

import json
import sys


def generate_package_rule_from_vuln(vuln, index):
    """Generate a Renovate package rule for a single vulnerability"""
    
    # Determine the package name based on the format
    if 'component' in vuln:
        package_name = vuln['component']
        current_version = vuln.get('version', 'unknown')
        fixed_version = vuln.get('recommended_version', vuln.get('fixed_versions', ['unknown'])[0])
        cve = vuln.get('vulnerability_id', 'UNKNOWN')
        severity = vuln.get('severity', 'UNKNOWN')
        description = vuln.get('description', '')
        cvss_score = vuln.get('cvss_score', 'N/A')
    else:
        package_name = vuln.get('package', 'unknown')
        current_version = vuln.get('current', 'unknown')
        fixed_version = vuln.get('fixed', 'unknown')
        cve = vuln.get('cve', 'UNKNOWN')
        severity = vuln.get('severity', 'UNKNOWN')
        description = vuln.get('description', '')
        cvss_score = vuln.get('cvss_score', 'N/A')
    
    # Parse the fixed version to create a constraint that stays within the same minor version
    # e.g., if fixed_version is "1.9.1", constraint is ">=1.9.1 <1.10.0"
    version_parts = fixed_version.split('.')
    if len(version_parts) >= 2:
        major = version_parts[0]
        minor = version_parts[1]
        next_minor = str(int(minor) + 1)
        version_constraint = f">={fixed_version} <{major}.{next_minor}.0"
    else:
        # Fallback if version format is unexpected
        version_constraint = f">={fixed_version}"

    rule = {
        "description": f"Black Duck - {cve} ({severity})",
        "matchDatasources": ["go"],
        "matchPackageNames": [package_name],
        "allowedVersions": version_constraint,
        "groupName": None,  # Don't group - create separate PR
        "separateMinorPatch": False,
        "commitMessageTopic": package_name,
        "prTitle": f"fix(security): update {package_name.split('/')[-1]} to v{fixed_version} to fix {cve} ({severity})",
        "prBodyNotes": [
            "### 🔒 Security Update - Black Duck Finding",
            "",
            f"**Vulnerability**: {cve}",
            f"**Severity**: {severity} (CVSS {cvss_score})",
            f"**Current Version**: {current_version}",
            f"**Fixed Version**: {fixed_version} (minimum safe version)",
            f"**Version Constraint**: {version_constraint}",
            "",
            f"**Description**: {description}",
            "",
            f"**Remediation**: Update {package_name} to version {fixed_version}. Constrained to same minor version to minimize breaking changes.",
            "",
            "This PR was created based on Black Duck security scan findings."
        ],
        "labels": [
            "security",
            f"{severity.lower()}-priority" if severity else "priority",
            "blackduck",
            cve.lower()
        ]
    }
    
    return rule


def process_report_format(filename="blackduck_report.json"):
    """Process full report format"""
    try:
        with open(filename) as f:
            report = json.load(f)
        
        rules = []
        for idx, vuln in enumerate(report.get('vulnerabilities', [])):
            rules.append(generate_package_rule_from_vuln(vuln, idx))
        
        return rules
    except FileNotFoundError:
        return []


def main():
    print("Generating Renovate package rules from Black Duck findings...")

    # Process report format
    all_rules = process_report_format()

    if all_rules:
        print(f"✓ Processed {len(all_rules)} vulnerabilities from blackduck_report.json")
    else:
        print("✗ No Black Duck report found or no vulnerabilities detected!")
        sys.exit(1)
    
    # Generate Renovate config fragment
    renovate_config = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated from Black Duck vulnerability findings",
        "packageRules": all_rules
    }
    
    # Write to file
    output_file = "renovate-blackduck-generated.json"
    with open(output_file, 'w') as f:
        json.dump(renovate_config, f, indent=2)
    
    print(f"\n✓ Generated Renovate configuration: {output_file}")
    print(f"✓ Total package rules created: {len(all_rules)}")
    print("\nPackage rules summary:")
    for idx, rule in enumerate(all_rules, 1):
        print(f"  {idx}. {rule['description']}")
        print(f"     Package: {rule['matchPackageNames'][0]}")
        print(f"     Min Version: {rule['allowedVersions']}")
    
    # Also print JSON output for GitHub Actions
    print("\n" + "="*60)
    print("RENOVATE PACKAGE RULES (JSON):")
    print("="*60)
    print(json.dumps(renovate_config, indent=2))


if __name__ == "__main__":
    main()
