#!/usr/bin/env python3
"""
Helper functions for finding Go package reviewers based on component ownership.
"""

import json
import os
import subprocess
from collections import defaultdict
from typing import Dict, List
from pathlib import Path


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


def find_component_for_file(filepath: str, components: List[dict]) -> Dict:
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

        for component in components:
            for comp_dir in component['directories']:
                if rel_path_str == comp_dir or rel_path_str.startswith(comp_dir + '/'):
                    return component

        if current_path == current_path.parent:
            break
        current_path = current_path.parent

    # No component found, return None
    return None




def get_reviewers_for_dependency(
    package_name: str,
    ownership_config: dict,
    include_secondary: bool = True
) -> Dict:
    """
    Main function: Get reviewers for a Go dependency update using go list.

    Args:
        package_name: Go package name (e.g., github.com/gin-gonic/gin)
        ownership_config: Component ownership configuration
        include_secondary: Whether to include secondary reviewers

    Returns:
        Dict with package info, affected modules/files/components, and reviewers
    """
    components = ownership_config.get('components', [])
    default_reviewers = ownership_config.get('default_reviewers', {"primary": [], "secondary": []})

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
        component = find_component_for_file(filepath, components)

        if component:
            comp_name = component['name']
        else:
            comp_name = "Default"
            component = {
                "name": "Default",
                "owners": default_reviewers
            }

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


def analyze_go_package_reviewers(package_name: str, ownership_config: dict) -> dict:
    """
    Analyze which components use a Go package and determine reviewers.

    This is the main entry point that matches the npm interface.

    Args:
        package_name: Go package name (e.g., github.com/gin-gonic/gin)
        ownership_config: Component ownership configuration

    Returns:
        Dict with analysis results including packages, components, and reviewers
    """
    result = get_reviewers_for_dependency(package_name, ownership_config, include_secondary=True)

    if not result:
        return {}

    # Convert components_affected list to dict keyed by name for consistency with npm
    components_dict = {}
    for comp in result.get('components_affected', []):
        components_dict[comp['name']] = comp

    return {
        'package': package_name,
        'packages_affected': result.get('modules_affected', []),
        'components': components_dict,
        'components_affected': result.get('components_affected', []),
        'reviewers': result.get('reviewers', [])
    }
