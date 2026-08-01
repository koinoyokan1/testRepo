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
    
    rule = {
        "description": f"Black Duck - {cve} ({severity})",
        "matchDatasources": ["go"],
        "matchPackageNames": [package_name],
        "allowedVersions": f">={fixed_version}",
        "groupName": None,  # Don't group - create separate PR
        "separateMinorPatch": False,
        "commitMessageTopic": package_name,
        "prTitle": f"fix(security): update {package_name.split('/')[-1]} to v{fixed_version}+ to fix {cve} ({severity})",
        "prBodyNotes": [
            "### 🔒 Security Update - Black Duck Finding",
            "",
            f"**Vulnerability**: {cve}",
            f"**Severity**: {severity} (CVSS {cvss_score})",
            f"**Current Version**: {current_version}",
            f"**Fixed Version**: {fixed_version}+",
            "",
            f"**Description**: {description}",
            "",
            f"**Remediation**: Update {package_name} to version {fixed_version} or later.",
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


def process_simple_format(filename="blackduck.json"):
    """Process simple blackduck.json format"""
    try:
        with open(filename) as f:
            vuln = json.load(f)
        return [generate_package_rule_from_vuln(vuln, 0)]
    except FileNotFoundError:
        return []


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
    
    # Collect all rules
    all_rules = []
    
    # Process both formats
    simple_rules = process_simple_format()
    report_rules = process_report_format()
    
    # Use report rules if available, otherwise use simple
    if report_rules:
        all_rules = report_rules
        print(f"✓ Processed {len(report_rules)} vulnerabilities from blackduck_report.json")
    elif simple_rules:
        all_rules = simple_rules
        print(f"✓ Processed {len(simple_rules)} vulnerability from blackduck.json")
    else:
        print("✗ No Black Duck reports found!")
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
