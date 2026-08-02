#!/usr/bin/env python3
"""
Scan container images from docker-compose.yml and Dockerfiles, find vulnerabilities from Black Duck report.
Generates Renovate rules for container image updates.

- Prebuilt images: Tracked in image_map.json and updated by Renovate's docker datasource
- Custom images: Detected from Dockerfiles and docker-compose.yml with build contexts

Vulnerabilities without a fix (no recommended_version or fixed_versions) are
filtered out and should be handled by create_github_issues.py instead.

Usage:
    python3 security-tooling/scan_container_images.py
"""

import json
import sys
import os
import re
import yaml
from collections import defaultdict


def is_fixable(vuln):
    """Check if a vulnerability has a fix available"""
    recommended_version = vuln.get('recommended_version')
    fixed_versions = vuln.get('fixed_versions', [])

    # Has fix if recommended_version exists or fixed_versions is non-empty
    if recommended_version and recommended_version not in [None, '', 'unknown']:
        return True
    if fixed_versions and len(fixed_versions) > 0:
        return True

    return False


def load_docker_compose(filepath="docker-compose.yml"):
    """Load docker-compose.yml to find custom images"""
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None


def load_blackduck_report(filepath="security-tooling/blackduck_report.json"):
    """Load Black Duck vulnerability report"""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_custom_images_from_compose(compose_data):
    """Extract custom images from docker-compose.yml"""
    custom_images = {}

    if not compose_data or 'services' not in compose_data:
        return custom_images

    for service_name, service_config in compose_data.get('services', {}).items():
        # Check if service has a build context (custom image)
        if 'build' in service_config:
            image_name = service_config.get('image', service_name)
            build_config = service_config['build']

            if isinstance(build_config, dict):
                context = build_config.get('context', '.')
                dockerfile = build_config.get('dockerfile', 'Dockerfile')
            else:
                context = build_config
                dockerfile = 'Dockerfile'

            dockerfile_path = os.path.join(context, dockerfile).replace('./', '')

            # Extract owner from comments if available
            owner = 'devops-team@company.com'  # default

            custom_images[image_name] = {
                'dockerfile': dockerfile_path,
                'context': context,
                'owner': owner,
                'service_name': service_name
            }

    return custom_images


def find_image_vulnerabilities(blackduck_report):
    """Extract container image vulnerabilities from Black Duck report"""
    image_vulns = defaultdict(list)

    for vuln in blackduck_report.get('vulnerabilities', []):
        ecosystem = vuln.get('ecosystem', '')
        if ecosystem == 'container':
            component = vuln['component']
            image_vulns[component].append(vuln)

    return image_vulns


def email_to_github_username(email):
    """Convert email to GitHub username by stripping @company.com"""
    if '@company.com' in email:
        return email.replace('@company.com', '')
    return email


def get_image_owner_from_compose(compose_file="docker-compose.yml"):
    """Extract owner from docker-compose.yml comments"""
    owners = {}

    try:
        with open(compose_file, 'r') as f:
            current_service = None
            in_services_block = False
            for line in f:
                stripped = line.strip()

                # Track if we're in the services block
                if stripped == 'services:':
                    in_services_block = True
                    continue

                # Detect service name (must be in services block, indented by 2 spaces, no leading spaces in stripped)
                if in_services_block and line.startswith('  ') and not line.startswith('    '):
                    if ':' in stripped and not stripped.startswith('#'):
                        service_name = stripped.split(':')[0].strip()
                        # Skip YAML keys like 'image', 'build', 'ports', etc.
                        if service_name not in ['image', 'build', 'ports', 'environment', 'container_name', 'volumes', 'depends_on', 'networks']:
                            current_service = service_name

                # Extract owner from comment
                if '# Owner:' in line and current_service:
                    owner = line.split('# Owner:')[1].strip()
                    owners[current_service] = owner
    except FileNotFoundError:
        pass

    return owners


