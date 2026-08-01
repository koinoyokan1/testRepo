#!/usr/bin/env python3
"""
Unified reviewer finder for both Go and npm dependencies.
Determines which teams should review based on Black Duck findings.
"""

import json
import sys
from find_reviewers import get_reviewers_for_dependency, load_component_ownership
from find_npm_reviewers import analyze_package_reviewers as analyze_npm_reviewers


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
    
    if ecosystem == 'npm':
        return analyze_npm_reviewers(component)
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


if __name__ == "__main__":
    report_file = sys.argv[1] if len(sys.argv) > 1 else "blackduck_report.json"
    
    results = process_blackduck_report(report_file)
    summary = generate_summary(results)
    print_summary(summary)
    
    # Save to file for GitHub Actions
    output_file = "reviewer_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': summary,
            'detailed_results': {
                pkg: data['analysis']
                for pkg, data in results.items()
            }
        }, f, indent=2)
    
    print(f"📁 Detailed analysis saved to: {output_file}")
