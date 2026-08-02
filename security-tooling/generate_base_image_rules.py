#!/usr/bin/env python3
"""
Generate Renovate package rules for container base image updates.

This script reads image_map.json and component_ownership.json to create
package rules with reviewers for each base image.

Usage:
    python3 security-tooling/generate_base_image_rules.py
"""

import json
import sys
import os


def email_to_github_username(email):
    """Convert email to GitHub username by stripping @company.com"""
    if '@company.com' in email:
        return email.replace('@company.com', '')
    return email


def load_component_ownership(filepath="security-tooling/component_ownership.json"):
    """Load component ownership configuration"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Warning: {filepath} not found, reviewers will not be assigned")
        return {"base_images": {}, "default_reviewers": {"primary": [], "secondary": []}}


def load_image_map(filepath="image_map.json"):
    """Load image map configuration"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {filepath} not found")
        return {}


def get_reviewers_for_image(image_name, ownership_config):
    """
    Get reviewers for a container base image.
    
    Args:
        image_name: Name of the image (e.g., "node", "postgres", "red/config")
        ownership_config: Component ownership configuration dict
        
    Returns:
        Dict with reviewers list and labels
    """
    base_images = ownership_config.get('base_images', {})
    default_reviewers = ownership_config.get('default_reviewers', {})
    
    # Look up image-specific owners
    image_config = base_images.get(image_name)
    
    if image_config:
        owners = image_config.get('owners', {})
    else:
        # Fall back to default reviewers
        owners = default_reviewers
    
    # Collect primary and secondary owners (convert emails to GitHub usernames)
    reviewers = list(set(
        owners.get('primary', []) +
        owners.get('secondary', [])
    ))

    # Convert email addresses to GitHub usernames
    reviewers = [email_to_github_username(r) for r in reviewers]

    # Create label for the image type
    image_label = f"image:{image_name.replace('/', '-')}"

    return {
        "reviewers": sorted(reviewers),
        "labels": [image_label]
    }


def generate_base_image_rule(image_name, image_data, ownership_config):
    """Generate a Renovate package rule for a base image"""
    origin_image = image_data.get('origin_image', '')
    
    if not origin_image:
        return None
    
    # Parse origin_image to get dep name
    if ':' in origin_image:
        dep_name = origin_image.split(':')[0]
    else:
        dep_name = origin_image
    
    # Get reviewers for this image
    reviewer_info = get_reviewers_for_image(image_name, ownership_config)
    
    package_rule = {
        "description": f"Container base image: {image_name} ({dep_name})",
        "matchManagers": ["regex"],
        "matchFileNames": ["image_map.json"],
        "matchPackageNames": [dep_name],
        "enabled": True,
        "groupName": f"container-base-image-{image_name.replace('/', '-')}",
        "prTitle": f"Container base image upgrade: update {image_name} ({{{{depName}}}}) to {{{{newVersion}}}}",
        "labels": [
            "dependencies",
            "security",
            "container-image",
            "prebuilt"
        ] + reviewer_info.get("labels", []),
        "reviewers": reviewer_info.get("reviewers", []),
        "semanticCommitType": "fix",
        "semanticCommitScope": "security"
    }
    
    return package_rule


def main():
    print("=" * 70)
    print("RENOVATE BASE IMAGE RULE GENERATOR")
    print("=" * 70)
    print()
    
    # Load configurations
    ownership_config = load_component_ownership()
    image_map = load_image_map()
    
    if not image_map:
        print("❌ No images found in image_map.json!")
        return 1
    
    print(f"Found {len(image_map)} base image(s)")
    print()
    
    # Generate package rules
    package_rules = []
    
    for image_name, image_data in image_map.items():
        print(f"📦 {image_name}: {image_data.get('origin_image', 'N/A')}")
        
        rule = generate_base_image_rule(image_name, image_data, ownership_config)
        if rule:
            package_rules.append(rule)
            reviewers = rule.get('reviewers', [])
            print(f"   Reviewers: {', '.join(reviewers) if reviewers else 'None'}")
        
        print()
    
    # Create output configuration
    output = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated package rules for container base images with reviewers",
        "packageRules": package_rules
    }
    
    # Write to file
    os.makedirs("security-tooling/generated", exist_ok=True)
    output_file = "security-tooling/generated/renovate-base-image-rules.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 70)
    print(f"✅ Generated {len(package_rules)} package rule(s)")
    print(f"📝 Saved to: {output_file}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
