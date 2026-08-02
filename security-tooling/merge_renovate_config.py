#!/usr/bin/env python3
"""
Merge all generated Renovate configurations into renovate-merged.json.

This script reads all generated JSON rule files and merges them with the base
renovate.json configuration to create the final renovate-merged.json that
Renovate will use.

Inputs:
  - renovate.json (base configuration)
  - security-tooling/generated/renovate-package-rules.json
  - security-tooling/generated/renovate-container-image-rules.json
  - security-tooling/generated/renovate-dockerfile-rules.json
  - security-tooling/generated/renovate-base-image-rules.json
  - security-tooling/generated/renovate-reviewers.json (optional)

Output:
  - renovate-merged.json (final merged configuration)

Usage:
    python3 security-tooling/merge_renovate_config.py
"""

import json
import sys


def load_json_file(filepath, description, required=True):
    """Load a JSON file with error handling"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded {description}: {filepath}")
        return data
    except FileNotFoundError:
        if required:
            print(f"❌ Error: Required file not found: {filepath}")
            sys.exit(1)
        else:
            print(f"⚠ Optional file not found: {filepath}, skipping")
            return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {filepath}: {e}")
        sys.exit(1)


def main():
    print("="*70)
    print("MERGING RENOVATE CONFIGURATIONS")
    print("="*70)
    print()
    
    # Load base renovate.json
    merged = load_json_file('renovate.json', 'base configuration', required=True)
    
    # Load all generated rule files
    package_rules = load_json_file(
        'security-tooling/generated/renovate-package-rules.json',
        'package rules (Go/npm)',
        required=False
    )
    
    container_rules = load_json_file(
        'security-tooling/generated/renovate-container-image-rules.json',
        'container image rules',
        required=False
    )
    
    dockerfile_rules = load_json_file(
        'security-tooling/generated/renovate-dockerfile-rules.json',
        'Dockerfile rules',
        required=False
    )
    
    base_image_rules = load_json_file(
        'security-tooling/generated/renovate-base-image-rules.json',
        'base image rules',
        required=False
    )
    
    reviewer_config = load_json_file(
        'security-tooling/generated/renovate-go-npm-reviewers.json',
        'reviewer assignments (Go/npm only)',
        required=False
    )
    
    print()
    print("-"*70)
    print("MERGING RULES")
    print("-"*70)
    
    # Create reviewer lookup map
    reviewer_rules = {}
    for rule in reviewer_config.get('packageRules', []):
        for pkg in rule.get('matchPackageNames', []):
            reviewer_rules[pkg] = rule
    
    if reviewer_rules:
        print(f"✓ Created reviewer lookup map: {len(reviewer_rules)} packages")
    
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
                
                # Add component owners to PR body notes
                if 'prBodyNotes' in bd_rule and rev_rule.get('reviewers'):
                    owners_section = [
                        "",
                        "---",
                        "",
                        "### 👥 Component Owners",
                        ""
                    ]
                    for reviewer in rev_rule.get('reviewers', []):
                        owners_section.append(f"- @{reviewer.replace('@company.com', '')}")
                    
                    # Add component labels info
                    if rev_rule.get('addLabels'):
                        components = [
                            lbl.replace('component:', '') 
                            for lbl in rev_rule.get('addLabels', []) 
                            if lbl.startswith('component:')
                        ]
                        if components:
                            owners_section.append("")
                            owners_section.append(f"**Affected Components**: {', '.join(components)}")
                    
                    # Insert before the "This PR was created..." line
                    bd_rule['prBodyNotes'] = (
                        bd_rule['prBodyNotes'][:-1] + 
                        owners_section + 
                        [bd_rule['prBodyNotes'][-1]]
                    )
        
        final_rules.append(bd_rule)
    
    print(f"✓ Merged package rules with reviewers: {len(final_rules)} rules")
    
    # Add other rule types
    container_count = len(container_rules.get('packageRules', []))
    dockerfile_count = len(dockerfile_rules.get('packageRules', []))
    base_image_count = len(base_image_rules.get('packageRules', []))
    
    final_rules.extend(container_rules.get('packageRules', []))
    final_rules.extend(dockerfile_rules.get('packageRules', []))
    final_rules.extend(base_image_rules.get('packageRules', []))
    
    print(f"✓ Added container image rules: {container_count} rules")
    print(f"✓ Added Dockerfile rules: {dockerfile_count} rules")
    print(f"✓ Added base image rules: {base_image_count} rules")
    
    # Merge Dockerfile regex managers
    regex_count = len(dockerfile_rules.get('regexManagers', []))
    if dockerfile_rules.get('regexManagers'):
        if 'regexManagers' not in merged:
            merged['regexManagers'] = []
        merged['regexManagers'].extend(dockerfile_rules.get('regexManagers', []))
        print(f"✓ Added Dockerfile regex managers: {regex_count} managers")
    
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
    
    print()
    print("="*70)
    print("✅ SUCCESSFULLY CREATED: renovate-merged.json")
    print("="*70)
    print(f"Total package rules: {len(merged['packageRules'])}")
    print(f"  - Package rules (Go/npm): {len(package_rules.get('packageRules', []))}")
    print(f"  - Container image rules: {container_count}")
    print(f"  - Dockerfile rules: {dockerfile_count}")
    print(f"  - Base image rules: {base_image_count}")
    print(f"  - Global disable rule: 1")
    print(f"Total regex managers: {len(merged.get('regexManagers', []))}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
