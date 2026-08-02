#!/usr/bin/env python3
"""
Automatically patch Dockerfiles to add RUN upgrade commands for base image vulnerabilities.

This script:
1. Detects vulnerabilities in base image OS packages
2. Modifies Dockerfiles to add RUN apk/apt/yum upgrade commands
3. Generates Renovate regex managers to keep these upgrades updated

Usage:
    python3 security-tooling/patch_base_image_dockerfiles.py [--dry-run]
"""

import json
import sys
import os
import re
import argparse
from collections import defaultdict


def load_categorization():
    """Load vulnerability categorization from detect_base_image_vulns.py"""
    with open("security-tooling/generated/vuln-categorization.json", 'r') as f:
        return json.load(f)


def read_dockerfile(filepath):
    """Read Dockerfile content"""
    with open(filepath, 'r') as f:
        return f.read()


def write_dockerfile(filepath, content):
    """Write Dockerfile content"""
    with open(filepath, 'w') as f:
        f.write(content)


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


def group_vulns_by_dockerfile(base_image_vulns):
    """Group vulnerabilities by Dockerfile path"""
    grouped = defaultdict(list)
    for vuln in base_image_vulns:
        file_path = vuln.get('file_path', '')
        if file_path:
            grouped[file_path].append(vuln)
    return grouped


def generate_upgrade_command(vulns, ecosystem):
    """Generate RUN upgrade command for a set of vulnerabilities"""
    package_manager = get_package_manager(ecosystem)
    
    # Group by package name and get recommended versions
    packages = []
    for vuln in vulns:
        component = vuln.get('component', '')
        recommended_version = vuln.get('recommended_version', '')
        if component and recommended_version:
            packages.append(f"{component}={recommended_version}")
    
    if not packages:
        return None
    
    # Generate command based on package manager
    if package_manager == 'apk':
        # apk upgrade --no-cache package1=version package2=version
        cmd = f"RUN apk upgrade --no-cache {' '.join(packages)}"
    elif package_manager == 'apt':
        # apt-get update && apt-get install --only-upgrade package1=version package2=version
        cmd = f"RUN apt-get update && apt-get install -y --only-upgrade {' '.join(packages)}"
    elif package_manager == 'yum':
        # yum update -y package1-version package2-version
        yum_packages = [p.replace('=', '-') for p in packages]
        cmd = f"RUN yum update -y {' '.join(yum_packages)}"
    else:
        return None
    
    return cmd


def find_insertion_point(dockerfile_content):
    """
    Find the best place to insert the upgrade command.
    
    Strategy:
    1. After the last FROM statement (for multi-stage builds, patch final stage)
    2. Before the first COPY/ADD command (to avoid cache invalidation)
    """
    lines = dockerfile_content.split('\n')
    
    # Find last FROM statement
    last_from_idx = -1
    first_copy_idx = len(lines)
    
    for idx, line in enumerate(lines):
        if line.strip().startswith('FROM '):
            last_from_idx = idx
        if line.strip().startswith(('COPY ', 'ADD ')) and first_copy_idx == len(lines):
            first_copy_idx = idx
    
    # Insert after FROM, before first COPY
    if last_from_idx >= 0:
        # Look for next non-comment, non-empty line after FROM
        for idx in range(last_from_idx + 1, len(lines)):
            line = lines[idx].strip()
            if line and not line.startswith('#'):
                return idx
        return last_from_idx + 1
    
    return 0


def patch_dockerfile(dockerfile_path, vulns, dry_run=False):
    """
    Add RUN upgrade command to Dockerfile for base image vulnerabilities.
    
    Returns: (success, upgrade_command, insertion_line)
    """
    # Read current Dockerfile
    content = read_dockerfile(dockerfile_path)
    
    # Determine ecosystem (assume all vulns in same file have same ecosystem)
    ecosystem = vulns[0].get('ecosystem', 'alpine')
    
    # Generate upgrade command
    upgrade_cmd = generate_upgrade_command(vulns, ecosystem)
    if not upgrade_cmd:
        return False, None, None
    
    # Check if upgrade command already exists
    if upgrade_cmd in content:
        print(f"  ⚠️  Upgrade command already exists in {dockerfile_path}")
        return True, upgrade_cmd, None
    
    # Find insertion point
    insertion_idx = find_insertion_point(content)
    
    # Insert the upgrade command
    lines = content.split('\n')
    
    # Add comment explaining why
    comment = f"# Security: Upgrade base image OS packages to fix vulnerabilities"
    cves = ', '.join([v.get('vulnerability_id', '') for v in vulns[:3]])
    if len(vulns) > 3:
        cves += f" (+{len(vulns) - 3} more)"
    detail_comment = f"# Fixes: {cves}"
    
    lines.insert(insertion_idx, detail_comment)
    lines.insert(insertion_idx, comment)
    lines.insert(insertion_idx + 2, upgrade_cmd)
    lines.insert(insertion_idx + 3, "")  # blank line for readability
    
    new_content = '\n'.join(lines)
    
    if not dry_run:
        write_dockerfile(dockerfile_path, new_content)
        print(f"  ✅ Patched {dockerfile_path}")
    else:
        print(f"  🔍 [DRY RUN] Would patch {dockerfile_path}")
    
    print(f"     Command: {upgrade_cmd}")
    
    return True, upgrade_cmd, insertion_idx


def main():
    parser = argparse.ArgumentParser(description='Patch Dockerfiles for base image vulnerabilities')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = parser.parse_args()
    
    print("=" * 70)
    print("DOCKERFILE BASE IMAGE PATCHER")
    print("=" * 70)
    print()
    
    # Load categorization
    try:
        categorized = load_categorization()
    except FileNotFoundError:
        print("❌ Error: Run detect_base_image_vulns.py first!")
        return 1
    
    base_image_vulns = categorized.get('base_image_vulns', [])
    
    if not base_image_vulns:
        print("✅ No base image vulnerabilities to patch!")
        return 0
    
    print(f"Found {len(base_image_vulns)} base image vulnerability(ies)")
    print()
    
    # Group by Dockerfile
    grouped = group_vulns_by_dockerfile(base_image_vulns)
    
    print(f"Affects {len(grouped)} Dockerfile(s):")
    print()

    # Patch each Dockerfile
    patched_files = []
    for dockerfile_path, vulns in grouped.items():
        print(f"📄 {dockerfile_path}:")
        print(f"   Vulnerabilities: {len(vulns)}")

        success, upgrade_cmd, _ = patch_dockerfile(dockerfile_path, vulns, args.dry_run)
        if success:
            patched_files.append({
                'filepath': dockerfile_path,
                'command': upgrade_cmd,
                'vulns': vulns
            })
        print()

    # Save patch information
    if not args.dry_run:
        os.makedirs("security-tooling/generated", exist_ok=True)
        with open("security-tooling/generated/dockerfile-patches.json", 'w') as f:
            json.dump(patched_files, f, indent=2)
        print(f"✅ Saved patch info to: security-tooling/generated/dockerfile-patches.json")

    print()
    print("=" * 70)
    print(f"✅ Summary: Patched {len(patched_files)} Dockerfile(s)")
    if args.dry_run:
        print("   (DRY RUN - no files were modified)")
    print("=" * 70)
    print()

    if not args.dry_run:
        print("Next steps:")
        print("1. Review the Dockerfile changes")
        print("2. Run: python3 security-tooling/generate_upgrade_regex.py")
        print("3. Test the Docker builds locally")
        print("4. Commit and push changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
