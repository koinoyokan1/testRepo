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
    python3 manage_reviewers.py process-report [blackduck_report.json]

    # Generate Renovate reviewer configuration
    python3 manage_reviewers.py generate-renovate [blackduck_report.json]
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import List, Dict
from npm_reviewer_utils import analyze_npm_package_reviewers


# ============================================================================
# Component Ownership
# ============================================================================

def load_component_ownership(filepath: str = "security-tooling/component_ownership.json") -> dict:
    """Load component ownership configuration"""
    with open(filepath, 'r') as f:
        return json.load(f)


# ============================================================================
# Go Dependency Analysis
# ============================================================================

def find_all_go_modules(root_dir: str = ".") -> List[str]:
    """
    Find all go.mod files in the repository (including nested modules).
    Returns list of directories containing go.mod files.
    """
    modules = []

    try:
        # Find all go.mod files
        result = subprocess.run(
            ["find", root_dir, "-name", "go.mod", "-type", "f"],
            capture_output=True,
            text=True,
            check=True
        )

        for go_mod_path in result.stdout.strip().split('\n'):
            if go_mod_path:
                # Get directory containing go.mod
                module_dir = os.path.dirname(go_mod_path)
                modules.append(module_dir if module_dir else ".")

    except subprocess.CalledProcessError:
        # Fallback to just current directory
        modules = ["."]

    return modules


def find_modules_importing_package(package_name: str) -> Dict[str, List[str]]:
    """
    Find all Go modules/packages that import the given package.
    Uses 'go list' for accurate dependency analysis.
    Scans all go.mod files in the repository (handles nested modules).

    Returns:
        Dict mapping module paths to list of files that import the package
    """
    result = defaultdict(list)

    # Find all Go modules in the repository
    all_modules = find_all_go_modules()
    print(f"Found {len(all_modules)} Go module(s): {all_modules}")

    # Scan each module separately
    for module_dir in all_modules:
        try:
            # Use 'go list' to find all packages in this module
            list_result = subprocess.run(
                ["go", "list", "-json", "./..."],
                capture_output=True,
                text=True,
                check=True,
                cwd=module_dir
            )

            # Parse JSON output - go list -json outputs newline-delimited JSON objects
            # We need to parse them as a stream
            packages = []
            json_buffer = ""
            brace_count = 0

            for char in list_result.stdout:
                json_buffer += char
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_buffer.strip():
                        # Complete JSON object
                        try:
                            pkg = json.loads(json_buffer.strip())
                            packages.append(pkg)
                        except json.JSONDecodeError as e:
                            print(f"Warning: Failed to parse JSON in {module_dir}: {e}")
                        json_buffer = ""

            # For each package, check if it imports our target package
            for pkg in packages:
                imports = pkg.get('Imports', [])
                go_files = pkg.get('GoFiles', [])
                pkg_dir = pkg.get('Dir', '')

                # Check direct imports
                if package_name in imports:
                    # This package directly imports our target
                    for go_file in go_files:
                        file_path = os.path.join(pkg_dir, go_file)
                        result[pkg.get('ImportPath', '')].append(file_path)

        except subprocess.CalledProcessError as e:
            print(f"Warning: 'go list' failed for module {module_dir}: {e}")
            # Continue to next module
            continue
        except FileNotFoundError:
            print("Error: 'go' command not found")
            print("Please install Go: https://go.dev/doc/install")
            raise

    return dict(result)


def find_component_for_file(filepath: str, ownership_config: dict) -> Dict:
    """
    Find the component that owns a file by recursively checking parent directories.
    """
    file_path = Path(filepath).resolve()
    current_path = file_path.parent

    while True:
        try:
            rel_path = current_path.relative_to(Path.cwd())
            rel_path_str = str(rel_path)
        except ValueError:
            break

        for component in ownership_config['components']:
            for comp_dir in component['directories']:
                if rel_path_str == comp_dir or rel_path_str.startswith(comp_dir + '/'):
                    return component

        if current_path == current_path.parent:
            break
        current_path = current_path.parent

    return {
        "name": "Default",
        "owners": ownership_config.get('default_reviewers', {"primary": [], "secondary": []})
    }


