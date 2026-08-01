#!/usr/bin/env python3
"""
Simulate Black Duck vulnerability input for Renovate POC.

This script:
1. Reads vulnerability data from blackduck.json and blackduck_report.json
2. Prints the package and fixed version
3. Can be extended to generate Renovate package rules dynamically

Future enhancements:
- Pull vulnerabilities from Black Duck API
- Generate Renovate package rules dynamically
- Trigger a Renovate run via webhook
"""

import json
import sys


def process_single_vuln():
    """Process the simple blackduck.json format"""
    print("=" * 60)
    print("SIMPLE VULNERABILITY FORMAT (blackduck.json)")
    print("=" * 60)

    with open("blackduck.json") as f:
        vuln = json.load(f)

    print(f"Package: {vuln['package']}")
    print(f"Current version: {vuln['current']}")
    print(f"Fixed version: {vuln['fixed']}")
    print(f"Path: {vuln['path']}")
    print(f"CVE: {vuln.get('cve', 'N/A')}")
    print(f"Severity: {vuln.get('severity', 'N/A')}")
    print(f"CVSS Score: {vuln.get('cvss_score', 'N/A')}")
    print(f"Description: {vuln.get('description', 'N/A')}")

    # Generate Renovate package rule
    package_rule = {
        "matchPackageNames": [vuln["package"]],
        "allowedVersions": f">={vuln['fixed']}"
    }

    print("\nGenerated Renovate package rule:")
    print(json.dumps(package_rule, indent=2))
    print()


def process_full_report():
    """Process the detailed blackduck_report.json format"""
    print("=" * 60)
    print("FULL BLACK DUCK SCAN REPORT (blackduck_report.json)")
    print("=" * 60)

    with open("blackduck_report.json") as f:
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
        print(f"  Fixed in: {', '.join(vuln['fixed_versions'])}")
        print(f"  Recommended: {vuln['recommended_version']}")
        print(f"  Remediation: {vuln['remediation']}")

    # Generate Renovate package rules for all vulnerabilities
    package_rules = []
    components_processed = set()

    for vuln in report['vulnerabilities']:
        if vuln['component'] not in components_processed:
            package_rules.append({
                "matchPackageNames": [vuln["component"]],
                "allowedVersions": f">={vuln['recommended_version']}"
            })
            components_processed.add(vuln['component'])

    print("\n" + "=" * 60)
    print("Generated Renovate package rules:")
    print("=" * 60)
    print(json.dumps({"packageRules": package_rules}, indent=2))
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        process_full_report()
    elif len(sys.argv) > 1 and sys.argv[1] == "--simple":
        process_single_vuln()
    else:
        # Process both by default
        process_single_vuln()
        print()
        process_full_report()


if __name__ == "__main__":
    main()
