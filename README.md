# Black Duck + Renovate Integration - Multi-Ecosystem

This repository demonstrates automated vulnerability remediation using **Black Duck** security scanning and **Renovate** dependency updates, with intelligent **component-based reviewer assignment** across **multiple ecosystems** (Go + npm/TypeScript).

## Project Overview

**Ecosystems Supported:**
- **Go**: 4 modules (main + 3 nested contrib modules)
- **npm/TypeScript**: 3 packages (2 services + 1 contrib plugin)

**Vulnerable Packages:**
- `github.com/gin-gonic/gin v1.8.0` (Go - CVE-2023-29401, CVE-2023-26125)
- `axios 0.21.1` (npm - CVE-2021-3749)
- `lodash 4.17.19/4.17.20` (npm - CVE-2021-23337, CVE-2020-8203)

**Application Structure:**
- Go services: API Gateway, Auth, Users, Payment, Utilities
- TypeScript services: Web Frontend, Admin Dashboard
- Contrib plugins: Go (plugin-a, plugin-b, shared-lib) + TypeScript (analytics-plugin)

**Automation:**
- Black Duck detects vulnerabilities across both ecosystems
- Renovate creates separate PRs per package with version constraints
- Component owners automatically assigned as reviewers based on file analysis

## ✨ Key Features

1. **Multi-Ecosystem Support** - Go (via `go list`) + npm (via import analysis)
2. **Nested Module Support** - Handles monorepos with multiple `go.mod` and `package.json` files
3. **Automated Reviewer Assignment** - Finds affected components and assigns correct teams
4. **Version Constraints** - Stays within same minor version to minimize breaking changes
5. **Component Ownership** - Maps directory structure to teams (11 components total)
6. **Unified Analysis** - Single tool processes entire Black Duck report (24 unique reviewers)

## 📋 Requirements

- **Go 1.20+** (required for `go list` dependency analysis)
- **Node.js/npm** (optional, for npm projects)
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

**For Go packages:**
```bash
python3 find_reviewers.py github.com/gin-gonic/gin
```

**For npm packages:**
```bash
python3 find_npm_reviewers.py axios
```

**For all vulnerabilities (unified):**
```bash
python3 find_all_reviewers.py
```

Output:
```
📊 Overall Statistics:
  • Vulnerable packages: 3
  • Total unique reviewers: 24

📦 Packages:
  GO: github.com/gin-gonic/gin → 8 components, 18 reviewers
  NPM: axios → 3 components, 6 reviewers
  NPM: lodash → 2 components, 4 reviewers
```

## Simulated Vulnerabilities

### Go Vulnerabilities

**gin-gonic/gin v1.8.0**

1. **CVE-2023-29401** (HIGH - CVSS 7.5)
   - Directory traversal vulnerability
   - Fixed in: v1.9.1, v1.10.0

2. **CVE-2023-26125** (MEDIUM - CVSS 5.3)
   - Denial of service through malformed requests
   - Fixed in: v1.8.2, v1.9.0

### npm Vulnerabilities

**axios 0.21.1**

1. **CVE-2021-3749** (HIGH - CVSS 7.5)
   - Server-Side Request Forgery (SSRF)
   - Fixed in: 0.21.2, 1.6.0

**lodash 4.17.19/4.17.20**

1. **CVE-2021-23337** (HIGH - CVSS 7.2)
   - Command injection vulnerability
   - Fixed in: 4.17.21

2. **CVE-2020-8203** (MEDIUM - CVSS 5.3)
   - Prototype pollution vulnerability
   - Fixed in: 4.17.20, 4.17.21

## Black Duck Output File

### `blackduck_report.json`
Full scan report format with vulnerabilities from multiple ecosystems.

Example structure:
```json
{
  "scan_date": "2024-08-01T19:23:00Z",
  "project_name": "example.com/oldversion",
  "total_vulnerabilities": 5,
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

- `component_ownership.json` - **Component to owner mapping (11 components)**
- `renovate.json` - Base Renovate configuration (enables gomod + npm)
- `blackduck_report.json` - Black Duck vulnerability scan report (5 CVEs)
- `.github/workflows/renovate.yml` - Renovate automation workflow

### Analysis Tools

- `find_reviewers.py` - Go dependency analyzer (uses `go list`)
- `find_npm_reviewers.py` - npm dependency analyzer (uses grep for imports)
- `find_all_reviewers.py` - **Unified multi-ecosystem analyzer**
- `generate_renovate_rules.py` - Dynamic rule generator from Black Duck findings
- `add_renovate_reviewers.py` - Renovate reviewer config generator

### Test Locally

```bash
# Analyze all vulnerabilities (Go + npm)
python3 find_all_reviewers.py

# Generate Renovate rules
python3 generate_renovate_rules.py

# Test specific ecosystem
python3 find_reviewers.py github.com/gin-gonic/gin  # Go
python3 find_npm_reviewers.py axios                  # npm
```

## 📚 Documentation

### Comprehensive Guides

- **[MULTI_ECOSYSTEM_SUMMARY.md](MULTI_ECOSYSTEM_SUMMARY.md)** - Complete multi-ecosystem guide (Go + npm)
- **[TYPESCRIPT_SUPPORT.md](TYPESCRIPT_SUPPORT.md)** - TypeScript/npm integration details
- **[NESTED_MODULES.md](NESTED_MODULES.md)** - Go nested modules support
- **[COMPONENT_OWNERSHIP.md](COMPONENT_OWNERSHIP.md)** - Component ownership system
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams

### Configuration Files

- [renovate.json](renovate.json) - Base Renovate configuration
- [blackduck_report.json](blackduck_report.json) - Black Duck scan report (5 CVEs)
- [component_ownership.json](component_ownership.json) - Component ownership mapping (11 components)