def generate_renovate_rule_for_custom_image(image_name, image_data, vulns):
    """Generate a Renovate package rule for a custom container image"""

    recommended_version = vulns[0]['recommended_version'] if vulns else None

    if not recommended_version:
        return None

    # Build CVE list
    cve_list = [v['vulnerability_id'] for v in vulns]
    severity_list = [v['severity'] for v in vulns]
    highest_severity = 'HIGH' if 'HIGH' in severity_list else ('MEDIUM' if 'MEDIUM' in severity_list else 'LOW')

    # Extract base image from vulns
    base_image = vulns[0].get('base_image', 'unknown')
    dockerfile = image_data.get('dockerfile', 'Dockerfile')

    # Create rule description
    if len(cve_list) == 1:
        description = f"Black Duck - {image_name} {cve_list[0]} ({highest_severity}) - Custom Image"
    else:
        description = f"Black Duck - {image_name} multiple CVEs ({highest_severity}) - Custom Image"

    # Build PR title
    if len(cve_list) == 1:
        pr_title = f"Custom container image upgrade: rebuild {image_name} to fix {cve_list[0]} in base image"
    else:
        pr_title = f"Custom container image upgrade: rebuild {image_name} to fix {len(cve_list)} CVEs in base image"

    # Build PR body notes
    pr_body = [
        "### 🔒 Security Update - Custom Container Image",
        "",
        f"**Image**: {image_name}",
        f"**Base Image**: {base_image}",
        f"**Recommended Base**: Update to {base_image.split(':')[0]}:{recommended_version}",
        f"**Dockerfile**: {dockerfile}",
        ""
    ]

    pr_body.append("**Vulnerabilities in Base Image:**")
    pr_body.append("")

    for vuln in vulns:
        pr_body.extend([
            f"#### {vuln['vulnerability_id']} ({vuln['severity']})",
            f"- **CVSS Score**: {vuln['cvss_score']}",
            f"- **Description**: {vuln['description']}",
            ""
        ])

    pr_body.extend([
        "**Remediation Steps**:",
        "",
        f"1. Update the FROM statement in `{dockerfile}`",
        f"2. Change base image to: `{base_image.split(':')[0]}:{recommended_version}`",
        "3. Rebuild the container image",
        "4. Update the image reference in `docker-compose.yml`",
        "",
        "---",
        "",
        f"**Files to Update**: `{dockerfile}`, `docker-compose.yml`",
        "",
        "This PR was created based on Black Duck container image scan findings."
    ])

    # Create unique branch name to avoid collisions
    safe_image_name = image_name.replace('/', '-').replace(':', '-').replace('.', '-')
    safe_cve = cve_list[0].lower().replace('_', '-') if len(cve_list) == 1 else 'multiple-cves'
    branch_name = f"blackduck/custom-image/{safe_image_name}/{safe_cve}"

    rule = {
        "description": description,
        "matchFileNames": [dockerfile, "docker-compose.yml"],
        "enabled": True,
        "branchName": branch_name,  # Unique branch to prevent collision
        "prTitle": pr_title,
        "prBodyNotes": pr_body,
        "labels": [
            "security",
            f"{highest_severity.lower()}-priority",
            "blackduck",
            "container-image",
            "custom-image"
        ] + [cve.lower() for cve in cve_list],
        "reviewers": [email_to_github_username(image_data.get('owner', 'devops-team'))]
    }

    return rule


