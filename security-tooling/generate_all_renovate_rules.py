#!/usr/bin/env python3
"""
Generate all Renovate rules and merge them into a final renovate-merged.json.

This script orchestrates the entire Renovate configuration generation process:
1. Generates package rules for Go/npm
2. Generates container image rules for custom images
3. Generates Dockerfile rules for OS packages
4. Generates base image rules with reviewers
5. Generates reviewer assignments
6. Merges everything into renovate-merged.json

Usage:
    python3 security-tooling/generate_all_renovate_rules.py
"""

import json
import os
import sys
import subprocess


def run_script(script_path, description):
    """Run a Python script and check for errors"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Script: {script_path}")
    print('='*70)
    
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True
    )
    
    # Print output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"❌ Error running {script_path}")
        return False
    
    print(f"✅ Successfully completed: {description}")
    return True


def merge_renovate_configs():
    """Merge all generated Renovate configurations into renovate-merged.json"""
    print(f"\n{'='*70}")
    print("MERGING RENOVATE CONFIGURATIONS")
    print('='*70)
    
    # Start with base renovate.json
    try:
        with open('renovate.json', 'r') as f:
            merged = json.load(f)
        print("✓ Loaded base renovate.json")
    except FileNotFoundError:
        print("❌ Error: renovate.json not found")
        return False
    
    # Read generated package rules (Go/npm)
    try:
        with open('security-tooling/generated/renovate-package-rules.json', 'r') as f:
            package_rules = json.load(f)
        print(f"✓ Loaded package rules: {len(package_rules.get('packageRules', []))} rules")
    except FileNotFoundError:
        print("⚠ No package rules found")
        package_rules = {'packageRules': []}
    
    # Read generated container image rules
    try:
        with open('security-tooling/generated/renovate-container-image-rules.json', 'r') as f:
            container_rules = json.load(f)
        print(f"✓ Loaded container image rules: {len(container_rules.get('packageRules', []))} rules")
    except FileNotFoundError:
        print("⚠ No container image rules found")
        container_rules = {'packageRules': []}
    
    # Read generated Dockerfile rules
    try:
        with open('security-tooling/generated/renovate-dockerfile-rules.json', 'r') as f:
            dockerfile_rules = json.load(f)
        print(f"✓ Loaded Dockerfile rules: {len(dockerfile_rules.get('regexManagers', []))} regex managers, "
              f"{len(dockerfile_rules.get('packageRules', []))} package rules")
    except FileNotFoundError:
        print("⚠ No Dockerfile rules found")
        dockerfile_rules = {'regexManagers': [], 'packageRules': []}
    
    # Read generated base image rules
    try:
        with open('security-tooling/generated/renovate-base-image-rules.json', 'r') as f:
            base_image_rules = json.load(f)
        print(f"✓ Loaded base image rules: {len(base_image_rules.get('packageRules', []))} rules")
    except FileNotFoundError:
        print("⚠ No base image rules found")
        base_image_rules = {'packageRules': []}
    
    # Read generated reviewer assignments
    reviewer_rules = {}
    try:
        with open('security-tooling/generated/renovate-reviewers.json', 'r') as f:
            reviewer_config = json.load(f)
            # Create a map of package name to reviewer rule
            for rule in reviewer_config.get('packageRules', []):
                for pkg in rule.get('matchPackageNames', []):
                    reviewer_rules[pkg] = rule
        print(f"✓ Loaded reviewer assignments: {len(reviewer_rules)} packages")
    except FileNotFoundError:
        print("⚠ No reviewer config found")
    
    # Merge package rules with reviewer assignments
    final_rules = []
    for bd_rule in package_rules.get('packageRules', []):
        pkg_names = bd_rule.get('matchPackageNames', [])
        
        # Merge with reviewer rule if exists
        for pkg_name in pkg_names:
            if pkg_name in reviewer_rules:
                rev_rule = reviewer_rules[pkg_name]
                bd_rule['reviewers'] = rev_rule.get('reviewers', [])
                bd_rule['addLabels'] = bd_rule.get('labels', []) + rev_rule.get('addLabels', [])
        
        final_rules.append(bd_rule)
    
    # Add other rule types
    final_rules.extend(container_rules.get('packageRules', []))
    final_rules.extend(dockerfile_rules.get('packageRules', []))
    final_rules.extend(base_image_rules.get('packageRules', []))
    
    # Merge Dockerfile regex managers
    if dockerfile_rules.get('regexManagers'):
        if 'regexManagers' not in merged:
            merged['regexManagers'] = []
        merged['regexManagers'].extend(dockerfile_rules.get('regexManagers', []))
    
    # Add global disable rule FIRST
    merged['packageRules'].append({
        "description": "Disable all updates by default - only Black Duck findings will be enabled",
        "matchPackagePatterns": ["*"],
        "matchManagers": ["gomod", "npm"],
        "enabled": False
    })
    
    # Add merged package rules AFTER the disable rule
    merged['packageRules'].extend(final_rules)
    
    # Write merged config
    with open('renovate-merged.json', 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"\n✅ Merged configuration written to: renovate-merged.json")
    print(f"✓ Total package rules: {len(merged['packageRules'])}")
    print(f"  - Package rules (Go/npm): {len(package_rules.get('packageRules', []))}")
    print(f"  - Container image rules: {len(container_rules.get('packageRules', []))}")
    print(f"  - Dockerfile rules: {len(dockerfile_rules.get('packageRules', []))}")
    print(f"  - Base image rules: {len(base_image_rules.get('packageRules', []))}")
    print(f"✓ Total regex managers: {len(merged.get('regexManagers', []))}")
    
    return True


def main():
    print("="*70)
    print("RENOVATE CONFIGURATION GENERATOR")
    print("="*70)
    print("\nThis script will generate all Renovate rules and merge them.")
    print()
    
    # Ensure generated directory exists
    os.makedirs("security-tooling/generated", exist_ok=True)
    
    # Step 1: Generate package rules (Go/npm)
    if not run_script("security-tooling/generate_package_rules.py", 
                     "Package Rules (Go/npm)"):
        return 1
    
    # Step 2: Generate container image rules
    if not run_script("security-tooling/generate_container_image_rules.py",
                     "Container Image Rules"):
        return 1
    
    # Step 3: Generate Dockerfile rules
    if not run_script("security-tooling/generate_dockerfile_rules.py",
                     "Dockerfile OS Package Rules"):
        return 1
    
    # Step 4: Generate base image rules
    if not run_script("security-tooling/generate_base_image_rules.py",
                     "Base Image Rules with Reviewers"):
        return 1
    
    # Step 5: Generate reviewer assignments (Go/npm only)
    print(f"\n{'='*70}")
    print("Running: Reviewer Assignments (Go/npm only)")
    print("Script: security-tooling/manage_reviewers.py generate-renovate")
    print('='*70)

    result = subprocess.run(
        [sys.executable, "security-tooling/manage_reviewers.py", "generate-renovate"],
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("⚠ Continuing without reviewer assignments")
    else:
        print("✅ Successfully completed: Reviewer Assignments")
    
    # Step 6: Merge all configurations
    if not merge_renovate_configs():
        return 1
    
    print(f"\n{'='*70}")
    print("✅ ALL RENOVATE RULES GENERATED SUCCESSFULLY!")
    print('='*70)
    print("\nGenerated files:")
    print("  - security-tooling/generated/renovate-package-rules.json")
    print("  - security-tooling/generated/renovate-container-image-rules.json")
    print("  - security-tooling/generated/renovate-dockerfile-rules.json")
    print("  - security-tooling/generated/renovate-base-image-rules.json")
    print("  - security-tooling/generated/renovate-go-npm-reviewers.json (Go/npm only)")
    print("  - renovate-merged.json ⭐")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
