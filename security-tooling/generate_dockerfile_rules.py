#!/usr/bin/env python3
"""
Generate Renovate package rules for OS-level packages in Dockerfiles.

This script reads Black Duck JSON reports and generates Renovate configuration
for packages installed via RUN commands in Dockerfiles (e.g., apk, apt, yum).

Usage:
    python3 security-tooling/generate_dockerfile_rules.py
"""

import json
import sys
import os
import re


def is_fixable(vuln):
    """Check if a vulnerability has a fix available"""
    recommended_version = vuln.get('recommended_version')
    fixed_versions = vuln.get('fixed_versions', [])
    
    if recommended_version and recommended_version not in [None, '', 'unknown']:
        return True
    if fixed_versions and len(fixed_versions) > 0:
        return True
    
    return False


def is_os_level_vuln(vuln):
    """Check if this is an OS-level package vulnerability"""
    ecosystem = vuln.get('ecosystem', '')
    # OS-level ecosystems
    os_ecosystems = ['alpine', 'debian', 'rhel', 'ubuntu', 'centos', 'fedora']
    return ecosystem in os_ecosystems


def get_package_manager(ecosystem):
    """Map ecosystem to package manager"""
    package_managers = {
        'alpine': 'apk',
        'debian': 'apt',
        'ubuntu': 'apt',
        'rhel': 'yum',
        'centos': 'yum',
        'fedora': 'dnf'
    }
    return package_managers.get(ecosystem, 'apk')


def generate_dockerfile_rule(vuln):
    """Generate a Renovate regex manager rule for a Dockerfile package"""
    component = vuln.get('component', 'unknown')
    current_version = vuln.get('version', 'unknown')
    recommended_version = vuln.get('recommended_version', 'unknown')
    cve = vuln.get('vulnerability_id', 'UNKNOWN')
    severity = vuln.get('severity', 'UNKNOWN')
    description = vuln.get('description', '')
    cvss_score = vuln.get('cvss_score', 'N/A')
    ecosystem = vuln.get('ecosystem', 'alpine')
    file_path = vuln.get('file_path', 'Dockerfile')
    package_manager = vuln.get('package_manager', get_package_manager(ecosystem))
    
    # Extract just the filename (not full path) for matchFileNames
    # e.g., "services/api-gateway/Dockerfile" -> "Dockerfile"
    # But we'll use the full path pattern for more specificity
    dockerfile_pattern = file_path.replace('/', '\\/')
    
    # Create regex pattern to match the package installation line
    # Example for apk: openssl=3.0.7-r0
    # Example for apt: openssl=3.0.7-1
    
    # The regex needs to capture:
    # - depName: package name (e.g., "openssl")
    # - currentValue: current version (e.g., "3.0.7-r0")
    
    # Pattern matches: package_name=version (with optional whitespace)
    regex_pattern = f'"({component})=([^\\s]+)"'
    
    rule = {
        "description": f"Black Duck - {cve} ({severity}) - {ecosystem} package in Dockerfile",
        "fileMatch": [f"^{dockerfile_pattern}$"],
        "matchStrings": [
            f"RUN\\s+{package_manager}\\s+(?:add|install)\\s+.*?{component}=(?<currentValue>[^\\s]+)"
        ],
        "depNameTemplate": component,
        "datasourceTemplate": "repology-repology",
        "versioningTemplate": "loose",
        "packageNameTemplate": f"{ecosystem}:{component}",
        "extractVersionTemplate": "^(?<version>.+)$",
        "enabled": True
    }
    
    # Generate a packageRule for this specific package
    package_rule = {
        "description": f"Black Duck - {cve} ({severity}) - {component} in {file_path}",
        "matchDatasources": ["repology-repology"],
        "matchPackageNames": [f"{ecosystem}:{component}"],
        "matchFileNames": [file_path],
        "allowedVersions": f">={recommended_version}",
        "enabled": True,
        "prTitle": f"OS package upgrade (explicit): update {component} to {recommended_version} in {file_path} to fix {cve} ({severity})",
        "prBodyNotes": [
            f"### 🔒 Security Update - OS-Level Package ({ecosystem.upper()})",
            "",
            f"**Vulnerability**: {cve}",
            f"**Severity**: {severity} (CVSS {cvss_score})",
            f"**Package Manager**: {package_manager}",
            f"**Package**: {component}",
            f"**Current Version**: {current_version}",
            f"**Fixed Version**: {recommended_version} (minimum safe version)",
            f"**Dockerfile**: {file_path}",
            "",
            f"**Description**: {description}",
            "",
            f"**Remediation**: Update {component} to version {recommended_version} in the Dockerfile RUN command.",
            "",
            "This PR was created based on Black Duck security scan findings."
        ],
        "labels": [
            "security",
            f"{severity.lower()}-priority" if severity else "priority",
            "blackduck",
            "dockerfile",
            ecosystem,
            cve.lower()
        ]
    }
    
    return {"regexManager": rule, "packageRule": package_rule}


def main():
    print("=" * 70)
    print("DOCKERFILE OS-LEVEL PACKAGE RULE GENERATOR")
    print("=" * 70)
    print()
    
    # Load Black Duck report
    report_file = "security-tooling/blackduck_report.json"
    try:
        with open(report_file, 'r') as f:
            report = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {report_file} not found")
        sys.exit(1)

    vulnerabilities = report.get('vulnerabilities', [])

    # Filter for OS-level package vulnerabilities that are fixable
    os_vulns = [v for v in vulnerabilities if is_os_level_vuln(v) and is_fixable(v)]

    if not os_vulns:
        print("✅ No fixable OS-level package vulnerabilities found!")
        # Create empty output files
        os.makedirs("security-tooling/generated", exist_ok=True)
        with open("security-tooling/generated/renovate-dockerfile-regex.json", 'w') as f:
            json.dump({"regexManagers": [], "packageRules": []}, f, indent=2)
        return 0

    print(f"📦 Found {len(os_vulns)} OS-level package vulnerability(ies)\n")

    # Generate rules
    regex_managers = []
    package_rules = []

    for idx, vuln in enumerate(os_vulns, 1):
        component = vuln.get('component', 'unknown')
        cve = vuln.get('vulnerability_id', 'UNKNOWN')
        ecosystem = vuln.get('ecosystem', 'alpine')
        file_path = vuln.get('file_path', 'Dockerfile')

        print(f"{idx}. {cve} - {component} ({ecosystem}) in {file_path}")

        rules = generate_dockerfile_rule(vuln)
        regex_managers.append(rules['regexManager'])
        package_rules.append(rules['packageRule'])

    # Create output configuration
    output = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated Dockerfile OS-level package rules from Black Duck",
        "regexManagers": regex_managers,
        "packageRules": package_rules
    }

    # Write to file
    os.makedirs("security-tooling/generated", exist_ok=True)
    output_file = "security-tooling/generated/renovate-dockerfile-regex.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("=" * 70)
    print(f"✅ Generated Dockerfile rule configuration: {output_file}")
    print(f"✅ Total regex managers created: {len(regex_managers)}")
    print(f"✅ Total package rules created: {len(package_rules)}")
    print("=" * 70)
    print()

    # Print summary
    print("📋 Regex Managers Summary:")
    for idx, rule in enumerate(regex_managers, 1):
        print(f"  {idx}. {rule['description']}")
        print(f"     File: {rule['fileMatch']}")
        print(f"     Package: {rule['depNameTemplate']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

