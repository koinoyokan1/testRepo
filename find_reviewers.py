#!/usr/bin/env python3
"""
Find component owners for a dependency update using Go's native tooling.

This script uses 'go list -json ./...' to accurately find all Go packages
that import a specific dependency, respecting Go module boundaries, build tags,
and the Go build system.

Requirements:
- Go toolchain installed (go command available)
- Valid go.mod file in the repository root
"""

import json
import os
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set


def load_component_ownership(filepath: str = "component_ownership.json") -> dict:
    """Load component ownership configuration"""
    with open(filepath, 'r') as f:
        return json.load(f)


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
                deps = pkg.get('Deps', [])
                go_files = pkg.get('GoFiles', [])
                pkg_dir = pkg.get('Dir', '')

                # Check direct imports
                if package_name in imports:
                    # This package directly imports our target
                    for go_file in go_files:
                        file_path = os.path.join(pkg_dir, go_file)
                        result[pkg.get('ImportPath', '')].append(file_path)

                # Optionally check transitive dependencies
                # if package_name in deps:
                #     # This package transitively depends on our target

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
    Main function: Get reviewers for a dependency update using go list.
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


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 find_reviewers.py <package_name> [--primary-only]")
        print("Example: python3 find_reviewers.py github.com/gin-gonic/gin")
        print("\nRequires Go toolchain and valid go.mod file")
        sys.exit(1)

    package_name = sys.argv[1]
    include_secondary = "--primary-only" not in sys.argv

    ownership_config = load_component_ownership()
    result = get_reviewers_for_dependency(package_name, ownership_config, include_secondary)

    print(f"\n{'='*70}")
    print(f"REVIEWER ANALYSIS FOR: {result['package']}")
    print(f"{'='*70}\n")

    print(f"📊 Summary:")
    print(f"  • Go modules affected: {len(result['modules_affected'])}")
    print(f"  • Files affected: {result['total_files']}")
    print(f"  • Components affected: {result['total_components']}")
    print(f"  • Total reviewers: {len(result['reviewers'])}")

    if result['modules_affected']:
        print(f"\n📦 Go Modules:")
        for module in result['modules_affected']:
            print(f"  - {module}")

    print(f"\n🔍 Components Affected:\n")
    for component in result['components_affected']:
        print(f"  📦 {component['name']}")
        print(f"     Files ({len(component['files'])}):")
        for file in component['files'][:5]:
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
    print(f"\n📋 JSON Output:\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
