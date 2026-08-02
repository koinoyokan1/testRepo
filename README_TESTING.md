# Testing Renovate Integration

## How to View the Generated Configuration

The GitHub Actions workflow **automatically generates and prints** the complete `renovate-merged.json` to the workflow logs. You don't need any scripts - just view the logs!

### Method 1: GitHub Web UI

1. Go to **Actions** tab: https://github.com/koinoyokan1/testRepo/actions
2. Click on the latest **"Renovate"** workflow run
3. Click on the **"Generate Black Duck Renovate Rules"** step
4. Scroll to find the section:
   ```
   ================================================================================
   RENOVATE MERGED CONFIGURATION (renovate-merged.json)
   ================================================================================
   ```
5. The complete JSON configuration is printed there

### Method 2: Extract from Workflow Logs (with GitHub CLI)

If you have `gh` CLI installed:

```bash
# Get the latest workflow run
gh run list --workflow=renovate.yml --limit 1

# View the logs
gh run view <RUN_ID> --log

# Or save to file
gh run view <RUN_ID> --log > /tmp/workflow-logs.txt

# Extract just the JSON
sed -n '/^{$/,/^}$/p' /tmp/workflow-logs.txt > renovate-merged.json
```

### Method 3: Download Logs Manually

1. Go to the workflow run page
2. Click the **⋮** (three dots) menu in the top right
3. Select **"Download log archive"**
4. Extract and search for `RENOVATE MERGED CONFIGURATION`

## What to Check

### Expected Output Structure

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "packageRules": [
    {
      "description": "Disable all updates by default...",
      "enabled": false
    },
    {
      "description": "Black Duck - CVE-2024-88888 (HIGH) - go",
      "matchPackageNames": ["github.com/google/uuid"],
      "reviewers": ["alice", "bob", "charlie", "david"],
      ...
    },
    ...
  ],
  "regexManagers": [ ... ]
}
```

### Key Verification Points

1. **Total Rules**: Should have ~35 package rules
2. **Reviewer Assignment**: Check that test packages have correct reviewers:
   - `github.com/google/uuid` → `alice, bob, charlie, david`
   - `validator` → `xavier, yvonne`
   - `qs` → `adam, zoe`
   - `rabbitmq` → `paul, quinn`
   - `elasticsearch` → `paul, quinn`

3. **Regex Managers**: Should have ~8 regex managers for Dockerfile OS packages

## Quick Verification Script

If you have the workflow logs saved to `/tmp/workflow-logs.txt`:

```bash
# Extract the JSON portion
awk '/^{$/,/^}$/' /tmp/workflow-logs.txt > renovate-merged.json

# Verify reviewer assignments
python3 << 'EOF'
import json

with open('renovate-merged.json') as f:
    config = json.load(f)

test_packages = {
    'github.com/google/uuid': ['alice', 'bob', 'charlie', 'david'],
    'validator': ['xavier', 'yvonne'],
    'qs': ['adam', 'zoe'],
    'rabbitmq': ['paul', 'quinn'],
    'elasticsearch': ['paul', 'quinn']
}

print("Verifying reviewer assignments:\n")
for rule in config.get('packageRules', []):
    for pkg_name, expected_reviewers in test_packages.items():
        if pkg_name in rule.get('matchPackageNames', []):
            actual = rule.get('reviewers', [])
            status = "✅" if set(actual) == set(expected_reviewers) else "❌"
            print(f"{status} {pkg_name}: {actual}")

print(f"\nTotal package rules: {len(config.get('packageRules', []))}")
print(f"Total regex managers: {len(config.get('regexManagers', []))}")
EOF
```

## Current Workflow Status

Check the status at: https://github.com/koinoyokan1/testRepo/actions

The workflow triggered by commit `7a0d91a` should show:
- ✅ All reviewer assignments correct
- ✅ 12 PRs created (2 per type × 6 types)
- ✅ No PRs for unresolvable vulnerabilities

## Why No Separate Script?

The workflow **already generates and prints** the complete configuration to logs. Creating a separate local generation script would:
- Duplicate the workflow logic (maintenance burden)
- Risk divergence between local and CI/CD behavior
- Add unnecessary complexity

Instead, **just check the workflow logs** to see exactly what Renovate will use!
