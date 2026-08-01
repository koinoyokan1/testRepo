# Quick Start Guide

## Prerequisites

- GitHub repository: `https://github.com/koinoyokan1/testRepo`
- All configuration files pushed to `main` branch

## Setup (5 minutes)

### Step 1: Self-Hosted Renovate Setup

1. **Create GitHub Token**:
   ```
   GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   Scopes: repo, workflow
   ```

2. **Add Secret**:
   ```
   Repository Settings → Secrets and variables → Actions → New repository secret
   Name: RENOVATE_TOKEN
   Value: <your-token>
   ```

3. **Enable Actions**:
   - Actions are already configured in `.github/workflows/`
   - Will run automatically on schedule and on push

### Step 2: Verify Configuration

Check that these files exist in your repo:

```bash
# Configuration files
✅ renovate.json
✅ .github/workflows/renovate.yml
✅ .github/workflows/blackduck-integration.yml

# Black Duck simulation files
✅ blackduck_report.json
✅ simulate_blackduck.py
✅ generate_renovate_rules.py
```

### Step 3: Trigger First Run

1. Go to Actions tab: https://github.com/koinoyokan1/testRepo/actions
2. Select "Renovate" workflow
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

Alternatively, Renovate runs automatically every hour on schedule.

### Step 4: Review PRs

Within a few minutes, you should see PRs created:

1. **PR for CVE-2023-29401 (HIGH)**
   - Title: `fix(security): update gin to v1.9.1+ to fix CVE-2023-29401 (HIGH)`
   - Branch: `renovate/gin-1.x`
   - Labels: `security`, `high-priority`, `blackduck`

2. **PR for CVE-2023-26125 (MEDIUM)**
   - Will be created if configured for separate PRs per CVE

## Testing Locally

### Test 1: Simulate Black Duck Scan

```bash
python3 simulate_blackduck.py
```

**Expected output:**
- Vulnerability details for both CVEs
- Renovate package rules

### Test 2: Generate Renovate Rules

```bash
python3 generate_renovate_rules.py
```

**Expected output:**
- `renovate-blackduck-generated.json` file created
- Summary of 2 vulnerabilities processed

### Test 3: Run Go Application

```bash
# Install dependencies
go mod download

# Run server
go run main.go

# Test in another terminal
curl http://localhost:8080/ping
curl http://localhost:8080/hello/Renovate
```

## Expected Results

### GitHub Actions Workflows

1. **Renovate workflow** - Runs hourly and on-demand
   - Processes Black Duck findings
   - Creates PRs for vulnerabilities

2. **Black Duck Integration workflow** - Runs daily
   - Simulates Black Duck scan
   - Generates Renovate rules
   - Uploads reports as artifacts

### Pull Requests

Each PR will include:

- ✅ **Security labels**: `security`, `blackduck`, `high-priority` or `medium-priority`
- ✅ **Detailed description**: CVE ID, CVSS score, description, remediation
- ✅ **Automated updates**: Updates `go.mod` and `go.sum`
- ✅ **Separate branch**: One branch per vulnerability fix

### PR Body Example

```markdown
This PR updates **github.com/gin-gonic/gin** from `1.8.0` to `1.9.1`.

### 🔒 Security Update - Black Duck Finding

**Vulnerability**: CVE-2023-29401
**Severity**: HIGH (CVSS 7.5)
**Current Version**: 1.8.0
**Fixed Version**: 1.9.1+

**Description**: Directory traversal vulnerability in gin-gonic/gin allows 
attackers to access files outside the intended directory.

**Remediation**: Update github.com/gin-gonic/gin to version 1.9.1 or later.

This PR was created based on Black Duck security scan findings.
```

## Troubleshooting

### No PRs Created?

1. **Check Actions logs**:
   - Go to Actions tab
   - View "Renovate" workflow logs
   - Look for errors

2. **Verify token**:
   - Check that `RENOVATE_TOKEN` secret exists
   - Token must have `repo` and `workflow` scopes

### PRs Not Separated?

Verify `renovate.json` has:
- `"groupName": null` in each package rule
- `"separateMinorPatch": true`
- `"prConcurrentLimit": 0`

### Need Help?

See the detailed setup guide: [RENOVATE_SETUP.md](RENOVATE_SETUP.md)

## Next Steps

1. ✅ Merge security PRs
2. ✅ Verify fixes with `go run main.go`
3. ✅ Add more vulnerabilities to `blackduck_report.json` (optional)
4. ✅ Customize PR templates in `renovate.json` (optional)
5. ✅ Monitor for new vulnerabilities automatically
