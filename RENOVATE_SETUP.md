# Renovate + Black Duck Integration Setup Guide

This guide explains how to set up Renovate to automatically create PRs based on Black Duck vulnerability findings.

## Overview

The integration creates **separate PRs** (one per vulnerability) with security fixes based on Black Duck scan results.

## Architecture

```
Black Duck Scan → JSON Reports → Renovate Rules → Separate PRs (1 per fix)
```

1. **Black Duck findings** are stored in `blackduck.json` and `blackduck_report.json`
2. **Renovate** reads the configuration from `renovate.json`
3. **GitHub Actions** orchestrates the workflow
4. **Separate PRs** are created for each vulnerability fix

## Setup Steps

### 1. Enable Self-Hosted Renovate on GitHub

1. **Create a GitHub Personal Access Token (PAT)**:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes:
     - `repo` (full control)
     - `workflow`
   - Generate and copy the token

2. **Add the token as a repository secret**:
   - Go to your repo: https://github.com/koinoyokan1/testRepo/settings/secrets/actions
   - Click "New repository secret"
   - Name: `RENOVATE_TOKEN`
   - Value: Paste your PAT
   - Click "Add secret"

3. **Enable GitHub Actions**:
   - The workflow files are already in `.github/workflows/`
   - Actions should run automatically

### 2. Verify Configuration Files

Ensure these files exist in your repository:

- ✅ `renovate.json` - Base Renovate configuration
- ✅ `.github/workflows/renovate.yml` - Renovate workflow
- ✅ `.github/workflows/blackduck-integration.yml` - Black Duck integration
- ✅ `blackduck_report.json` - Black Duck vulnerability scan report
- ✅ `generate_renovate_rules.py` - Dynamic rule generator
- ✅ `simulate_blackduck.py` - Black Duck scan simulator

### 3. How It Works

#### Automatic Workflow

1. **Black Duck Integration workflow** runs:
   - Detects vulnerabilities from JSON files
   - Generates Renovate package rules
   - Uploads artifacts

2. **Renovate workflow** runs:
   - Dynamically generates Renovate rules from Black Duck findings
   - Merges generated rules with base `renovate.json` configuration
   - Creates **separate PRs** for each vulnerability found in Black Duck reports:
     - `fix(security): update gin to v1.9.1+ to fix CVE-2023-29401 (HIGH)`
     - Each PR includes CVE details, severity, and remediation steps

3. **PR Creation**:
   - ✅ One branch per vulnerability fix
   - ✅ One PR per branch
   - ✅ Security labels automatically applied
   - ✅ Detailed vulnerability information in PR body

### 4. Trigger Renovate Manually

You can trigger Renovate runs manually:

1. Go to: https://github.com/koinoyokan1/testRepo/actions
2. Select "Renovate" workflow
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

### 5. Expected PRs

Based on current Black Duck findings, you should see these PRs:

1. **PR #1**: `fix(security): update gin to v1.9.1+ to fix CVE-2023-29401 (HIGH)`
   - Updates `github.com/gin-gonic/gin` from v1.8.0 to v1.9.1
   - Fixes directory traversal vulnerability
   - Labels: `security`, `high-priority`, `blackduck`, `cve-2023-29401`

## Configuration Details

### Renovate Settings

Key settings in `renovate.json`:

- **`prConcurrentLimit: 0`** - No limit on concurrent PRs
- **`separateMinorPatch: true`** - Separate PRs for minor/patch updates
- **`separateMajorMinor: true`** - Separate PRs for major/minor updates
- **`groupName: null`** - Don't group updates (individual PRs)

### Package Rules

Each Black Duck vulnerability gets its own package rule:

```json
{
  "matchPackageNames": ["github.com/gin-gonic/gin"],
  "allowedVersions": ">=1.9.1",
  "groupName": null,
  "prTitle": "fix(security): update gin to v1.9.1+ to fix CVE-2023-29401 (HIGH)"
}
```

## Testing the Integration

### Test 1: Generate Renovate Rules

```bash
python3 generate_renovate_rules.py
```

Expected output:
- `renovate-blackduck-generated.json` with package rules
- Summary of vulnerabilities processed

### Test 2: Simulate Black Duck Scan

```bash
python3 simulate_blackduck.py
```

Expected output:
- Vulnerability details
- Renovate package rules

### Test 3: Manual Renovate Run

1. Push changes to `main` branch
2. GitHub Actions will trigger automatically
3. Check Actions tab for workflow runs
4. PRs should appear shortly after

## Troubleshooting

### No PRs Created

1. **Check GitHub Actions logs**:
   - Go to Actions tab
   - Check "Renovate" workflow logs

2. **Verify RENOVATE_TOKEN**:
   - Ensure the secret exists
   - Token must have `repo` and `workflow` scopes

3. **Check Renovate configuration**:
   ```bash
   # Validate renovate.json syntax
   npx --package renovate -c 'renovate-config-validator'
   ```

### PRs Not Separated

Ensure these settings in `renovate.json`:
- `groupName: null` in each package rule
- `separateMinorPatch: true`
- `separateMajorMinor: true`

## Customization

### Add More Vulnerabilities

1. Edit `blackduck_report.json`
2. Add new vulnerability objects to the `vulnerabilities` array
3. Run `generate_renovate_rules.py` to update rules
4. Commit and push changes

### Modify PR Template

Edit the `prBodyNotes` in `renovate.json` or `generate_renovate_rules.py`.

## Next Steps

1. ✅ Push all configuration files to GitHub
2. ✅ Set up RENOVATE_TOKEN secret
3. ✅ Enable GitHub Actions
4. ✅ Trigger initial Renovate run
5. ✅ Review and merge security PRs
6. ✅ Monitor for new vulnerabilities