def main():
    print("=" * 70)
    print("CUSTOM CONTAINER IMAGE VULNERABILITY SCANNER")
    print("=" * 70)
    print()

    # Load configurations
    compose_data = load_docker_compose()
    blackduck_report = load_blackduck_report()
    owners = get_image_owner_from_compose()

    # Find image vulnerabilities (only custom images - prebuilt are in image_map.json)
    image_vulns = find_image_vulnerabilities(blackduck_report)

    if not image_vulns:
        print("✅ No custom container image vulnerabilities found!")
        print("   (Prebuilt images are tracked in image_map.json)")
        return 0

    # Extract custom images from docker-compose
    custom_images = extract_custom_images_from_compose(compose_data)

    # Update owners from compose file comments
    for service_name, owner in owners.items():
        for image_name, image_data in custom_images.items():
            if image_data['service_name'] == service_name:
                image_data['owner'] = owner

    # Filter for custom images only
    custom_image_vulns = {}
    for image_name, vulns in image_vulns.items():
        # Check if this is a custom image (contains company domain or matches compose)
        if 'ghcr.io/company' in image_name or image_name in custom_images:
            custom_image_vulns[image_name] = vulns

    if not custom_image_vulns:
        print("✅ No custom image vulnerabilities found!")
        print(f"   Total vulnerabilities: {len(image_vulns)} (all in prebuilt images)")
        print("   Prebuilt image vulnerabilities are handled by image_map.json Renovate updates")
        return 0

    print(f"Found vulnerabilities in {len(custom_image_vulns)} custom image(s)")
    print(f"   (Skipping {len(image_vulns) - len(custom_image_vulns)} prebuilt images tracked in image_map.json)")
    print()

    # Filter out unfixable vulnerabilities
    skipped_unfixable = []
    fixable_image_vulns = {}

    for image_name, vulns in custom_image_vulns.items():
        fixable_vulns = [v for v in vulns if is_fixable(v)]
        unfixable_vulns = [v for v in vulns if not is_fixable(v)]

        if fixable_vulns:
            fixable_image_vulns[image_name] = fixable_vulns

        if unfixable_vulns:
            skipped_unfixable.extend(unfixable_vulns)

    if skipped_unfixable:
        print(f"⚠️  Found {len(skipped_unfixable)} unfixable custom image vulnerability(ies):")
        for v in skipped_unfixable:
            print(f"   - {v.get('vulnerability_id')} in {v.get('component')}")
        print("   These will be handled by create_github_issues.py\n")

    # Generate Renovate rules for custom images
    renovate_rules = []

    # Process custom images
    for image_name, vulns in fixable_image_vulns.items():
        # Find matching custom image data
        # Black Duck may report image without version tag, docker-compose has it with tag
        image_data = None
        for custom_name, custom_data in custom_images.items():
            # Match with or without version tag
            custom_base = custom_name.split(':')[0]  # Remove :version
            image_base = image_name.split(':')[0]    # Remove :version

            if (custom_name == image_name or
                custom_base == image_base or
                image_name.endswith('/' + custom_name) or
                image_base.endswith('/' + custom_base.split('/')[-1])):
                image_data = custom_data
                break

        if not image_data:
            # Create minimal data if not found in compose
            image_data = {
                'dockerfile': 'Dockerfile',
                'owner': 'devops-team',  # GitHub username (not email)
                'service_name': image_name.split('/')[-1].split(':')[0]
            }

        print(f"🔨 {image_name} (CUSTOM)")
        print(f"   Dockerfile: {image_data['dockerfile']}")
        print(f"   Owner: {image_data['owner']}")
        print(f"   CVEs: {len(vulns)}")
        for v in vulns:
            print(f"     - {v['vulnerability_id']} ({v['severity']})")

        rule = generate_renovate_rule_for_custom_image(image_name, image_data, vulns)
        if rule:
            renovate_rules.append(rule)
        print()

    # Generate output
    output = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "description": "Auto-generated custom container image rules from Black Duck",
        "packageRules": renovate_rules
    }

    # Save to file
    os.makedirs("security-tooling/generated", exist_ok=True)
    output_file = "security-tooling/generated/renovate-container-images.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 70)
    print(f"✅ Generated {len(renovate_rules)} Renovate rule(s) for custom images")
    print(f"📁 Saved to: {output_file}")
    print("=" * 70)
    print()

    # Print summary
    print("📊 Summary:")
    print(f"  • Custom images with vulnerabilities: {len(fixable_image_vulns)}")
    print(f"  • Total CVEs in custom images: {sum(len(v) for v in fixable_image_vulns.values())}")
    print(f"  • Renovate rules generated: {len(renovate_rules)}")
    print()
    print("ℹ️  Note: Prebuilt images (nginx, postgres, redis, etc.) are tracked in image_map.json")
    print("   and updated automatically by Renovate's docker datasource.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