def get_reviewers_for_dependency(
    package_name: str,
    ownership_config: dict,
    include_secondary: bool = True
) -> Dict:
    """
    Main function: Get reviewers for a Go dependency update using go list.
    """
    # Step 1: Find all modules/files importing the package
    modules_files = find_modules_importing_package(package_name)

    if not modules_files:
        return {
            "package": package_name,
            "modules_affected": [],
            "files_affected": [],
            "total_files": 0,
            "components_affected": [],
            "total_components": 0,
            "reviewers": []
        }

    # Flatten to get all files
    all_files = []
    for module, files in modules_files.items():
        all_files.extend(files)

    # Step 2: Map files to components
    component_files = defaultdict(list)
    components_found = {}

    for filepath in all_files:
        component = find_component_for_file(filepath, ownership_config)
        comp_name = component['name']

        component_files[comp_name].append(filepath)
        components_found[comp_name] = component

    # Step 3: Collect all unique reviewers
    reviewers = set()
    for comp_name, component in components_found.items():
        owners = component['owners']
        reviewers.update(owners.get('primary', []))
        if include_secondary:
            reviewers.update(owners.get('secondary', []))

    # Step 4: Build result
    components_affected = [
        {
            "name": comp_name,
            "files": sorted(files),
            "owners": components_found[comp_name]['owners']
        }
        for comp_name, files in sorted(component_files.items())
    ]

    return {
        "package": package_name,
        "modules_affected": list(modules_files.keys()),
        "files_affected": sorted(all_files),
        "total_files": len(all_files),
        "components_affected": components_affected,
        "total_components": len(components_affected),
        "reviewers": sorted(list(reviewers))
    }


# ============================================================================
# Unified Analysis Functions
# ============================================================================


def analyze_go_reviewers(package_name: str) -> dict:
    """Wrapper for Go reviewer analysis to match npm interface"""
    ownership_config = load_component_ownership()
    result = get_reviewers_for_dependency(package_name, ownership_config, include_secondary=True)

    if not result:
        return {}

    # Convert components_affected list to dict keyed by name
    components_dict = {}
    for comp in result.get('components_affected', []):
        components_dict[comp['name']] = comp

    return {
        'package': package_name,
        'packages_affected': result.get('modules_affected', []),
        'components': components_dict,
        'reviewers': result.get('reviewers', [])
    }


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
        return analyze_go_reviewers(component)
    else:
        print(f"Warning: Unknown ecosystem '{ecosystem}' for {component}")
        return {}


def process_blackduck_report(report_file: str = "blackduck_report.json") -> dict:
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
    blackduck_report_file: str = "security-tooling/blackduck_report.json",
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
            result = get_reviewers_for_dependency(
                package,
                ownership_config,
                include_secondary=True
            )

        if result and result.get('reviewers'):
            reviewers = result['reviewers']
            components = result.get('components_affected', [])

            print(f"  ✓ Found {len(reviewers)} reviewers")
            print(f"  ✓ Affects {len(components)} components")

            rule = {
                "description": f"Auto-assign reviewers for {package} (affects {len(components)} components)",
                "matchDatasources": [ecosystem],
                "matchPackageNames": [package],
                "reviewers": reviewers[:5],  # Limit to 5 reviewers max
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
                rule = {
                    "description": f"Default reviewers for {package}",
                    "matchDatasources": [ecosystem],
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
    process_parser.add_argument('report_file', nargs='?', default='security-tooling/blackduck_report.json',
                               help='Black Duck report file (default: security-tooling/blackduck_report.json)')

    # Generate Renovate config
    renovate_parser = subparsers.add_parser('generate-renovate',
                                            help='Generate Renovate reviewer configuration')
    renovate_parser.add_argument('report_file', nargs='?', default='security-tooling/blackduck_report.json',
                                help='Black Duck report file (default: security-tooling/blackduck_report.json)')
    renovate_parser.add_argument('--output', default='security-tooling/generated/renovate-reviewers.json',
                                help='Output file (default: security-tooling/generated/renovate-reviewers.json)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'analyze':
        if args.go:
            result = analyze_go_reviewers(args.go)
            print(json.dumps(result, indent=2))
        elif args.npm:
            ownership_config = load_component_ownership()
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
