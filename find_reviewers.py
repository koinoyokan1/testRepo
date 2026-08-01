#!/usr/bin/env python3
"""
Find component owners for a dependency update by:
1. Finding all files that import the dependency
2. Mapping files to components by directory
3. Identifying component owners
4. Returning list of reviewers
"""

import json
import os
import re
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set, Tuple


def load_component_ownership(filepath: str = "component_ownership.json") -> dict:
    """Load component ownership configuration"""
    with open(filepath, 'r') as f:
        return json.load(f)


def find_files_importing_package(package_name: str, root_dir: str = ".") -> List[str]:
    """
    Find all Go files that import the given package.
    Uses grep to search for import statements.
    """
    files = []
    
    # Search for import statements containing the package
    # Matches both: import "package" and import ( "package" )
    try:
        # Find all .go files
        result = subprocess.run(
            ["find", root_dir, "-name", "*.go", "-type", "f"],
            capture_output=True,
            text=True,
            check=True
        )
        
        go_files = result.stdout.strip().split('\n')
        
        # Check each file for the import
        for go_file in go_files:
            if not go_file:
                continue
                
            try:
                with open(go_file, 'r') as f:
                    content = f.read()
                    # Check if package is imported (DOTALL to match across newlines)
                    if re.search(rf'import\s+.*"{re.escape(package_name)}"', content, re.DOTALL):
                        files.append(go_file)
            except Exception as e:
                # Silently skip files that can't be read
                continue
                
    except subprocess.CalledProcessError:
        print(f"Warning: Could not search for files importing {package_name}")
    
    return files


def find_component_for_file(filepath: str, ownership_config: dict) -> Dict:
    """
    Find the component that owns a file by recursively checking parent directories.
    Returns the component config or default reviewers if not found.
    """
    # Normalize the file path
    file_path = Path(filepath).resolve()
    
    # Try each parent directory from most specific to least specific
    current_path = file_path.parent
    
    while True:
        # Make path relative to repo root
        try:
            rel_path = current_path.relative_to(Path.cwd())
            rel_path_str = str(rel_path)
        except ValueError:
            # We've gone above the repo root
            break
        
        # Check if this directory matches any component
        for component in ownership_config['components']:
            for comp_dir in component['directories']:
                if rel_path_str == comp_dir or rel_path_str.startswith(comp_dir + '/'):
                    return component
        
        # Move up one directory
        if current_path == current_path.parent:
            # Reached filesystem root
            break
        current_path = current_path.parent
    
    # No component found, return default
    return {
        "name": "Default",
        "owners": ownership_config.get('default_reviewers', {
            "primary": [],
            "secondary": []
        })
    }


def get_reviewers_for_dependency(
    package_name: str,
    ownership_config: dict,
    include_secondary: bool = True
) -> Dict[str, any]:
    """
    Main function: Get reviewers for a dependency update.
    Returns dict with components affected and list of reviewers.
    """
    # Step 1: Find all files importing the package
    files = find_files_importing_package(package_name)

    if not files:
        return {
            "package": package_name,
            "files_affected": [],
            "total_files": 0,
            "components_affected": [],
            "total_components": 0,
            "reviewers": []
        }

    # Step 2: Map files to components
    component_files = defaultdict(list)
    components_found = {}

    for filepath in files:
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
        "files_affected": sorted(files),
        "total_files": len(files),
        "components_affected": components_affected,
        "total_components": len(components_affected),
        "reviewers": sorted(list(reviewers))
    }


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 find_reviewers.py <package_name> [--primary-only]")
        print("Example: python3 find_reviewers.py github.com/gin-gonic/gin")
        sys.exit(1)

    package_name = sys.argv[1]
    include_secondary = "--primary-only" not in sys.argv

    # Load ownership config
    ownership_config = load_component_ownership()

    # Get reviewers
    result = get_reviewers_for_dependency(
        package_name,
        ownership_config,
        include_secondary
    )

    # Pretty print results
    print(f"\n{'='*70}")
    print(f"REVIEWER ANALYSIS FOR: {result['package']}")
    print(f"{'='*70}\n")

    print(f"📊 Summary:")
    print(f"  • Files affected: {result['total_files']}")
    print(f"  • Components affected: {result['total_components']}")
    print(f"  • Total reviewers: {len(result['reviewers'])}")

    print(f"\n🔍 Components Affected:\n")
    for component in result['components_affected']:
        print(f"  📦 {component['name']}")
        print(f"     Files ({len(component['files'])}):")
        for file in component['files'][:5]:  # Show first 5 files
            print(f"       - {file}")
        if len(component['files']) > 5:
            print(f"       ... and {len(component['files']) - 5} more")

        print(f"     Owners:")
        print(f"       Primary: {', '.join(component['owners']['primary'])}")
        print(f"       Secondary: {', '.join(component['owners']['secondary'])}")
        print()

    print(f"👥 Reviewers to Add:")
    for reviewer in result['reviewers']:
        print(f"  ✓ {reviewer}")

    print(f"\n{'='*70}")

    # Also output JSON for programmatic use
    print(f"\n📋 JSON Output:\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
