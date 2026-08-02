# Security Tooling - Black Duck + Renovate Integration

This directory contains all the tooling for automated vulnerability remediation using **Black Duck** security scanning and **Renovate** dependency updates, with intelligent **component-based reviewer assignment** across **multiple ecosystems** (Go + npm/TypeScript).

## 📁 Directory Structure

```
security-tooling/
├── generated/                  # Auto-generated files (DO NOT EDIT)
│   ├── renovate-blackduck-generated.json
│   ├── renovate-reviewers.json
│   └── reviewer_analysis.json
├── mockBlackDuck/
│   └── blackduck_report.json  # Input: Black Duck vulnerability scan report (mock data)
├── component_ownership.json    # Config: Component to owner mapping
├── generate_renovate_rules.py # Script: Generate Renovate rules from Black Duck
├── manage_reviewers.py        # Script: Manage reviewer assignments
├── npm_reviewer_utils.py      # Utility: npm/TypeScript reviewer analysis
├── simulate_blackduck.py      # Script: Simulate Black Duck reports
└── DOCUMENTATION.md           # Complete documentation

Note: GitHub Actions workflows are in the repository root at `../.github/workflows/`:
- `blackduck-integration.yml` - Black Duck scanning workflow
- `renovate.yml` - Renovate PR generation workflow
```

## 🚀 Quick Start

### Running from Repository Root

All scripts expect to be run from the **repository root directory**:

```bash
# Generate Renovate rules from Black Duck findings (code dependencies)
python3 security-tooling/generate_renovate_rules.py

# Scan container images and generate rules
python3 security-tooling/scan_container_images.py

# Analyze all vulnerabilities (Go + npm)
python3 security-tooling/manage_reviewers.py process-report

# Generate reviewer assignments for Renovate
python3 security-tooling/manage_reviewers.py generate-renovate

# Analyze specific packages
python3 security-tooling/manage_reviewers.py analyze --go github.com/gin-gonic/gin
python3 security-tooling/manage_reviewers.py analyze --npm axios
```

## 📋 Key Files

### Configuration Files
- **`component_ownership.json`** - Maps directories to team owners
- **`../renovate.json`** - Base Renovate configuration template (at repository root)
- **`mockBlackDuck/blackduck_report.json`** - Black Duck vulnerability scan results (mock data for testing)
- **`../image_versions.json`** - Container image versions (prebuilt + custom)

### GitHub Workflows (in `../.github/workflows/`)
- **`blackduck-integration.yml`** - Automated Black Duck security scanning
- **`renovate.yml`** - Renovate PR creation and reviewer assignment

### Scripts
- **`generate_renovate_rules.py`** - Creates Renovate package rules from Black Duck findings (code dependencies)
- **`scan_container_images.py`** - Scans container images from Black Duck findings and generates Renovate rules
- **`manage_reviewers.py`** - Unified reviewer management (Go + npm)
- **`npm_reviewer_utils.py`** - npm/TypeScript dependency analysis utilities
- **`simulate_blackduck.py`** - Test tool for Black Duck report processing

### Generated Files (in `generated/`)
- **`renovate-blackduck-generated.json`** - Renovate package rules
- **`renovate-reviewers.json`** - Reviewer assignments
- **`reviewer_analysis.json`** - Detailed analysis results

## 🔄 Workflow

1. **Black Duck Scan** → Generates `mockBlackDuck/blackduck_report.json`
2. **Generate Rules** → `generate_renovate_rules.py` creates Renovate package rules
3. **Find Reviewers** → `manage_reviewers.py` analyzes affected components and assigns reviewers
4. **Renovate PRs** → Automated PRs are created with correct reviewers assigned

## 📚 Documentation

See **[DOCUMENTATION.md](DOCUMENTATION.md)** for complete documentation covering:
- Multi-ecosystem support (Go + npm)
- System architecture and design
- Component ownership system
- Automated reviewer assignment
- Integration with GitHub Actions
- Testing and troubleshooting

## 🎯 Features

- **Multi-Ecosystem Support** - Go (via `go list`) + npm (via import analysis) + Container images
- **Container Image Scanning** - Both prebuilt (nginx, postgres, redis) and custom-built images
- **Nested Module Support** - Handles monorepos with multiple `go.mod` and `package.json` files
- **Automated Reviewer Assignment** - Finds affected components and assigns correct teams
- **Version Constraints** - Stays within same minor version to minimize breaking changes
- **Component Ownership** - Maps directory structure and images to teams
- **Unified Analysis** - Single tool processes entire Black Duck report (code + containers)

## 🔧 Requirements

- **Go 1.20+** (for Go dependency analysis)
- **Python 3.9+**
- **Node.js/npm** (for npm projects)
- **Git**
- **GitHub Actions** (for automation)
