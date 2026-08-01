# Black Duck + Renovate Integration with Component Ownership

This repository demonstrates automated vulnerability remediation using **Black Duck** security scanning and **Renovate** dependency updates, with intelligent **component-based reviewer assignment**.

## Project Overview

- **Go Module**: `example.com/oldversion`
- **Vulnerable Package**: `github.com/gin-gonic/gin v1.8.0` (older version with known CVEs)
- **Application**: Multi-service Go application (API Gateway, Auth, Users, Payment, Utilities)
- **Automation**:
  - Black Duck detects vulnerabilities
  - Renovate creates PRs with version constraints (e.g., v1.9.x, not v1.12.0)
  - Component owners automatically assigned as reviewers

## ✨ Key Features

1. **Automated Reviewer Assignment** - Uses `go list` to find affected components
2. **Version Constraints** - Stays within same minor version to minimize breaking changes
3. **Component Ownership** - Maps directory structure to teams and owners
4. **Mock Infrastructure** - Complete working example with 6 components

## 📋 Requirements

- **Go 1.20+** (required for `go list` dependency analysis)
- **Python 3.9+**
- **Git**
- **GitHub Actions** (for automated workflow)

## 🚀 Quick Start

### 1. Review Component Ownership

See [COMPONENT_OWNERSHIP.md](COMPONENT_OWNERSHIP.md) for the ownership system.

Edit `component_ownership.json` to map your directories to teams:
```json
{
  "name": "API Gateway",
  "directories": ["services/api-gateway"],
  "owners": {
    "primary": ["alice@company.com"],
    "secondary": ["bob@company.com"]
  }
}
```

### 2. Test Reviewer Assignment

```bash
# Find reviewers for a dependency
python3 find_reviewers.py github.com/gin-gonic/gin
```

## Simulated Vulnerabilities

The project uses Gin v1.8.0, which has the following simulated CVEs:

1. **CVE-2023-29401** (HIGH - CVSS 7.5)
   - Directory traversal vulnerability
   - Fixed in: v1.9.1, v1.10.0

2. **CVE-2023-26125** (MEDIUM - CVSS 5.3)
   - Denial of service through malformed requests
   - Fixed in: v1.8.2, v1.9.0

## Black Duck Output File

### `blackduck_report.json`
Full scan report format with multiple vulnerabilities and summary statistics.

Example structure:
```json
{
  "scan_date": "2024-08-01T19:23:00Z",
  "project_name": "example.com/oldversion",
  "total_vulnerabilities": 2,
  "vulnerabilities": [
    {
      "component": "github.com/gin-gonic/gin",
      "version": "1.8.0",
      "vulnerability_id": "CVE-2023-29401",
      "severity": "HIGH",
      "cvss_score": 7.5,
      "recommended_version": "1.9.1",
      "remediation": "Update to version 1.9.1 or later"
    }
  ]
}
```

## Usage

### Run the Application
```bash
# Install dependencies
go mod download

# Run the server
go run main.go

# Test endpoints
curl http://localhost:8080/ping
curl http://localhost:8080/hello/World
```

### Simulate Black Duck Scan
```bash
# View vulnerability report
python3 simulate_blackduck.py
```

### Fix Vulnerabilities
To fix the vulnerabilities, update Gin to v1.9.1 or later:
```bash
go get github.com/gin-gonic/gin@v1.9.1
go mod tidy
```

## 🔄 Renovate Integration

This project is configured to automatically create PRs for vulnerability fixes:

### How It Works

1. **Black Duck findings** are stored in `blackduck_report.json`
2. **On every run**, Renovate workflow dynamically generates rules from the Black Duck report
3. **Renovate** uses the generated rules and creates **separate PRs** for each CVE found
4. **GitHub Actions** orchestrates the automation (runs hourly)

### Expected PRs

Based on current vulnerabilities, Renovate will create:

- ✅ **PR #1**: `fix(security): update gin to v1.9.1+ to fix CVE-2023-29401 (HIGH)`
  - Fixes directory traversal vulnerability
  - Labels: `security`, `high-priority`, `blackduck`

- ✅ **PR #2**: `fix(security): update gin to v1.9.1+ to fix CVE-2023-26125 (MEDIUM)`
  - Fixes denial of service vulnerability
  - Labels: `security`, `medium-priority`, `blackduck`

### Configuration Files

- `component_ownership.json` - **Component to owner mapping**
- `renovate.json` - Base Renovate configuration
- `blackduck_report.json` - Black Duck vulnerability scan report
- `.github/workflows/renovate.yml` - Renovate automation workflow
- `generate_renovate_rules.py` - Dynamic rule generator from Black Duck findings
- `find_reviewers.py` - Component ownership analyzer (uses `go list`)
- `add_renovate_reviewers.py` - Renovate reviewer config generator

### Test Locally

```bash
# Analyze dependency impact
python3 find_reviewers.py github.com/gin-gonic/gin

# Generate Renovate config with reviewers
python3 add_renovate_reviewers.py

# Run full test
./test_reviewer_assignment.sh
```

## 📚 Documentation

- [RENOVATE_SETUP.md](RENOVATE_SETUP.md) - Complete setup guide
- [renovate.json](renovate.json) - Base Renovate configuration
- [blackduck_report.json](blackduck_report.json) - Black Duck scan report
