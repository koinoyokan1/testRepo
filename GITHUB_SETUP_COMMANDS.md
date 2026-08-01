# GitHub Setup Commands

Follow these commands to push your changes and set up Renovate.

## Step 1: Verify Your Local Setup

```bash
# Run validation script
./validate_setup.sh
```

**Expected:** All checks should pass ✓

## Step 2: Stage and Commit Changes

```bash
# Check git status
git status

# Add all new files
git add .

# Commit with descriptive message
git commit -m "feat: add Renovate + Black Duck integration

- Add Renovate configuration for automated dependency updates
- Add Black Duck vulnerability simulation files
- Configure GitHub Actions workflows for automation
- Add documentation and setup guides
- Configure separate PRs per CVE fix"

# View commit
git log -1 --stat
```

## Step 3: Push to GitHub

```bash
# Push to main branch
git push origin main

# Verify push
git status
```

## Step 4: Verify Files on GitHub

Open your repository: https://github.com/koinoyokan1/testRepo

Check that these files are present:
- ✅ `renovate.json`
- ✅ `.github/workflows/renovate.yml`
- ✅ `.github/workflows/blackduck-integration.yml`
- ✅ `blackduck.json`
- ✅ `blackduck_report.json`
- ✅ All documentation files

## Step 5: Set Up Renovate (Choose One Option)

### Option A: Renovate GitHub App (Easiest)

1. **Install the app**:
   ```
   Browser: https://github.com/apps/renovate
   Click: "Install" or "Configure"
   Select: "koinoyokan1/testRepo"
   Click: "Install & Authorize"
   ```

2. **Wait for Renovate**:
   - Renovate will detect `renovate.json` automatically
   - First run happens within minutes
   - PRs will be created automatically

3. **Check for PRs**:
   ```
   Browser: https://github.com/koinoyokan1/testRepo/pulls
   ```

### Option B: Self-Hosted Renovate (More Control)

1. **Create GitHub Personal Access Token**:
   ```
   Browser: https://github.com/settings/tokens
   Click: "Generate new token (classic)"
   
   Scopes to select:
   ✓ repo (Full control of private repositories)
   ✓ workflow (Update GitHub Action workflows)
   
   Click: "Generate token"
   Copy: The token (you won't see it again!)
   ```

2. **Add Token as Repository Secret**:
   ```
   Browser: https://github.com/koinoyokan1/testRepo/settings/secrets/actions
   Click: "New repository secret"
   
   Name: RENOVATE_TOKEN
   Secret: <paste your token>
   
   Click: "Add secret"
   ```

3. **Enable GitHub Actions**:
   ```
   Browser: https://github.com/koinoyokan1/testRepo/actions
   
   If prompted: Click "I understand my workflows, go ahead and enable them"
   ```

4. **Trigger First Run Manually**:
   ```
   Browser: https://github.com/koinoyokan1/testRepo/actions
   Click: "Renovate" workflow
   Click: "Run workflow"
   Select branch: main
   Click: "Run workflow"
   ```

5. **Monitor Workflow**:
   ```
   Browser: Stay on Actions page
   Watch: The workflow run (should complete in 1-2 minutes)
   Check: Logs for any errors
   ```

## Step 6: Verify PRs Were Created

```bash
# Check PRs via GitHub CLI (if installed)
gh pr list

# Or open in browser
# https://github.com/koinoyokan1/testRepo/pulls
```

**Expected PRs:**

1. **CVE-2023-29401 (HIGH)**:
   - Title: `fix(security): update gin to v1.9.1+ to fix CVE-2023-29401 (HIGH)`
   - Labels: `security`, `high-priority`, `blackduck`, `cve-2023-29401`
   - Branch: `renovate/gin-1.x` or similar

## Step 7: Review and Merge a PR

```bash
# Option 1: Via GitHub web interface
# Browser: https://github.com/koinoyokan1/testRepo/pulls
# Click on a PR → Review changes → Merge

# Option 2: Via command line (if gh CLI installed)
gh pr checkout <PR-number>
go mod verify
go run main.go  # Test the fix
gh pr merge <PR-number> --squash
```

## Step 8: Verify Fix

```bash
# Pull latest changes
git pull origin main

# Check updated version
cat go.mod | grep gin

# Expected: github.com/gin-gonic/gin v1.9.1 (or later)

# Test the application
go run main.go

# In another terminal:
curl http://localhost:8080/ping
# Expected: {"message":"pong"}
```

## Troubleshooting Commands

### Check GitHub Actions Logs

```bash
# Via GitHub CLI
gh run list
gh run view <run-id> --log

# Via browser
# https://github.com/koinoyokan1/testRepo/actions
```

### Verify Renovate Token (Self-Hosted)

```bash
# Via GitHub CLI
gh secret list

# Expected output should include: RENOVATE_TOKEN
```

### Test Black Duck Simulation Locally

```bash
# Full test
python3 simulate_blackduck.py

# Simple format only
python3 simulate_blackduck.py --simple

# Report format only
python3 simulate_blackduck.py --report
```

### Generate Renovate Rules Locally

```bash
# Generate rules
python3 generate_renovate_rules.py

# Check output
cat renovate-blackduck-generated.json | python3 -m json.tool
```

### Force Renovate to Run Again

```bash
# Via GitHub CLI
gh workflow run renovate.yml

# Via browser
# https://github.com/koinoyokan1/testRepo/actions/workflows/renovate.yml
# Click "Run workflow"
```

## Quick Reference

### Repository URL
```
https://github.com/koinoyokan1/testRepo
```

### Key URLs
- Actions: https://github.com/koinoyokan1/testRepo/actions
- PRs: https://github.com/koinoyokan1/testRepo/pulls
- Settings: https://github.com/koinoyokan1/testRepo/settings
- Secrets: https://github.com/koinoyokan1/testRepo/settings/secrets/actions

### Important Files
- Renovate config: `renovate.json`
- Renovate workflow: `.github/workflows/renovate.yml`
- Black Duck integration: `.github/workflows/blackduck-integration.yml`

## Success Criteria

✅ All files committed and pushed to GitHub
✅ Renovate installed (GitHub App or token configured)
✅ GitHub Actions enabled and running
✅ PRs created with CVE fixes
✅ PRs have correct labels and descriptions
✅ Separate PR per vulnerability
✅ PRs can be merged successfully

## Next Steps

After successful setup:

1. **Monitor for new vulnerabilities**: Workflows run automatically
2. **Review PRs**: Check security fixes as they're created
3. **Customize**: Modify `renovate.json` as needed
4. **Add more CVEs**: Update `blackduck_report.json` to test more scenarios
