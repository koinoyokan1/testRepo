#!/usr/bin/env python3
"""
Helper functions for finding npm package reviewers based on component ownership.
"""

import json
import os
import subprocess
from collections import defaultdict
from typing import Dict, List
from pathlib import Path


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


def find_component_for_npm_file(file_path: str, components: List[dict]) -> dict:
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


def analyze_npm_package_reviewers(package_name: str, ownership_config: dict) -> dict:
    """
    Analyze which components use an npm package and determine reviewers.

    Returns:
        Dict with analysis results including files, components, and reviewers
    """
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
            component = find_component_for_npm_file(file_path, components)

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
    components_affected = []
    for comp_name, component in component_set.items():
        owners = component.get('owners', {})
        all_reviewers.update(owners.get('primary', []))
        all_reviewers.update(owners.get('secondary', []))

        components_affected.append({
            'name': comp_name,
            'files': sorted(files_by_component[comp_name]),
            'owners': owners
        })

    return {
        'package': package_name,
        'packages_affected': list(packages_affected.keys()),
        'components': component_set,
        'components_affected': components_affected,
        'reviewers': sorted(list(all_reviewers))
    }

