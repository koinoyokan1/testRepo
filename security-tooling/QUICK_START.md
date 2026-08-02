# Quick Start: Base Image OS Package Patching

## TL;DR

Black Duck finds CVE in base image OS package → Script patches Dockerfile → Renovate keeps it updated

## Run the Test

```bash
./test_base_image_patching.sh
```

This will:
- Detect base image vulnerabilities
- Preview what would be patched

## Step-by-Step Usage

### 1. Detect Vulnerabilities

```bash
python3 security-tooling/detect_base_image_vulns.py
```

Output: `security-tooling/generated/vuln-categorization.json`

### 2. Preview Patches (Dry Run)

```bash
python3 security-tooling/patch_base_image_dockerfiles.py --dry-run
```

Shows what would be changed without modifying files.

### 3. Apply Patches

```bash
python3 security-tooling/patch_base_image_dockerfiles.py
```

Output: 
- Modified Dockerfiles
- `security-tooling/generated/dockerfile-patches.json`

### 4. Generate Renovate Config

```bash
python3 security-tooling/generate_upgrade_regex.py
```

Output: `security-tooling/generated/renovate-base-image-upgrades.json`

### 5. Review Changes

```bash
git diff services/*/Dockerfile
cat security-tooling/generated/renovate-base-image-upgrades.json
```

### 6. Commit and Push

```bash
git add .
git commit -m "fix(security): patch base image OS packages"
git push
```

## Example Transformation

### Before
```dockerfile
FROM node:16.14.0-alpine
WORKDIR /app
COPY . .
```

### After
```dockerfile
FROM node:16.14.0-alpine

# Security: Upgrade base image OS packages to fix vulnerabilities
# Fixes: CVE-2023-2650
RUN apk upgrade --no-cache libssl3=3.0.9-r1 libcrypto3=3.0.9-r1

WORKDIR /app
COPY . .
```

## Automatic Mode (GitHub Actions)

The scripts run automatically in CI/CD. Just push code and the workflow handles everything!

## Common Commands

```bash
# Check what vulnerabilities exist
cat security-tooling/generated/vuln-categorization.json | jq '.base_image_vulns'

# Preview patches only
python3 security-tooling/patch_base_image_dockerfiles.py --dry-run

# Test Docker builds after patching
cd services/web-frontend && docker build .

# Verify Renovate config is valid
cat security-tooling/generated/renovate-base-image-upgrades.json | jq .
```

## What Gets Created

```
security-tooling/generated/
├── vuln-categorization.json          # Vulnerability categories
├── dockerfile-patches.json            # Patch metadata
└── renovate-base-image-upgrades.json  # Renovate config

services/*/Dockerfile                  # Modified with upgrade commands
```

## FAQ

**Q: Will this break my Docker builds?**  
A: No. The script uses pinned versions from Black Duck.

**Q: What if I don't want to patch a specific file?**  
A: Revert the Dockerfile and exclude it from the workflow.

**Q: Does this work with all base images?**  
A: Yes, as long as they use apk, apt, or yum package managers.

**Q: How do I undo changes?**  
A: `git checkout services/web-frontend/Dockerfile`

## Supported Distributions

- Alpine (apk)
- Debian/Ubuntu (apt)
- RHEL/CentOS (yum)

## Documentation

- **BASE_IMAGE_PATCHING.md** - Complete feature guide
- **ARCHITECTURE.md** - System design
- **README.md** - Updated with full coverage info

## Support

For issues or questions:
1. Check Black Duck report format
2. Verify Dockerfile syntax
3. Review script output for errors
4. Check package manager is supported
