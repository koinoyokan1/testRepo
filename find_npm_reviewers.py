#!/usr/bin/env python3
"""
Find reviewers for npm package updates based on component ownership.
Uses npm ls to find which packages depend on a given npm package.
"""

import json
import os
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Set


def load_component_ownership(filepath: str = "component_ownership.json") -> dict:
    """Load component ownership configuration"""
    with open(filepath, 'r') as f:
        return json.load(f)


def find_all_package_json_files(root_dir: str = ".") -> List[str]:
    """
    Find all package.json files in the repository (including nested packages).
    Returns list of directories containing package.json files.
    """
    packages = []
    
    try:
        # Find all package.json files
        result = subprocess.run(
            ["find", root_dir, "-name", "package.json", "-type", "f", "-not", "-path", "*/node_modules/*"],
            capture_output=True,
            text=True,
            check=True
        )
        
        for package_json_path in result.stdout.strip().split('\n'):
            if package_json_path:
                # Get directory containing package.json
                package_dir = os.path.dirname(package_json_path)
                packages.append(package_dir if package_dir else ".")
        
    except subprocess.CalledProcessError:
        # Fallback to just current directory
        packages = ["."]
    
    return packages


def find_packages_using_dependency(package_name: str) -> Dict[str, List[str]]:
    """
    Find all npm packages that depend on the given package.
    
    Returns:
        Dict mapping package directory to list of files that import the package
    """
    result = defaultdict(list)
    
    # Find all package.json files
    all_packages = find_all_package_json_files()
    print(f"Found {len(all_packages)} npm package(s): {all_packages}")
    
    # Check each package
    for package_dir in all_packages:
        package_json_path = os.path.join(package_dir, "package.json")
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Check dependencies and devDependencies
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            if package_name in dependencies or package_name in dev_dependencies:
                # This package uses our target dependency
                # Find TypeScript/JavaScript files that import it
                ts_files = find_import_files(package_dir, package_name)
                result[package_dir] = ts_files
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Failed to read {package_json_path}: {e}")
            continue
    
    return result


def find_import_files(package_dir: str, package_name: str) -> List[str]:
    """Find TypeScript/JavaScript files that import the given package"""
    files = []
    
    try:
        # Search for imports in TypeScript and JavaScript files
        # Patterns: import ... from 'package' or require('package')
        result = subprocess.run(
            [
                "grep", "-r", "-l",
                "--include=*.ts",
                "--include=*.tsx", 
                "--include=*.js",
                "--include=*.jsx",
                "-E",
                f"(import.*from ['\"]({package_name}|{package_name}/.*)['\"]|require\\(['\"]({package_name}|{package_name}/.*)['\"\\)])",
                package_dir
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    
    except subprocess.CalledProcessError:
        pass
    
    return files


def find_component_for_file(file_path: str, components: List[dict]) -> dict:
    """
    Find the component that owns a file by matching directory prefixes.
    Returns the component dict or None.
    """
    # Normalize path
    abs_path = os.path.abspath(file_path)
    
    # Try to match from most specific to least specific
    best_match = None
    best_match_len = 0
    
    for component in components:
        for directory in component.get('directories', []):
            abs_dir = os.path.abspath(directory)
            
            # Check if file is under this directory
            if abs_path.startswith(abs_dir + os.sep) or abs_path.startswith(abs_dir):
                dir_len = len(abs_dir)
                if dir_len > best_match_len:
                    best_match = component
                    best_match_len = dir_len
    
    return best_match


def analyze_package_reviewers(package_name: str, ownership_file: str = "component_ownership.json") -> dict:
    """
    Analyze which components use a package and determine reviewers.
    
    Returns:
        Dict with analysis results including files, components, and reviewers
    """
    ownership_config = load_component_ownership(ownership_file)
    components = ownership_config.get('components', [])
    default_reviewers = ownership_config.get('default_reviewers', {})
    
    # Find packages that use this dependency
    packages_affected = find_packages_using_dependency(package_name)
    
    if not packages_affected:
        print(f"No packages found using {package_name}")
        return {}
    
    # Collect all affected files and components
    files_by_component = defaultdict(list)
    component_set = {}
    
    for package_dir, files in packages_affected.items():
        for file_path in files:
            component = find_component_for_file(file_path, components)
            
            if component:
                component_name = component['name']
            else:
                component_name = "Default"
                component = {
                    'name': 'Default',
                    'owners': default_reviewers
                }
            
            files_by_component[component_name].append(file_path)
            component_set[component_name] = component
    
    # Collect all reviewers
    all_reviewers = set()
    for component in component_set.values():
        owners = component.get('owners', {})
        all_reviewers.update(owners.get('primary', []))
        all_reviewers.update(owners.get('secondary', []))
    
    return {
        'package': package_name,
        'packages_affected': list(packages_affected.keys()),
        'files_by_component': dict(files_by_component),
        'components': component_set,
        'reviewers': sorted(list(all_reviewers))
    }


def print_analysis(analysis: dict):
    """Pretty print the analysis results"""
    if not analysis:
        return
    
    package = analysis['package']
    packages_affected = analysis['packages_affected']
    files_by_component = analysis['files_by_component']
    components = analysis['components']
    reviewers = analysis['reviewers']
    
    total_files = sum(len(files) for files in files_by_component.values())
    
    print("\n" + "="*70)
    print(f"REVIEWER ANALYSIS FOR: {package}")
    print("="*70)
    
    print(f"\n📊 Summary:")
    print(f"  • NPM packages affected: {len(packages_affected)}")
    print(f"  • Files affected: {total_files}")
    print(f"  • Components affected: {len(components)}")
    print(f"  • Total reviewers: {len(reviewers)}")
    
    print(f"\n📦 NPM Packages:")
    for pkg_dir in packages_affected:
        print(f"  - {pkg_dir}")
    
    print(f"\n🔍 Components Affected:")
    for component_name in sorted(files_by_component.keys()):
        component = components[component_name]
        files = files_by_component[component_name]
        owners = component.get('owners', {})
        
        print(f"\n  📦 {component_name}")
        print(f"     Files ({len(files)}):")
        for file_path in files[:5]:  # Show first 5 files
            print(f"       - {file_path}")
        if len(files) > 5:
            print(f"       ... and {len(files) - 5} more")
        
        print(f"     Owners:")
        print(f"       Primary: {', '.join(owners.get('primary', []))}")
        print(f"       Secondary: {', '.join(owners.get('secondary', []))}")
    
    print(f"\n👥 Reviewers to Add:")
    for reviewer in sorted(reviewers):
        print(f"  ✓ {reviewer}")
    
    print("\n" + "="*70)
    
    # JSON output
    print(f"\n📋 JSON Output:\n")
    print(json.dumps({
        'package': package,
        'packages_affected': packages_affected,
        'total_files': total_files,
        'components_affected': [
            {
                'name': name,
                'files': files_by_component[name],
                'owners': components[name].get('owners', {})
            }
            for name in sorted(files_by_component.keys())
        ],
        'total_components': len(components),
        'reviewers': reviewers
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 find_npm_reviewers.py <package-name>")
        print("Example: python3 find_npm_reviewers.py axios")
        sys.exit(1)
    
    package_name = sys.argv[1]
    analysis = analyze_package_reviewers(package_name)
    print_analysis(analysis)
