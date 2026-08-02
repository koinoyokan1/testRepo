#!/usr/bin/env python3
"""
Generate Renovate regex managers for base image upgrade commands.

This script creates regex managers that can automatically update the package
versions in the RUN upgrade commands added by patch_base_image_dockerfiles.py.

Usage:
    python3 security-tooling/generate_upgrade_regex.py
"""

import json
import sys
import os


def load_patches():
    """Load Dockerfile patch information"""
    with open("security-tooling/generated/dockerfile-patches.json", 'r') as f:
        return json.load(f)


def get_package_manager(ecosystem):
    """Map ecosystem to package manager"""
    mapping = {
        'alpine': 'apk',
        'debian': 'apt',
        'ubuntu': 'apt',
        'rhel': 'yum',
        'centos': 'yum',
        'fedora': 'dnf'
    }
    return mapping.get(ecosystem, 'apk')


def generate_regex_manager(patch_info):
    """
    Generate Renovate regex manager for a base image upgrade command.
    
    For apk: RUN apk upgrade --no-cache libssl3=3.0.8-r0 libcrypto3=3.0.8-r0
    We need to create a regex that matches each package=version pair.
    """
    filepath = patch_info['filepath']
    vulns = patch_info['vulns']
    
    if not vulns:
        return []
    
    # Get ecosystem and package manager
    ecosystem = vulns[0].get('ecosystem', 'alpine')
    package_manager = get_package_manager(ecosystem)
    
    # Create one regex manager per package
    regex_managers = []
    
    for vuln in vulns:
        component = vuln.get('component', '')
        cve = vuln.get('vulnerability_id', '')
        severity = vuln.get('severity', 'UNKNOWN')
        recommended_version = vuln.get('recommended_version', '')
        
        if not component or not recommended_version:
            continue
        
        # Create regex pattern for this package
        if package_manager == 'apk':
            # Match: RUN apk upgrade --no-cache ... component=version ...
            match_pattern = f"RUN\\s+apk\\s+upgrade\\s+--no-cache\\s+.*?{component}=(?<currentValue>[^\\s]+)"
        elif package_manager == 'apt':
            # Match: RUN apt-get install --only-upgrade ... component=version ...
            match_pattern = f"RUN\\s+apt-get\\s+install\\s+.*?--only-upgrade\\s+.*?{component}=(?<currentValue>[^\\s]+)"
        elif package_manager == 'yum':
            # Match: RUN yum update -y ... component-version ...
            match_pattern = f"RUN\\s+yum\\s+update\\s+-y\\s+.*?{component}-(?<currentValue>[^\\s]+)"
        else:
            continue
        
        # Escape forward slashes for regex
        escaped_filepath = filepath.replace('/', '\\/')

        regex_manager = {
            "description": f"Black Duck - {cve} ({severity}) - Base image {ecosystem} package",
            "fileMatch": [f"^{escaped_filepath}$"],
            "matchStrings": [match_pattern],
            "depNameTemplate": component,
            "datasourceTemplate": "repology-repology",
            "versioningTemplate": "loose",
            "packageNameTemplate": f"{ecosystem}:{component}",
            "extractVersionTemplate": "^(?<version>.+)$",
            "enabled": True
        }
        
        regex_managers.append(regex_manager)
    
    return regex_managers


def generate_package_rules(patch_info):
    """Generate Renovate package rules for base image upgrades"""
    filepath = patch_info['filepath']
    vulns = patch_info['vulns']
    
    if not vulns:
        return []
    
    ecosystem = vulns[0].get('ecosystem', 'alpine')
    package_rules = []
    
    for vuln in vulns:
        component = vuln.get('component', '')
        cve = vuln.get('vulnerability_id', '')
        severity = vuln.get('severity', 'UNKNOWN')
        cvss_score = vuln.get('cvss_score', 'N/A')
        current_version = vuln.get('version', '')
        recommended_version = vuln.get('recommended_version', '')
        description = vuln.get('description', '')
        
        if not component or not recommended_version:
            continue
        
        package_rule = {
            "description": f"Black Duck - {cve} ({severity}) - Base image {component}",
            "matchDatasources": ["repology-repology"],
            "matchPackageNames": [f"{ecosystem}:{component}"],
            "matchFileNames": [filepath],
            "allowedVersions": f">={recommended_version}",
            "enabled": True,
            "prTitle": f"OS package upgrade (base image): upgrade {component} to {recommended_version} in {filepath} to fix {cve}",
            "prBodyNotes": [
                f"### 🔒 Security Update - Base Image OS Package ({ecosystem.upper()})",
                "",
                f"**Vulnerability**: {cve}",
                f"**Severity**: {severity} (CVSS {cvss_score})",
                f"**Package**: {component} (from base image)",
                f"**Current Version**: {current_version}",
                f"**Fixed Version**: {recommended_version}",
                f"**Dockerfile**: {filepath}",
                "",
                f"**Description**: {description}",
                "",
                "**Note**: This package comes from the base image and is being upgraded",
                "via `RUN apk/apt/yum upgrade` to fix security vulnerabilities without",
                "requiring a full base image version change.",
                "",
                "This PR was created based on Black Duck security scan findings."
            ],
            "labels": [
                "security",
                f"{severity.lower()}-priority",
                "blackduck",
                "base-image-upgrade",
                ecosystem,
                cve.lower()
            ]
        }
        
        package_rules.append(package_rule)
    
    return package_rules


def main():
    print("=" * 70)
    print("RENOVATE REGEX GENERATOR FOR BASE IMAGE UPGRADES")
    print("=" * 70)
    print()
    
    # Load patch information
    try:
        patches = load_patches()
    except FileNotFoundError:
        print("❌ Error: Run patch_base_image_dockerfiles.py first!")
        return 1
    
    if not patches:
        print("✅ No patches found - nothing to generate!")
        return 0
    
    print(f"Found {len(patches)} patched Dockerfile(s)")
    print()
    
    # Generate regex managers and package rules
    all_regex_managers = []
    all_package_rules = []
    
    for patch in patches:
        filepath = patch['filepath']
        print(f"📄 {filepath}")
        
        regex_managers = generate_regex_manager(patch)
        package_rules = generate_package_rules(patch)
        
        print(f"   Generated {len(regex_managers)} regex manager(s)")
        print(f"   Generated {len(package_rules)} package rule(s)")
        print()
        
        all_regex_managers.extend(regex_managers)
        all_package_rules.extend(package_rules)
    
    # Create output configuration
    output = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated regex managers for base image OS package upgrades",
        "regexManagers": all_regex_managers,
        "packageRules": all_package_rules
    }

    # Save to file
    os.makedirs("security-tooling/generated", exist_ok=True)
    output_file = "security-tooling/generated/renovate-base-image-upgrades.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 70)
    print(f"✅ Generated regex manager configuration: {output_file}")
    print(f"✅ Total regex managers: {len(all_regex_managers)}")
    print(f"✅ Total package rules: {len(all_package_rules)}")
    print("=" * 70)
    print()

    print("📋 Summary:")
    for mgr in all_regex_managers:
        print(f"  • {mgr['description']}")
        print(f"    File: {mgr['fileMatch']}")
        print(f"    Package: {mgr['depNameTemplate']}")

    print()
    print("Next steps:")
    print("1. The generated config will be automatically merged by .github/workflows/renovate.yml")
    print("2. Renovate will create PRs when newer versions are available")
    print("3. Test Docker builds after merging any Renovate PRs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
