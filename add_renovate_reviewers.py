#!/usr/bin/env python3
"""
Integrate with Renovate to add reviewers based on component ownership.
This script updates renovate configuration with dynamic reviewers.
"""

import json
import sys
from find_reviewers import (
    load_component_ownership,
    get_reviewers_for_dependency
)


def update_renovate_config_with_reviewers(package_name: str, reviewers: list) -> dict:
    """
    Update Renovate configuration to include reviewers for a specific package.
    Returns the package rule configuration.
    """
    return {
        "matchPackageNames": [package_name],
        "reviewers": reviewers
    }


def generate_renovate_reviewers_config(
    blackduck_report_file: str = "blackduck_report.json",
    ownership_file: str = "component_ownership.json",
    output_file: str = "renovate-reviewers.json"
):
    """
    Generate Renovate reviewer configuration based on Black Duck findings
    and component ownership.
    """
    # Load Black Duck report
    with open(blackduck_report_file, 'r') as f:
        blackduck_report = json.load(f)
    
    # Load component ownership
    ownership_config = load_component_ownership(ownership_file)
    
    # Track unique packages from vulnerabilities
    packages_affected = set()
    for vuln in blackduck_report.get('vulnerabilities', []):
        packages_affected.add(vuln['component'])
    
    # Generate reviewer rules for each package
    package_rules = []
    
    for package in packages_affected:
        print(f"\nAnalyzing reviewers for: {package}")
        
        # Get reviewers for this package
        result = get_reviewers_for_dependency(
            package,
            ownership_config,
            include_secondary=True
        )
        
        if result['reviewers']:
            print(f"  ✓ Found {len(result['reviewers'])} reviewers")
            print(f"  ✓ Affects {result['total_components']} components")
            
            rule = {
                "description": f"Auto-assign reviewers for {package} (affects {result['total_components']} components)",
                "matchDatasources": ["go"],
                "matchPackageNames": [package],
                "reviewers": result['reviewers'][:5],  # Limit to 5 reviewers max
                "addLabels": [
                    f"component:{comp['name'].lower().replace(' ', '-')}"
                    for comp in result['components_affected'][:3]  # Add first 3 component labels
                ]
            }
            package_rules.append(rule)
        else:
            print(f"  ⚠ No reviewers found, using defaults")
            default_reviewers = ownership_config.get('default_reviewers', {})
            all_defaults = (
                default_reviewers.get('primary', []) +
                default_reviewers.get('secondary', [])
            )
            
            if all_defaults:
                rule = {
                    "description": f"Default reviewers for {package}",
                    "matchDatasources": ["go"],
                    "matchPackageNames": [package],
                    "reviewers": all_defaults[:5]
                }
                package_rules.append(rule)
    
    # Create final config
    config = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated reviewer assignments based on component ownership",
        "packageRules": package_rules
    }
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Generated {output_file} with {len(package_rules)} reviewer rules")
    return config


def main():
    """CLI interface"""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python3 add_renovate_reviewers.py")
        print("\nGenerates Renovate reviewer configuration based on:")
        print("  - blackduck_report.json (vulnerability findings)")
        print("  - component_ownership.json (component ownership mapping)")
        print("\nOutputs:")
        print("  - renovate-reviewers.json (Renovate package rules with reviewers)")
        sys.exit(0)
    
    config = generate_renovate_reviewers_config()
    
    # Pretty print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
