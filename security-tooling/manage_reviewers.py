#!/usr/bin/env python3
"""
Unified reviewer management for both Go and npm dependencies.
Determines which teams should review based on Black Duck findings and generates Renovate configuration.

Usage:
    # Analyze a single Go package
    python3 manage_reviewers.py analyze --go github.com/gin-gonic/gin

    # Analyze a single npm package
    python3 manage_reviewers.py analyze --npm axios

    # Process entire Black Duck report
    python3 manage_reviewers.py process-report [security-tooling/mockBlackDuck/blackduck_report.json]

    # Generate Renovate reviewer configuration
    python3 manage_reviewers.py generate-renovate [security-tooling/mockBlackDuck/blackduck_report.json]
"""

import json
import os
import sys
import argparse
from typing import Dict
from npm_reviewer_utils import analyze_npm_package_reviewers
from go_reviewer_utils import analyze_go_package_reviewers


# ============================================================================
# Email to GitHub Username Conversion
# ============================================================================

def email_to_github_username(email: str) -> str:
    """Convert email to GitHub username by extracting the part before @"""
    if '@' in email:
        return email.split('@')[0]
    return email


# ============================================================================
# Component Ownership
# ============================================================================

def load_component_ownership(filepath: str = "security-tooling/component_ownership.json") -> dict:
    """Load component ownership configuration"""
    with open(filepath, 'r') as f:
        return json.load(f)


# ============================================================================
# Unified Analysis Functions
# ============================================================================


def find_reviewers_for_vulnerability(vuln: dict) -> dict:
    """
    Find reviewers for a single vulnerability from Black Duck report.

    Args:
        vuln: Vulnerability dict with ecosystem, component, etc.

    Returns:
        Analysis dict with reviewers and affected components
    """
    ecosystem = vuln.get('ecosystem', 'go')
    component = vuln.get('component', '')
    ownership_config = load_component_ownership()

    if ecosystem == 'npm':
        return analyze_npm_package_reviewers(component, ownership_config)
    elif ecosystem == 'go':
        return analyze_go_package_reviewers(component, ownership_config)
    else:
        print(f"Warning: Unknown ecosystem '{ecosystem}' for {component}")
        return {}


def process_blackduck_report(report_file: str = "security-tooling/mockBlackDuck/blackduck_report.json") -> dict:
    """
    Process entire Black Duck report and find reviewers for all vulnerabilities.

    Returns:
        Dict mapping package names to reviewer analysis
    """
    with open(report_file, 'r') as f:
        report = json.load(f)

    vulnerabilities = report.get('vulnerabilities', [])
    results = {}

    print(f"\n{'='*70}")
    print(f"PROCESSING BLACK DUCK REPORT")
    print(f"{'='*70}\n")
    print(f"Total vulnerabilities: {len(vulnerabilities)}\n")

    for idx, vuln in enumerate(vulnerabilities, 1):
        component = vuln.get('component', 'unknown')
        ecosystem = vuln.get('ecosystem', 'go')
        cve = vuln.get('vulnerability_id', 'UNKNOWN')
        severity = vuln.get('severity', 'UNKNOWN')

        print(f"\n[{idx}/{len(vulnerabilities)}] Processing: {component} ({ecosystem}) - {cve} ({severity})")
        print("-" * 70)

        # Skip if we already analyzed this package
        if component in results:
            print(f"  ℹ️  Already analyzed {component}, skipping...")
            continue

        analysis = find_reviewers_for_vulnerability(vuln)

        if analysis:
            reviewers = analysis.get('reviewers', [])
            components = len(analysis.get('components', {}))
            print(f"  ✅ Found {len(reviewers)} reviewers across {components} components")
            results[component] = {
                'ecosystem': ecosystem,
                'cve': cve,
                'severity': severity,
                'analysis': analysis
            }
        else:
            print(f"  ⚠️  No usage found for {component}")

    return results


def generate_summary(results: dict) -> dict:
    """Generate a summary of all reviewers needed"""
    all_reviewers = set()
    components_by_package = {}

    for package, data in results.items():
        analysis = data['analysis']
        reviewers = analysis.get('reviewers', [])
        components = list(analysis.get('components', {}).keys())

        all_reviewers.update(reviewers)
        components_by_package[package] = {
            'ecosystem': data['ecosystem'],
            'cve': data['cve'],
            'severity': data['severity'],
            'components': components,
            'reviewers': reviewers
        }

    return {
        'total_packages': len(results),
        'total_reviewers': len(all_reviewers),
        'all_reviewers': sorted(list(all_reviewers)),
        'packages': components_by_package
    }




