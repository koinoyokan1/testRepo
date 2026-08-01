# Black Duck Vulnerability Simulation - Go Project

This repository simulates a Go project with known vulnerabilities detected by Black Duck, specifically targeting the **Gin web framework**.

## Project Overview

- **Go Module**: `example.com/oldversion`
- **Vulnerable Package**: `github.com/gin-gonic/gin v1.8.0` (older version with known CVEs)
- **Application**: Simple REST API with `/ping` and `/hello/:name` endpoints

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

## Integration with Renovate

The simulation script generates Renovate-compatible package rules that can be used to automatically update vulnerable dependencies:

```json
{
  "packageRules": [
    {
      "matchPackageNames": ["github.com/gin-gonic/gin"],
      "allowedVersions": ">=1.9.1"
    }
  ]
}
```
