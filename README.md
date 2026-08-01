# Black Duck Vulnerability Simulation - Go Project

This repository simulates a Go project with known vulnerabilities detected by Black Duck, specifically targeting the **Gin web framework**. It demonstrates automated vulnerability remediation using **Renovate** integration.

## Project Overview

- **Go Module**: `example.com/oldversion`
- **Vulnerable Package**: `github.com/gin-gonic/gin v1.8.0` (older version with known CVEs)
- **Application**: Simple REST API with `/ping` and `/hello/:name` endpoints
- **Automation**: Renovate creates **separate PRs** for each vulnerability fix

## 🚀 Quick Start

### Self-Hosted Renovate Setup

See [RENOVATE_SETUP.md](RENOVATE_SETUP.md) for detailed setup instructions.

## Simulated Vulnerabilities

The project uses Gin v1.8.0, which has the following simulated CVEs:

1. **CVE-2023-29401** (HIGH - CVSS 7.5)
   - Directory traversal vulnerability
   - Fixed in: v1.9.1, v1.10.0

2. **CVE-2023-26125** (MEDIUM - CVSS 5.3)
   - Denial of service through malformed requests
   - Fixed in: v1.8.2, v1.9.0

## Black Duck Output Files

### 1. `blackduck.json`
Simple format with single vulnerability:
```json
{
  "path": "go.mod",
  "package": "github.com/gin-gonic/gin",
  "current": "1.8.0",
  "fixed": "1.9.1",
  "cve": "CVE-2023-29401",
  "severity": "HIGH",
  "description": "...",
  "cvss_score": 7.5
}
```

### 2. `blackduck_report.json`
Full scan report format with multiple vulnerabilities and summary statistics.

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
# View both vulnerability formats
python3 simulate_blackduck.py

# View only simple format
python3 simulate_blackduck.py --simple

# View only full report
python3 simulate_blackduck.py --report
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

1. **Black Duck findings** are stored in JSON files (`blackduck.json`, `blackduck_report.json`)
2. **On every run**, Renovate workflow dynamically generates rules from Black Duck reports
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

- `renovate.json` - Main Renovate configuration
- `.github/workflows/renovate.yml` - Renovate automation workflow
- `.github/workflows/blackduck-integration.yml` - Black Duck integration workflow
- `generate_renovate_rules.py` - Dynamic rule generator

### Generate Renovate Rules

The workflow automatically generates rules on every run. To test locally:

```bash
python3 generate_renovate_rules.py
```

This creates `renovate-blackduck-generated.json` with package rules for each vulnerability found in the Black Duck reports.

## 📚 Documentation

- [RENOVATE_SETUP.md](RENOVATE_SETUP.md) - Complete setup guide
- [renovate.json](renovate.json) - Renovate configuration
- [blackduck.json](blackduck.json) - Simple vulnerability format
- [blackduck_report.json](blackduck_report.json) - Full scan report