def print_summary(summary: dict):
    """Print a consolidated summary"""
    print(f"\n\n{'='*70}")
    print("CONSOLIDATED SUMMARY")
    print(f"{'='*70}\n")

    print(f"📊 Overall Statistics:")
    print(f"  • Vulnerable packages: {summary['total_packages']}")
    print(f"  • Total unique reviewers: {summary['total_reviewers']}")

    print(f"\n📦 Packages Requiring Updates:\n")
    for package, data in summary['packages'].items():
        print(f"  {data['ecosystem'].upper()}: {package}")
        print(f"    └─ {data['cve']} ({data['severity']})")
        print(f"    └─ {len(data['components'])} component(s) affected")
        print(f"    └─ {len(data['reviewers'])} reviewer(s) needed\n")

    print(f"👥 All Required Reviewers ({summary['total_reviewers']}):")
    for reviewer in summary['all_reviewers']:
        print(f"  ✓ {reviewer}")

    print(f"\n{'='*70}\n")


def generate_renovate_reviewers_config(
    blackduck_report_file: str = "security-tooling/mockBlackDuck/blackduck_report.json",
    ownership_file: str = "security-tooling/component_ownership.json",
    output_file: str = "security-tooling/generated/renovate-reviewers.json"
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
    packages_affected = {}
    for vuln in blackduck_report.get('vulnerabilities', []):
        component = vuln['component']
        ecosystem = vuln.get('ecosystem', 'go')
        packages_affected[component] = ecosystem

    # Generate reviewer rules for each package
    package_rules = []

    for package, ecosystem in packages_affected.items():
        print(f"\nAnalyzing reviewers for: {package} ({ecosystem})")

        # Get reviewers for this package
        if ecosystem == 'npm':
            result = analyze_npm_package_reviewers(package, ownership_config)
        else:  # go
            result = analyze_go_package_reviewers(package, ownership_config)

        if result and result.get('reviewers'):
            reviewers = result['reviewers']
            components = result.get('components_affected', [])

            print(f"  ✓ Found {len(reviewers)} reviewers")
            print(f"  ✓ Affects {len(components)} components")

            # Convert email addresses to GitHub usernames
            github_reviewers = [email_to_github_username(r) for r in reviewers]

            rule = {
                "description": f"Auto-assign reviewers for {package} (affects {len(components)} components)",
                "matchDatasources": [ecosystem],
                "matchPackageNames": [package],
                "reviewers": github_reviewers[:5],  # Limit to 5 reviewers max
                "addLabels": [
                    f"component:{comp['name'].lower().replace(' ', '-')}"
                    for comp in components[:3]  # Add first 3 component labels
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
                # Convert email addresses to GitHub usernames
                github_defaults = [email_to_github_username(r) for r in all_defaults]

                rule = {
                    "description": f"Default reviewers for {package}",
                    "matchDatasources": [ecosystem],
                    "matchPackageNames": [package],
                    "reviewers": github_defaults[:5]
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
    parser = argparse.ArgumentParser(
        description="Unified reviewer management for Go and npm dependencies"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Analyze single package
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single package')
    analyze_group = analyze_parser.add_mutually_exclusive_group(required=True)
    analyze_group.add_argument('--go', help='Go package name (e.g., github.com/gin-gonic/gin)')
    analyze_group.add_argument('--npm', help='npm package name (e.g., axios)')

    # Process Black Duck report
    process_parser = subparsers.add_parser('process-report', help='Process entire Black Duck report')
    process_parser.add_argument('report_file', nargs='?', default='security-tooling/mockBlackDuck/blackduck_report.json',
                               help='Black Duck report file (default: security-tooling/mockBlackDuck/blackduck_report.json)')

    # Generate Renovate config
    renovate_parser = subparsers.add_parser('generate-renovate',
                                            help='Generate Renovate reviewer configuration')
    renovate_parser.add_argument('report_file', nargs='?', default='security-tooling/mockBlackDuck/blackduck_report.json',
                                help='Black Duck report file (default: security-tooling/mockBlackDuck/blackduck_report.json)')
    renovate_parser.add_argument('--output', default='security-tooling/generated/renovate-reviewers.json',
                                help='Output file (default: security-tooling/generated/renovate-reviewers.json)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'analyze':
        ownership_config = load_component_ownership()
        if args.go:
            result = analyze_go_package_reviewers(args.go, ownership_config)
            print(json.dumps(result, indent=2))
        elif args.npm:
            result = analyze_npm_package_reviewers(args.npm, ownership_config)
            print(json.dumps(result, indent=2))

    elif args.command == 'process-report':
        results = process_blackduck_report(args.report_file)
        summary = generate_summary(results)
        print_summary(summary)

        # Save to file
        output_file = "security-tooling/generated/reviewer_analysis.json"
        with open(output_file, 'w') as f:
            json.dump({
                'summary': summary,
                'detailed_results': {
                    pkg: data['analysis']
                    for pkg, data in results.items()
                }
            }, f, indent=2)

        print(f"📁 Detailed analysis saved to: {output_file}")

    elif args.command == 'generate-renovate':
        config = generate_renovate_reviewers_config(
            args.report_file,
            output_file=args.output
        )
        print("\n" + "="*70)
        print("GENERATED RENOVATE CONFIG")
        print("="*70)
        print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
