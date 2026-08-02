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
from pathlib import Path


def email_to_github_username(email):
    """Convert email to GitHub username by extracting the part before @"""
    if '@' in email:
        return email.split('@')[0]
    return email


def load_component_ownership(filepath="security-tooling/component_ownership.json"):
    """Load component ownership configuration"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Warning: {filepath} not found, reviewers will not be assigned")
        return {"components": []}


def find_component_for_dockerfile(dockerfile_path, ownership_config):
    """
    Map a Dockerfile path to its component using directories from component_ownership.json.

    Args:
        dockerfile_path: Path to Dockerfile (e.g., "services/api-gateway/Dockerfile")
        ownership_config: Component ownership configuration dict

    Returns:
        Component dict with name and owners, or None if no match
    """
    # Normalize the path - get the directory containing the Dockerfile
    path = Path(dockerfile_path)
    dockerfile_dir = str(path.parent)

    # Try to match against component directories
    for component in ownership_config.get('components', []):
        for comp_dir in component.get('directories', []):
            # Check if the Dockerfile directory matches the component directory
            # e.g., "services/api-gateway" matches "services/api-gateway/Dockerfile"
            if dockerfile_dir == comp_dir or dockerfile_dir.startswith(comp_dir + '/'):
                return component

    return None


def get_reviewers_for_dockerfile(dockerfile_path, ownership_config):
    """
    Get reviewers for a Dockerfile based on component ownership.

    Returns:
        Dict with reviewers list and component labels
    """
    component = find_component_for_dockerfile(dockerfile_path, ownership_config)

    if not component:
        return {"reviewers": [], "labels": []}

    # Collect primary and secondary owners (convert emails to GitHub usernames)
    owners = component.get('owners', {})
    reviewers = list(set(
        owners.get('primary', []) +
        owners.get('secondary', [])
    ))

    # Convert email addresses to GitHub usernames
    reviewers = [email_to_github_username(r) for r in reviewers]

    # Create component label
    component_label = f"component:{component['name']}"

    return {
        "reviewers": sorted(reviewers),
        "labels": [component_label]
    }


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


def generate_dockerfile_rule(vuln, ownership_config=None):
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

    # Get reviewers for this Dockerfile
    reviewer_info = {"reviewers": [], "labels": []}
    if ownership_config:
        reviewer_info = get_reviewers_for_dockerfile(file_path, ownership_config)
    
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
    
    # Build flexible regex pattern that handles apk flags like --no-cache, --update, etc.
    # Pattern: RUN apk [flags] add/install [flags] ... package=version
    if package_manager == 'apk':
        match_pattern = f"RUN\\s+apk\\s+[^\\n]*?(?:add|install)[^\\n]*?{component}=(?<currentValue>[^\\s]+)"
    elif package_manager == 'apt':
        match_pattern = f"RUN\\s+apt-get\\s+[^\\n]*?install[^\\n]*?{component}=(?<currentValue>[^\\s]+)"
    elif package_manager == 'yum':
        match_pattern = f"RUN\\s+yum\\s+[^\\n]*?install[^\\n]*?{component}-(?<currentValue>[^\\s]+)"
    else:
        # Fallback to generic pattern
        match_pattern = f"RUN\\s+{package_manager}\\s+[^\\n]*?(?:add|install)[^\\n]*?{component}[=-](?<currentValue>[^\\s]+)"

    rule = {
        "description": f"Black Duck - {cve} ({severity}) - {ecosystem} package in Dockerfile",
        "fileMatch": [f"^{dockerfile_pattern}$"],
        "matchStrings": [match_pattern],
        "depNameTemplate": component,
        "datasourceTemplate": "repology-repology",
        "versioningTemplate": "loose",
        "packageNameTemplate": f"{ecosystem}:{component}",
        "extractVersionTemplate": "^(?<version>.+)$",
        "enabled": True
    }
    
    # Generate a packageRule for this specific package
    # Create unique branch name
    safe_component = component.replace('/', '-').replace('_', '-')
    safe_cve = cve.lower().replace('_', '-')
    dockerfile_short = file_path.split('/')[-2] if '/' in file_path else 'root'
    branch_name = f"blackduck/dockerfile/{dockerfile_short}/{safe_component}/{safe_cve}"

    package_rule = {
        "description": f"Black Duck - {cve} ({severity}) - {component} in {file_path}",
        "matchDatasources": ["repology-repology"],
        "matchPackageNames": [f"{ecosystem}:{component}"],
        "matchFileNames": [file_path],
        "allowedVersions": f">={recommended_version}",
        "enabled": True,
        "branchName": branch_name,  # Unique branch to prevent collision
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
        ] + reviewer_info.get("labels", []),
        "reviewers": reviewer_info.get("reviewers", [])
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

    # Load component ownership configuration
    ownership_config = load_component_ownership()

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

        rules = generate_dockerfile_rule(vuln, ownership_config)
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

