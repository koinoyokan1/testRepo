#!/usr/bin/env python3
"""
Simulate Black Duck vulnerability scan output.

This script reads the existing blackduck_report.json and outputs
a human-readable summary that mimics what Black Duck would produce.
"""

import json
import sys
from datetime import datetime


def load_blackduck_report(filepath="security-tooling/blackduck_report.json"):
    """Load Black Duck vulnerability report"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filepath} not found", file=sys.stderr)
        sys.exit(1)


def print_scan_header(report):
    """Print scan header information"""
    print("=" * 80)
    print("BLACK DUCK VULNERABILITY SCAN RESULTS")
    print("=" * 80)
    print()
    print(f"Project: {report.get('project_name', 'Unknown')}")
    print(f"Scan Date: {report.get('scan_date', 'Unknown')}")
    print(f"Status: {report.get('scan_status', 'Unknown')}")
    print()


def print_summary(report):
    """Print vulnerability summary"""
    summary = report.get('summary', {})
    total = report.get('total_vulnerabilities', 0)
    
    print("=" * 80)
    print("VULNERABILITY SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Vulnerabilities: {total}")
    print(f"  • Critical: {summary.get('critical', 0)}")
    print(f"  • High:     {summary.get('high', 0)}")
    print(f"  • Medium:   {summary.get('medium', 0)}")
    print(f"  • Low:      {summary.get('low', 0)}")
    print()


def print_vulnerabilities(report):
    """Print detailed vulnerability information"""
    vulnerabilities = report.get('vulnerabilities', [])
    
    if not vulnerabilities:
        print("No vulnerabilities found.")
        return
    
    print("=" * 80)
    print("VULNERABILITY DETAILS")
    print("=" * 80)
    print()
    
    # Group by ecosystem
    by_ecosystem = {}
    for vuln in vulnerabilities:
        ecosystem = vuln.get('ecosystem', 'unknown')
        if ecosystem not in by_ecosystem:
            by_ecosystem[ecosystem] = []
        by_ecosystem[ecosystem].append(vuln)
    
    for ecosystem, vulns in sorted(by_ecosystem.items()):
        print(f"\n{ecosystem.upper()} Ecosystem ({len(vulns)} vulnerabilities)")
        print("-" * 80)
        
        for i, vuln in enumerate(vulns, 1):
            component = vuln.get('component', 'Unknown')
            version = vuln.get('version', 'Unknown')
            cve = vuln.get('vulnerability_id', 'Unknown')
            severity = vuln.get('severity', 'Unknown')
            cvss = vuln.get('cvss_score', 'N/A')
            fixed_versions = vuln.get('fixed_versions', [])
            recommended = vuln.get('recommended_version', 'N/A')
            
            print(f"\n  {i}. {cve} ({severity} - CVSS {cvss})")
            print(f"     Component: {component} {version}")
            
            if fixed_versions:
                print(f"     Fixed in: {', '.join(map(str, fixed_versions))}")
                print(f"     Recommended: {recommended}")
            else:
                print(f"     ⚠️  NO FIX AVAILABLE")
            
            print(f"     File: {vuln.get('file_path', 'Unknown')}")


def print_recommendations(report):
    """Print remediation recommendations"""
    vulnerabilities = report.get('vulnerabilities', [])
    fixable = [v for v in vulnerabilities if v.get('fixed_versions') or v.get('recommended_version')]
    unfixable = [v for v in vulnerabilities if not (v.get('fixed_versions') or v.get('recommended_version'))]
    
    print()
    print("=" * 80)
    print("REMEDIATION RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    if fixable:
        print(f"✅ {len(fixable)} vulnerability(ies) have fixes available")
        print("   Run automated remediation: python3 security-tooling/generate_renovate_rules.py")
        print()
    
    if unfixable:
        print(f"⚠️  {len(unfixable)} vulnerability(ies) have NO fixes available")
        print("   Manual investigation required for:")
        for vuln in unfixable:
            print(f"     - {vuln.get('vulnerability_id')} in {vuln.get('component')}")
        print()
    
    print("Next Steps:")
    print("  1. Review vulnerabilities above")
    print("  2. Automated Renovate PRs will be created for fixable issues")
    print("  3. GitHub Issues will be created for unfixable vulnerabilities")
    print("  4. Monitor security-tooling/generated/ for Renovate configs")
    print()


def main():
    """Main function"""
    report = load_blackduck_report()
    
    print_scan_header(report)
    print_summary(report)
    print_vulnerabilities(report)
    print_recommendations(report)
    
    print("=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)
    

if __name__ == "__main__":
    main()
