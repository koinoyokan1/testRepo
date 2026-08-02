#!/usr/bin/env python3
"""
Detect OS-level vulnerabilities in base image layers (not in RUN commands).

This script identifies vulnerabilities that exist in the base image itself,
which cannot be fixed by updating RUN apk/apt/yum commands.

Usage:
    python3 security-tooling/detect_base_image_vulns.py
"""

import json
import sys
import os
import re


def load_blackduck_report(filepath="security-tooling/mockBlackDuck/blackduck_report.json"):
    """Load Black Duck vulnerability report"""
    with open(filepath, 'r') as f:
        return json.load(f)


def read_dockerfile(filepath):
    """Read Dockerfile content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None


def extract_base_image(dockerfile_content):
    """Extract the base image from Dockerfile FROM statement"""
    if not dockerfile_content:
        return None
    
    # Match: FROM image:tag or FROM image:tag AS builder
    match = re.search(r'^FROM\s+([^\s]+)', dockerfile_content, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def extract_installed_packages(dockerfile_content, package_manager='apk'):
    """Extract packages explicitly installed in RUN commands"""
    if not dockerfile_content:
        return set()
    
    installed_packages = set()
    
    # Pattern to match package installations
    if package_manager == 'apk':
        # Match: RUN apk add package=version or RUN apk --no-cache add package=version
        pattern = r'RUN\s+apk\s+(?:--no-cache\s+)?(?:add|install)\s+([^\n]+)'
    elif package_manager == 'apt':
        pattern = r'RUN\s+apt-get\s+install\s+([^\n]+)'
    elif package_manager == 'yum':
        pattern = r'RUN\s+yum\s+install\s+([^\n]+)'
    else:
        return installed_packages
    
    matches = re.findall(pattern, dockerfile_content)
    for match in matches:
        # Extract package names (strip versions and flags)
        packages = re.findall(r'([a-z0-9-]+)(?:=|$)', match)
        installed_packages.update(packages)
    
    return installed_packages


def is_base_image_vuln(vuln, dockerfile_path):
    """
    Determine if vulnerability is in base image layer (not in RUN command).
    
    Returns True if:
    1. Ecosystem is OS-level (alpine, debian, etc.)
    2. Package is NOT explicitly installed in a RUN command
    3. Dockerfile exists at the specified path
    """
    ecosystem = vuln.get('ecosystem', '')
    os_ecosystems = ['alpine', 'debian', 'rhel', 'ubuntu', 'centos', 'fedora']
    
    if ecosystem not in os_ecosystems:
        return False
    
    # Read the Dockerfile
    dockerfile_content = read_dockerfile(dockerfile_path)
    if not dockerfile_content:
        return False
    
    # Get package manager
    package_manager = vuln.get('package_manager', 'apk')
    if package_manager not in ['apk', 'apt', 'yum']:
        package_manager = 'apk'  # default
    
    # Get packages explicitly installed
    installed_packages = extract_installed_packages(dockerfile_content, package_manager)
    
    # Check if this package is explicitly installed
    component = vuln.get('component', '')
    
    # If package is NOT in installed packages, it's from base image
    return component not in installed_packages


def categorize_vulnerabilities(blackduck_report):
    """
    Categorize vulnerabilities into:
    1. base_image_vulns: OS packages in base image layers (need RUN upgrade)
    2. explicit_install_vulns: OS packages in RUN commands (already handled)
    3. container_vulns: Base image version issues (need FROM update)
    """
    categorized = {
        'base_image_vulns': [],
        'explicit_install_vulns': [],
        'container_vulns': []
    }
    
    for vuln in blackduck_report.get('vulnerabilities', []):
        ecosystem = vuln.get('ecosystem', '')
        file_path = vuln.get('file_path', '')
        
        # Container ecosystem - base image version issue
        if ecosystem == 'container':
            categorized['container_vulns'].append(vuln)
            continue
        
        # OS-level package
        os_ecosystems = ['alpine', 'debian', 'rhel', 'ubuntu', 'centos', 'fedora']
        if ecosystem in os_ecosystems:
            # Check if it's in base image or explicit install
            if is_base_image_vuln(vuln, file_path):
                categorized['base_image_vulns'].append(vuln)
            else:
                categorized['explicit_install_vulns'].append(vuln)
    
    return categorized


def main():
    print("=" * 70)
    print("BASE IMAGE VULNERABILITY DETECTOR")
    print("=" * 70)
    print()
    
    # Load Black Duck report
    blackduck_report = load_blackduck_report()
    
    # Categorize vulnerabilities
    categorized = categorize_vulnerabilities(blackduck_report)
    
    print(f"📊 Vulnerability Categories:")
    print(f"  • Base Image OS Packages: {len(categorized['base_image_vulns'])}")
    print(f"  • Explicit RUN Install: {len(categorized['explicit_install_vulns'])}")
    print(f"  • Container Base Images: {len(categorized['container_vulns'])}")
    print()
    
    if categorized['base_image_vulns']:
        print("🔍 Base Image OS Package Vulnerabilities (need RUN upgrade):")
        print()
        for vuln in categorized['base_image_vulns']:
            print(f"  • {vuln['vulnerability_id']} - {vuln['component']} ({vuln.get('severity', 'UNKNOWN')})")
            print(f"    File: {vuln.get('file_path', 'unknown')}")
            print(f"    Current: {vuln.get('version', 'unknown')}")
            print(f"    Fixed: {vuln.get('recommended_version', 'unknown')}")
            print()
    
    # Save categorization
    os.makedirs("security-tooling/generated", exist_ok=True)
    output_file = "security-tooling/generated/vuln-categorization.json"
    with open(output_file, 'w') as f:
        json.dump(categorized, f, indent=2)
    
    print(f"✅ Saved categorization to: {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
