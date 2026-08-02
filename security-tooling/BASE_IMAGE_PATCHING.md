# Base Image OS Package Patching

## Overview

This feature automatically patches Dockerfiles to upgrade vulnerable OS packages that exist in base image layers but are not explicitly installed via RUN commands.

## The Problem

Traditional Renovate regex managers can only update packages that appear in explicit RUN commands:

```dockerfile
# Renovate CAN update this:
RUN apk add curl=7.88.0-r0

# But Renovate CANNOT update packages in the base image:
FROM node:16.14.0-alpine
# alpine:3.16 contains libssl3=3.0.8-r0 (VULNERABLE)
# This package is invisible to regex managers!
```

## The Solution

Three scripts work together to enable automated patching:

### 1. detect_base_image_vulns.py

**Purpose:** Categorize vulnerabilities into base image vs. explicit install

**Logic:**
- Reads Black Duck report
- For each OS-level vulnerability, checks if package appears in a RUN command
- If NOT found in RUN commands, it's a base image vulnerability
- Outputs categorization to `generated/vuln-categorization.json`

**Output Example:**
```json
{
  "base_image_vulns": [
    {
      "component": "libssl3",
      "version": "3.0.8-r0",
      "fixed_version": "3.0.9-r1",
      "ecosystem": "alpine",
      "file_path": "services/web-frontend/Dockerfile"
    }
  ],
  "explicit_install_vulns": [...]
}
```

### 2. patch_base_image_dockerfiles.py

**Purpose:** Automatically modify Dockerfiles to add upgrade commands

**Features:**
- Supports `--dry-run` for preview
- Detects package manager (apk/apt/yum) from base image
- Inserts upgrade command after FROM, before COPY (optimal for Docker cache)
- Idempotent: won't duplicate existing upgrade commands
- Groups multiple packages into single RUN command per Dockerfile

**Insertion Strategy:**
```dockerfile
FROM node:16.14.0-alpine

# INSERTED HERE (after FROM, before other commands)
# Security: Upgrade base image OS packages to fix vulnerabilities
# Fixes: CVE-2023-2650
RUN apk upgrade --no-cache libssl3=3.0.9-r1 libcrypto3=3.0.9-r1

WORKDIR /app
COPY . .
```

**Output:** 
- Modified Dockerfiles
- `generated/dockerfile-patches.json` (metadata)

### 3. generate_upgrade_regex.py

**Purpose:** Create Renovate regex managers to keep upgrades current

**Generates:**
- Regex patterns matching the upgrade commands
- Package rules with allowedVersions to prevent breaking changes
- CVE metadata for PR descriptions

**Output Example:**
```json
{
  "regexManagers": [
    {
      "description": "Manage base image OS package upgrades in Dockerfile",
      "fileMatch": ["services/web-frontend/Dockerfile"],
      "matchStrings": [
        "RUN\\s+apk\\s+upgrade\\s+--no-cache\\s+.*?libssl3=(?<currentValue>[^\\s]+)"
      ],
      "datasourceTemplate": "repology",
      "depNameTemplate": "libssl3",
      "packageNameTemplate": "alpine/libssl3"
    }
  ],
  "packageRules": [
    {
      "matchPackageNames": ["alpine/libssl3"],
      "allowedVersions": ">=3.0.9 <3.1.0",
      "description": "Fix CVE-2023-2650"
    }
  ]
}
```

## Workflow Integration

### GitHub Actions (.github/workflows/renovate.yml)

```yaml
- name: Detect base image vulnerabilities
  run: python3 security-tooling/detect_base_image_vulns.py

- name: Patch Dockerfiles  
  run: python3 security-tooling/patch_base_image_dockerfiles.py

- name: Generate upgrade regex
  run: python3 security-tooling/generate_upgrade_regex.py

- name: Merge Renovate configs
  run: |
    # Merges all configs into renovate-merged.json
    python3 -c "import json; ..."
```

## Supported Package Managers

| Package Manager | Distribution | Command Format |
|-----------------|--------------|----------------|
| apk | Alpine | `RUN apk upgrade --no-cache pkg=ver` |
| apt | Debian/Ubuntu | `RUN apt-get install --only-upgrade pkg=ver` |
| yum | RHEL/CentOS | `RUN yum update -y pkg-ver` |

## Example End-to-End Flow

### Initial State
- Black Duck detects CVE-2023-2650 in libssl3=3.0.8-r0
- Package is in node:16.14.0-alpine base image
- NOT in any RUN command

### After Scripts Run
```dockerfile
FROM node:16.14.0-alpine

# Security: Upgrade base image OS packages to fix vulnerabilities
# Fixes: CVE-2023-2650
RUN apk upgrade --no-cache libssl3=3.0.9-r1 libcrypto3=3.0.9-r1

WORKDIR /app
COPY . .
```

### Future Renovate PR
When libssl3=3.0.10-r0 is released:
- Renovate detects update via Repology datasource
- Creates PR updating 3.0.9-r1 to 3.0.10-r0
- allowedVersions ensures it stays in 3.0.x range

## Benefits

- **Automated:** Runs in CI/CD pipeline
- **Non-breaking:** Version constraints prevent major updates
- **Granular:** Updates specific packages, not entire base image
- **Self-maintaining:** Renovate keeps packages current
- **Complete coverage:** Fills the gap in vulnerability remediation

## Limitations

- Only works for ecosystems with Repology datasource
- Requires Black Duck to identify vulnerable packages
- Cannot fix vulnerabilities in packages without available updates
- Adds slight build time overhead (one extra RUN layer)

## Testing

```bash
# Run full integration test
./test_base_image_patching.sh

# Or step-by-step
python3 security-tooling/detect_base_image_vulns.py
python3 security-tooling/patch_base_image_dockerfiles.py --dry-run
python3 security-tooling/patch_base_image_dockerfiles.py
python3 security-tooling/generate_upgrade_regex.py
```

## Troubleshooting

**No base image vulnerabilities detected?**
- Check `generated/vuln-categorization.json`
- Verify Black Duck report has OS-level vulnerabilities
- Ensure packages are NOT already in RUN commands

**Patch failed?**
- Check Dockerfile syntax
- Verify package manager is supported
- Review error message for specific issue

**Renovate not creating PRs?**
- Verify `renovate-merged.json` includes the regex managers
- Check Repology has the package
- Confirm allowedVersions range includes available updates
