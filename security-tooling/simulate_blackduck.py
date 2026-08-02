#!/usr/bin/env python3
"""
Simulate Black Duck vulnerability input for Renovate POC.

This script:
1. Reads vulnerability data from blackduck_report.json
2. Prints the package and fixed version
3. Generates Renovate package rules dynamically

Future enhancements:
- Pull vulnerabilities from Black Duck API
- Trigger a Renovate run via webhook
"""

import json
import sys


def process_full_report():
    """Process the detailed blackduck_report.json format"""
    print("=" * 60)
    print("FULL BLACK DUCK SCAN REPORT (security-tooling/blackduck_report.json)")
    print("=" * 60)

    with open("security-tooling/blackduck_report.json") as f:
        report = json.load(f)

    print(f"Project: {report['project_name']}")
    print(f"Scan Date: {report['scan_date']}")
    print(f"Status: {report['scan_status']}")
    print(f"Total Vulnerabilities: {report['total_vulnerabilities']}")
    print(f"\nSummary:")
    print(f"  Critical: {report['summary']['critical']}")
    print(f"  High: {report['summary']['high']}")
    print(f"  Medium: {report['summary']['medium']}")
    print(f"  Low: {report['summary']['low']}")

    print(f"\nDetailed Vulnerabilities:")
    print("-" * 60)

    for vuln in report['vulnerabilities']:
        print(f"\n{vuln['vulnerability_id']} - {vuln['severity']}")
        print(f"  Component: {vuln['component']} v{vuln['version']}")
        print(f"  CVSS Score: {vuln['cvss_score']}")
        print(f"  Description: {vuln['description']}")

        fixed_versions = vuln.get('fixed_versions', [])
        if fixed_versions:
            print(f"  Fixed in: {', '.join(fixed_versions)}")
            print(f"  Recommended: {vuln.get('recommended_version', 'N/A')}")
        else:
            print(f"  Fixed in: NO FIX AVAILABLE")

        print(f"  Remediation: {vuln['remediation']}")

    # Generate Renovate package rules for all vulnerabilities
    package_rules = []
    components_processed = set()

    for vuln in report['vulnerabilities']:
        component = vuln['component']
        recommended_version = vuln.get('recommended_version')

        if component not in components_processed and recommended_version:
            package_rules.append({
                "matchPackageNames": [component],
                "allowedVersions": f">={recommended_version}"
            })
            components_processed.add(component)

    print("\n" + "=" * 60)
    print("Generated Renovate package rules:")
    print("=" * 60)
    print(json.dumps({"packageRules": package_rules}, indent=2))
    print()


def main():
    process_full_report()


if __name__ == "__main__":
    main()
