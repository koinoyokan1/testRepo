# Multi-Ecosystem Monorepo with Automated Security Remediation

This repository is a multi-ecosystem monorepo featuring an end-to-end automated security remediation pipeline powered by **Black Duck** vulnerability scanning and **Renovate** dependency management, with intelligent **component-based reviewer assignment**.

## Table of Contents

- [Monorepo Architecture](#monorepo-architecture)
- [Container Image Management](#container-image-management)
- [Black Duck Integration & Mocking](#black-duck-integration--mocking)
- [Dynamic Renovate Workflow](#dynamic-renovate-workflow)
- [Pull Request Lifecycle](#pull-request-lifecycle)
- [Quick Start](#quick-start)
- [Enhanced Features](#enhanced-features)
- [Documentation](#documentation)

---

## Monorepo Architecture

This repository is structured as a **monorepo** containing multiple programming ecosystems, services, and container images:

### Directory Structure

```
.
├── services/                    # Core microservices
│   ├── api-gateway/            # Go service
│   ├── auth/                   # Go service
│   ├── users/                  # Go service
│   ├── payment/                # Go service
│   ├── web-frontend/           # TypeScript/Node.js service
│   └── admin-dashboard/        # TypeScript/Node.js service
├── contrib/                     # Contributed plugins and libraries
│   ├── plugin-a/               # Go plugin
│   ├── plugin-b/               # Go plugin
│   ├── shared-lib/             # Go shared library
│   └── analytics-plugin/       # TypeScript plugin
├── pkg/                         # Shared Go packages
│   ├── database/
│   └── utils/
├── go.mod                       # Root Go module
├── package.json                 # Root npm package (if applicable)
├── image_map.json               # Prebuilt image tracking for Renovate
├── docker-compose.yml           # Container orchestration (tracks custom images)
└── security-tooling/            # Security automation scripts
```

### Supported Ecosystems

- **Go Modules**: Multiple `go.mod` files (main module + 3 nested contrib modules)
  - Main services: API Gateway, Auth, Users, Payment
  - Shared packages: Database utilities, common utilities
  - Contrib plugins: plugin-a, plugin-b, shared-lib

- **NPM/TypeScript Packages**: Multiple `package.json` files
  - Frontend services: Web Frontend, Admin Dashboard
  - Contrib plugins: Analytics Plugin

- **Container Images**: Docker-based deployments
  - Prebuilt third-party images (nginx, postgres, redis, node, golang)
  - Custom internal images built on base images

### Component Ownership

Each component in the monorepo has **distinct owners** defined in `security-tooling/component_ownership.json`. This ownership configuration maps directories to teams and is used to:

- Automatically assign reviewers to security PRs based on affected components
- Ensure the correct developers are notified when their code dependencies have vulnerabilities
- Track responsibility across 11 distinct components with 24 unique reviewers

Example ownership definition:
```json
{
  "name": "API Gateway",
  "directories": ["services/api-gateway"],
  "owners": {
    "primary": ["alice@company.com"],
    "secondary": ["bob@company.com", "charlie@company.com"]
  }
}
```

---

## Container Image Management

The repository manages container images across two distinct categories, each tracked and updated differently:

### 1. Prebuilt Images (`image_map.json`)

**Prebuilt images** are third-party container images consumed directly from public registries (e.g., Docker Hub, Quay.io). These are tracked in `image_map.json`.

**Examples:**
- `nginx:1.21.0` - Web server and reverse proxy
- `postgres:13.2` - Primary database
- `redis:6.0.9` - Cache and session store
- `node:16.14.0-alpine` - Base image for Node.js services
- `golang:1.19.0-alpine` - Base image for Go services

**Structure:**
```json
{
  "nginx": {
    "origin_image": "nginx:1.21.0",
    "owner": "platform-team@company.com",
    "purpose": "Web server and reverse proxy"
  },
  "postgres": {
    "origin_image": "postgres:13.2",
    "owner": "database-team@company.com",
    "purpose": "Primary database"
  }
}
```

**How it Works:**
- Renovate uses a **regex manager** configured in `renovate.json` to parse `image_map.json`
- The regex extracts image names and versions from the `origin_image` field
- Renovate automatically creates PRs when new versions are available in the upstream registry
- **This mechanism is independent of Black Duck** and uses Renovate's native Docker datasource

### 2. Custom Images (`docker-compose.yml` and Dockerfiles)

**Custom images** are internally built container images that extend base images (like `golang:alpine` or `node:alpine`). These are tracked in source files: `docker-compose.yml` and their corresponding Dockerfiles.

**Examples:**
- `ghcr.io/company/api-gateway:v2.3.1` (based on `golang:1.19.0-alpine`)
- `ghcr.io/company/web-frontend:v3.2.0` (based on `node:16.14.0-alpine`)

**Structure in docker-compose.yml:**
```yaml
services:
  api-gateway:
    image: ghcr.io/company/api-gateway:v2.3.1
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    # Base: golang:1.19.0-alpine
    # Owner: alice@company.com
    # CVE: CVE-2022-41716 (HIGH) - Rebuild with golang:1.21.5-alpine
```

**Important:**
- Custom image metadata (owner, base image) is extracted from comments in `docker-compose.yml`
- When a base image vulnerability is detected (e.g., CVE in `golang:1.19.0-alpine`), Black Duck flags the custom image that inherits it
- The remediation requires updating the `FROM` statement in the Dockerfile and rebuilding the custom image

---

## Black Duck Integration & Mocking

Since this is a demonstration repository, **Black Duck scans are simulated** using `security-tooling/simulate_blackduck.py`. In a production environment, this would be replaced by an actual Black Duck API integration.

### How Black Duck Scanning Works

1. **Scan Execution**: Black Duck (or the simulation script) scans all dependency manifests:
   - `go.mod` files for Go dependencies
   - `package.json` files for npm dependencies
   - Container images referenced in `image_map.json` and `docker-compose.yml`

2. **Vulnerability Detection**: The scanner identifies known CVEs in:
   - Direct and transitive dependencies (Go packages, npm packages)
   - Container base images (both prebuilt and custom images)
   - Inherited vulnerabilities from base images in custom builds

3. **Report Generation**: Scan results are written to `security-tooling/blackduck_report.json`

### Black Duck Report Format

The report is a structured JSON file serving as the **single source of truth** for all vulnerabilities:

```json
{
  "scan_date": "2024-08-01T19:23:00Z",
  "project_name": "example.com/oldversion",
  "scan_status": "COMPLETED",
  "total_vulnerabilities": 12,
  "vulnerabilities": [
    {
      "component": "github.com/gin-gonic/gin",
      "version": "1.8.0",
      "vulnerability_id": "CVE-2023-29401",
      "severity": "HIGH",
      "cvss_score": 7.5,
      "description": "Directory traversal vulnerability...",
      "published_date": "2023-06-08",
      "fixed_versions": ["1.9.1", "1.10.0"],
      "recommended_version": "1.9.1",
      "file_path": "go.mod",
      "remediation": "Update github.com/gin-gonic/gin to version 1.9.1 or later",
      "ecosystem": "go"
    },
    {
      "component": "axios",
      "version": "0.21.1",
      "vulnerability_id": "CVE-2021-3749",
      "severity": "HIGH",
      "cvss_score": 7.5,
      "ecosystem": "npm",
      "recommended_version": "1.6.0",
      ...
    },
    {
      "component": "nginx",
      "version": "1.21.0",
      "vulnerability_id": "CVE-2021-23017",
      "severity": "HIGH",
      "cvss_score": 8.1,
      "ecosystem": "container",
      "image_type": "prebuilt",
      "recommended_version": "1.25.3",
      ...
    },
    {
      "component": "ghcr.io/company/api-gateway",
      "version": "v2.3.1",
      "vulnerability_id": "CVE-2022-41716",
      "severity": "HIGH",
      "ecosystem": "container",
      "image_type": "custom",
      "base_image": "golang:1.19.0-alpine",
      "recommended_version": "v2.4.1",
      ...
    }
  ],
  "summary": {
    "critical": 0,
    "high": 9,
    "medium": 3,
    "low": 0
  }
}
```

### Key Fields

- **`ecosystem`**: The package ecosystem (`go`, `npm`, `container`)
- **`recommended_version`**: The minimum safe version that fixes the vulnerability
- **`image_type`**: For containers, distinguishes `prebuilt` vs `custom` images
- **`base_image`**: For custom images, identifies the base image causing the vulnerability

### Running the Simulation

```bash
python3 security-tooling/simulate_blackduck.py
```

This generates `security-tooling/blackduck_report.json` with 12 simulated vulnerabilities across Go, npm, and container ecosystems.

---

## Dynamic Renovate Workflow

The core automation is orchestrated by `.github/workflows/renovate.yml`, which runs **hourly** or on-demand. This workflow dynamically generates Renovate configuration from the Black Duck report, ensuring that **only vulnerable packages** are updated.

### Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Black Duck Report (blackduck_report.json)                   │
│     - Contains all vulnerabilities across ecosystems            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Generate Renovate Rules                                     │
│     ├─ generate_package_rules.py (Go/NPM packages)              │
│     └─ generate_container_image_rules.py (Docker images)        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Assign Reviewers                                            │
│     └─ manage_reviewers.py (component ownership mapping)        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Merge Configurations                                        │
│     └─ renovate-merged.json (final config)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Renovate Execution                                          │
│     └─ Creates separate PRs for each vulnerability              │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Breakdown

#### Step 1: Rule Generation for Packages (Go/NPM)

**Script:** `security-tooling/generate_package_rules.py`

**Input:** `blackduck_report.json`

**Processing:**
- Filters vulnerabilities with `ecosystem: "go"` or `ecosystem: "npm"`
- For each vulnerability, generates a Renovate `packageRule`:
  - `matchDatasources`: `["go"]` or `["npm"]`
  - `matchPackageNames`: The package name (e.g., `["github.com/gin-gonic/gin"]`)
  - `allowedVersions`: Version constraint (e.g., `">=1.9.1 <1.10.0"`)
    - Constrains updates to the same minor version to minimize breaking changes
  - `prTitle`, `prBodyNotes`: CVE details, severity, CVSS score
  - `labels`: `["security", "high-priority", "blackduck", "cve-2023-29401", "go"]`

**Output:** `security-tooling/generated/renovate-blackduck-generated.json`

**Example Generated Rule:**
```json
{
  "description": "Black Duck - CVE-2023-29401 (HIGH) - go",
  "matchDatasources": ["go"],
  "matchPackageNames": ["github.com/gin-gonic/gin"],
  "allowedVersions": ">=1.9.1 <1.10.0",
  "prTitle": "fix(security): update gin to v1.9.1 to fix CVE-2023-29401 (HIGH)",
  "prBodyNotes": [
    "### 🔒 Security Update - Black Duck Finding (GO)",
    "",
    "**Vulnerability**: CVE-2023-29401",
    "**Severity**: HIGH (CVSS 7.5)",
    "**Current Version**: 1.8.0",
    "**Fixed Version**: 1.9.1 (minimum safe version)",
    ...
  ],
  "labels": ["security", "high-priority", "blackduck", "cve-2023-29401", "go"]
}
```

##### Step 2: Rule Generation for Container Images

**Script:** `security-tooling/generate_container_image_rules.py`

**Input:**
- `blackduck_report.json`
- `docker-compose.yml`
- `image_map.json`

**Processing:**
- Filters vulnerabilities with `ecosystem: "container"`
- **Prebuilt images**: Tracked in `image_map.json`, updated by Renovate's docker datasource (independent of Black Duck)
- **Custom images only**: Matches vulnerable custom images from Black Duck against `docker-compose.yml`
- For each vulnerable custom image, generates a Renovate rule:
  - `matchFileNames`: Dockerfile path and `docker-compose.yml`
  - `prTitle`, `prBodyNotes`: CVE details, base image update instructions
  - `reviewers`: Extracted from the `# Owner:` comment in `docker-compose.yml`
  - PR notes include base image rebuild instructions with specific file paths

**Output:** `security-tooling/generated/renovate-container-images.json`

**Example Generated Rule (Custom Image only):**

> **Note:** Prebuilt images (nginx, postgres, redis) are tracked in `image_map.json` and updated by Renovate's docker datasource independently. The `generate_container_image_rules.py` script only generates rules for custom images.
```json
{
  "description": "Black Duck - api-gateway CVE-2022-41716 (HIGH) - Custom Image",
  "matchFileNames": ["services/api-gateway/Dockerfile", "docker-compose.yml"],
  "enabled": true,
  "prTitle": "fix(security): rebuild api-gateway to fix CVE-2022-41716 in base image",
  "prBodyNotes": [
    "### 🔒 Security Update - Custom Container Image",
    "",
    "**Image**: ghcr.io/company/api-gateway:v2.3.1",
    "**Base Image**: golang:1.19.0-alpine",
    "**Recommended Base**: Update to golang:1.21.5-alpine",
    "**Dockerfile**: services/api-gateway/Dockerfile",
    "",
    "**Remediation Steps**:",
    "1. Update the FROM statement in `services/api-gateway/Dockerfile`",
    "2. Change base image to: `golang:1.21.5-alpine`",
    "3. Rebuild the container image",
    "4. Update the image reference in `docker-compose.yml`"
  ],
  "labels": ["security", "high-priority", "blackduck", "container-image", "custom-image"],
  "reviewers": ["alice@company.com"]
}
```

#### Step 2a: Rule Generation for OS-Level Packages in Dockerfiles

**Script:** `security-tooling/generate_dockerfile_rules.py`

**Input:**
- `blackduck_report.json`

**Processing:**
- Filters vulnerabilities with OS-level ecosystems (`alpine`, `debian`, `rhel`, `ubuntu`, etc.)
- For each OS-level package vulnerability:
  - Generates a **regex manager** rule to detect the package in Dockerfile `RUN` commands
  - Creates a **package rule** with version constraints
  - Matches specific Dockerfiles based on the `file_path` from Black Duck
  - Supports multiple package managers: `apk` (Alpine), `apt` (Debian/Ubuntu), `yum` (RHEL/CentOS)

**Output:** `security-tooling/generated/renovate-dockerfile-regex.json`

**Example Generated Regex Manager:**
```json
{
  "description": "Black Duck - CVE-2023-0464 (HIGH) - alpine package in Dockerfile",
  "fileMatch": ["^services\\/api-gateway\\/Dockerfile$"],
  "matchStrings": [
    "RUN\\s+apk\\s+(?:add|install)\\s+.*?openssl=(?<currentValue>[^\\s]+)"
  ],
  "depNameTemplate": "openssl",
  "datasourceTemplate": "repology",
  "versioningTemplate": "loose",
  "packageNameTemplate": "alpine/openssl",
  "enabled": true
}
```

**Example Generated Package Rule:**
```json
{
  "description": "Black Duck - CVE-2023-0464 (HIGH) - openssl in services/api-gateway/Dockerfile",
  "matchDatasources": ["repology"],
  "matchPackageNames": ["alpine/openssl"],
  "matchFileNames": ["services/api-gateway/Dockerfile"],
  "allowedVersions": ">=3.0.9-r0",
  "prTitle": "fix(security): update openssl to 3.0.9-r0 in services/api-gateway/Dockerfile to fix CVE-2023-0464 (HIGH)",
  "prBodyNotes": [
    "### 🔒 Security Update - OS-Level Package (ALPINE)",
    "**Vulnerability**: CVE-2023-0464",
    "**Severity**: HIGH (CVSS 7.5)",
    "**Package Manager**: apk",
    "**Package**: openssl",
    "**Current Version**: 3.0.7-r0",
    "**Fixed Version**: 3.0.9-r0 (minimum safe version)",
    "**Dockerfile**: services/api-gateway/Dockerfile",
    ...
  ],
  "labels": ["security", "high-priority", "blackduck", "dockerfile", "alpine", "cve-2023-0464"]
}
```

**How It Works:**
1. Black Duck reports `ecosystem: "alpine"` and `file_path: "services/api-gateway/Dockerfile"`
2. The script generates a regex to find `openssl=3.0.7-r0` in that specific Dockerfile
3. Renovate uses the regex manager to detect the current version
4. When a newer version is available (e.g., `3.0.9-r0`), Renovate creates a PR to update the Dockerfile
5. The PR changes: `RUN apk --no-cache add openssl=3.0.7-r0` → `RUN apk --no-cache add openssl=3.0.9-r0`

#### Step 2b: GitHub Issue Creation for Unfixable Vulnerabilities

**Script:** `security-tooling/create_github_issues.py`

**Input:** `blackduck_report.json`

**Processing:**
- Identifies vulnerabilities that lack both `recommended_version` and `fixed_versions`
- For each unfixable vulnerability:
  - Generates a detailed GitHub Issue body with CVE details, severity, and remediation guidance
  - Creates a shell script with `gh issue create` commands
  - Stores issue metadata in JSON format for the workflow

**Output:**
- `security-tooling/generated/github-issues.sh` - Shell script to create issues
- `security-tooling/generated/unfixable-vulnerabilities.json` - Issue metadata
- `security-tooling/generated/issue-body-{n}.md` - Issue body markdown files

**Example GitHub Issue:**
```markdown
## 🚨 Unfixable Vulnerability Detected

**This vulnerability currently has NO available fix.** This issue has been automatically created by the Black Duck security scanner.

### Vulnerability Details

- **CVE ID**: CVE-2023-UNFIXED
- **Severity**: CRITICAL
- **CVSS Score**: 9.8
- **Published**: 2023-06-01

### Affected Component

- **Package**: `zlib`
- **Current Version**: `1.2.11`
- **Ecosystem**: alpine
- **File**: `services/api-gateway/Dockerfile`

### Description

Critical memory corruption vulnerability in zlib compression library with no available fix

### Remediation Status

⚠️ **No fix currently available**

No fix currently available. Monitor vendor announcements for updates.

### Recommended Actions

1. **Monitor** vendor security announcements for updates
2. **Review** if this component is critical to your application
3. **Consider** alternative packages or workarounds
4. **Assess** the risk and potential impact on your systems
5. **Implement** additional security controls or network-level mitigations if possible
```

**GitHub Issue Labels:**
- `security` - Security vulnerability
- `unfixable` - No fix available
- `blackduck` - Source of finding
- `{severity}-priority` - Priority level (critical-priority, high-priority, etc.)
- `{ecosystem}` - Package ecosystem (go, npm, alpine, etc.)

**Workflow Integration:**
The workflow automatically runs the generated shell script using GitHub CLI (`gh issue create`) to open issues for each unfixable vulnerability.

#### Step 3: Reviewer Assignment

**Script:** `security-tooling/manage_reviewers.py generate-renovate`

**Input:**
- `blackduck_report.json`
- `security-tooling/component_ownership.json`

**Processing:**
- For **Go packages**: Uses `go list -json -m all` to find all modules importing the vulnerable package
  - Maps imported files to components using the ownership configuration
  - Collects primary and secondary owners from all affected components
- For **npm packages**: Analyzes `import` statements in TypeScript/JavaScript files
  - Maps files importing the package to components
  - Collects owners from affected components
- For **container images**: Reviewers are extracted from `# Owner:` comments in `docker-compose.yml`

**Output:** `security-tooling/generated/renovate-reviewers.json`

**Example:**
```json
{
  "packageRules": [
    {
      "description": "Auto-assign reviewers for github.com/gin-gonic/gin (affects 8 components)",
      "matchDatasources": ["go"],
      "matchPackageNames": ["github.com/gin-gonic/gin"],
      "reviewers": [
        "alice@company.com",
        "bob@company.com",
        "charlie@company.com",
        "david@company.com",
        "architects@company.com"
      ],
      "addLabels": [
        "component:api-gateway",
        "component:authentication-service",
        "component:contrib-plugin-a"
      ]
    }
  ]
}
```

#### Step 4: Configuration Merging

**Location:** `.github/workflows/renovate.yml` (inline Python script)

**Process:**
1. Creates a **base merged config** with:
   - Global Renovate settings (no rate limits, semantic commits, etc.)
   - A single rule: **Disable all updates by default** (`enabled: false` for all packages)

2. Reads generated configurations:
   - `renovate-blackduck-generated.json` (package rules)
   - `renovate-container-images.json` (container image rules)
   - `renovate-reviewers.json` (reviewer assignments)

3. Merges package rules with reviewer assignments:
   - For each package rule, finds the corresponding reviewer rule by package name
   - Merges `reviewers` and `addLabels` fields into the package rule

4. Appends container image rules (already have reviewers from Step 2)

5. Writes final configuration to **`renovate-merged.json`**

**Key Insight:** The base config disables **all** updates by default. Only packages/images with vulnerabilities (from the Black Duck report) are explicitly enabled via the generated rules. This ensures Renovate only creates PRs for security fixes, not general dependency updates.

#### Step 5: Renovate Execution

**Tool:** `renovatebot/github-action@v40.3.2`

**Configuration File:** `renovate-merged.json` (dynamically generated)

**Behavior:**
- Scans dependency manifests (`go.mod`, `package.json`, `docker-compose.yml`, Dockerfiles, `image_map.json`)
- Matches packages against the merged `packageRules`
- For each enabled package rule:
  - Checks if a newer version is available that satisfies `allowedVersions`
  - If yes, creates a PR with the specified title, body, labels, and reviewers
- Creates **separate PRs** for each vulnerability (not grouped)

---

## Pull Request Lifecycle

When Renovate executes with the merged configuration, it creates **individual PRs** for each vulnerability. Each PR is highly detailed and context-aware.

### PR Structure

#### 1. PR Title
Format: `fix(security): update <package> to <version> to fix <CVE> (<severity>)`

**Examples:**
- `fix(security): update gin to v1.9.1 to fix CVE-2023-29401 (HIGH)`
- `fix(security): update axios to v1.6.0 to fix CVE-2021-3749 (HIGH)`
- `fix(security): update nginx to 1.25.3 to fix CVE-2021-23017`

#### 2. PR Description

**For Go/NPM Packages:**
```markdown
### 🔒 Security Update - Black Duck Finding (GO)

**Vulnerability**: CVE-2023-29401
**Severity**: HIGH (CVSS 7.5)
**Ecosystem**: go
**Current Version**: 1.8.0
**Fixed Version**: 1.9.1 (minimum safe version)
**Version Constraint**: >=1.9.1 <1.10.0

**Description**: Directory traversal vulnerability in gin-gonic/gin allows attackers to access files outside the intended directory

**Remediation**: Update github.com/gin-gonic/gin to version 1.9.1. Constrained to same minor version to minimize breaking changes.

This PR was created based on Black Duck security scan findings.
```

**For Container Images (Prebuilt):**
```markdown
### 🔒 Security Update - Container Image (PREBUILT)

**Image**: nginx:1.21.0
**Current Version**: 1.21.0
**Recommended Version**: 1.25.3

**Vulnerabilities Fixed**:

#### CVE-2021-23017 (HIGH)
- **CVSS Score**: 8.1
- **Description**: Off-by-one error in nginx resolver allows attackers to cause a denial of service or execute arbitrary code

**Remediation**: Update nginx to version 1.21.1 or later, preferably 1.25.3 for latest security patches

---

**Files to Update**: Dockerfile and `docker-compose.yml`

This PR was created based on Black Duck container image scan findings.
```

**For Container Images (Custom):**
```markdown
### 🔒 Security Update - Container Image (CUSTOM)

**Image**: ghcr.io/company/api-gateway:v2.3.1
**Current Version**: v2.3.1
**Recommended Version**: v2.4.1
**Base Image**: golang:1.19.0-alpine
**Dockerfile**: services/api-gateway/Dockerfile

**Vulnerabilities Fixed**:

#### CVE-2022-41716 (HIGH)
- **CVSS Score**: 7.5
- **Description**: Inherited from base image golang:1.19.0-alpine - Unsanitized NUL in environment variables

**Remediation**: Rebuild with updated golang base image (1.21.5-alpine) and update to v2.4.1

---

**Files to Update**: Dockerfile and `docker-compose.yml`
**Action Required**: Update base image in Dockerfile and rebuild container image

This PR was created based on Black Duck container image scan findings.
```

#### 3. PR Labels

Every PR includes contextual labels:
- `security` - Marks as a security fix
- `<severity>-priority` - Priority level (`high-priority`, `medium-priority`, etc.)
- `blackduck` - Source of the finding
- `<cve-id>` - Specific CVE identifier (e.g., `cve-2023-29401`)
- `<ecosystem>` - Package ecosystem (`go`, `npm`, `container`)
- `component:<name>` - Affected components (e.g., `component:api-gateway`)

#### 4. PR Reviewers

Reviewers are **automatically assigned** based on:
- **For Go/NPM packages**: Component ownership analysis
  - The script identifies which components import/use the vulnerable package
  - Primary and secondary owners of all affected components are assigned
  - Example: If `gin` is used by 8 components, reviewers from all 8 teams are assigned
- **For container images**: Owner extracted from `# Owner:` comments in `docker-compose.yml` and `image_map.json`
  - Prebuilt images: Team responsible for the infrastructure (e.g., `platform-team@company.com`) from `image_map.json`
  - Custom images: Service owner (e.g., `alice@company.com` for API Gateway) from `docker-compose.yml` comments

#### 5. Version Constraints

Updates are constrained to the **same minor version** to minimize breaking changes:
- If the recommended fix is `1.9.1`, the constraint is `>=1.9.1 <1.10.0`
- This prevents automatic major/minor version jumps that could introduce breaking changes
- Developers can manually upgrade to newer majors after review

### PR Workflow

1. **Automated Creation**: Renovate creates the PR with all metadata
2. **Reviewer Notification**: GitHub notifies assigned reviewers
3. **Code Review**: Reviewers examine the change and test in staging
4. **Approval & Merge**: Once approved, the PR is merged
5. **CI/CD Pipeline**: Automated builds/deployments pick up the fix
6. **Verification**: Security team verifies the vulnerability is resolved in the next Black Duck scan

---

## Quick Start

### Requirements

- **Go 1.20+** (for `go list` dependency analysis)
- **Node.js/npm** (for npm package analysis)
- **Python 3.9+** (for automation scripts)
- **GitHub Actions** (for CI/CD workflows)

### 1. Simulate a Black Duck Scan

Generate the vulnerability report:
```bash
python3 security-tooling/simulate_blackduck.py
```

This creates `security-tooling/blackduck_report.json` with 12 simulated vulnerabilities.

### 2. Generate Renovate Rules

Run the automation scripts to generate Renovate configuration:

```bash
# Generate package rules (Go/NPM)
python3 security-tooling/generate_package_rules.py

# Generate container image rules
python3 security-tooling/generate_container_image_rules.py

# Generate Dockerfile OS-level package rules
python3 security-tooling/generate_dockerfile_rules.py

# NEW: Detect and patch base image vulnerabilities
python3 security-tooling/detect_base_image_vulns.py
python3 security-tooling/patch_base_image_dockerfiles.py
python3 security-tooling/generate_upgrade_regex.py

# Generate GitHub Issues for unfixable vulnerabilities
python3 security-tooling/create_github_issues.py

# Generate reviewer assignments
python3 security-tooling/manage_reviewers.py generate-renovate
```

**Outputs:**
- `security-tooling/generated/renovate-blackduck-generated.json` - Go/NPM package rules
- `security-tooling/generated/renovate-container-images.json` - Container image rules
- `security-tooling/generated/renovate-dockerfile-regex.json` - Dockerfile OS-level package rules (explicit installs)
- `security-tooling/generated/renovate-base-image-upgrades.json` - ✨ **NEW**: Base image upgrade rules
- `security-tooling/generated/vuln-categorization.json` - ✨ **NEW**: Vulnerability categorization
- `security-tooling/generated/dockerfile-patches.json` - ✨ **NEW**: Dockerfile patch metadata
- `security-tooling/generated/github-issues.sh` - Script to create GitHub Issues
- `security-tooling/generated/unfixable-vulnerabilities.json` - Unfixable vulnerability metadata
- `security-tooling/generated/renovate-reviewers.json` - Reviewer assignments

### 3. Test Reviewer Assignment

Analyze which components are affected by specific vulnerabilities:

```bash
# For Go packages
python3 security-tooling/manage_reviewers.py analyze --go github.com/gin-gonic/gin

# For npm packages
python3 security-tooling/manage_reviewers.py analyze --npm axios

# For all vulnerabilities
python3 security-tooling/manage_reviewers.py process-report
```

**Sample Output:**
```
📊 Overall Statistics:
  • Vulnerable packages: 3
  • Total unique reviewers: 24

📦 Packages:
  GO: github.com/gin-gonic/gin → 8 components, 18 reviewers
  NPM: axios → 3 components, 6 reviewers
  NPM: lodash → 2 components, 4 reviewers
```

### 4. Trigger Renovate (Locally or via GitHub Actions)

The Renovate workflow runs automatically every hour, or you can trigger it manually via **GitHub Actions** → **Workflow Dispatch**.

**What happens:**
- The workflow executes all generation scripts
- Merges configurations into `renovate-merged.json`
- Renovate scans manifests and creates PRs for vulnerable packages

### 5. Review Generated PRs

Renovate will create individual PRs for each vulnerability:
- Go package updates in `go.mod`
- npm package updates in `package.json`
- Prebuilt container image updates in `image_map.json`
- Custom container image base updates in Dockerfiles
- OS-level package updates in Dockerfiles

Each PR includes:
- CVE details and CVSS scores
- Recommended version from Black Duck
- Automatically assigned reviewers based on affected components

---

## Documentation

### Security Tooling Documentation

- **[security-tooling/README.md](security-tooling/README.md)** - Quick start guide for security automation tools
- **[security-tooling/DOCUMENTATION.md](security-tooling/DOCUMENTATION.md)** - Comprehensive technical documentation:
  - Multi-ecosystem support (Go, npm, Docker)
  - System architecture and design principles
  - Component ownership system
  - Nested module support
  - Automated reviewer assignment algorithms
- **[security-tooling/BASE_IMAGE_PATCHING.md](security-tooling/BASE_IMAGE_PATCHING.md)** - ✨ **NEW**: Base image patching guide
- **[security-tooling/QUICK_START.md](security-tooling/QUICK_START.md)** - ✨ **NEW**: Quick reference for base image patching
- **[security-tooling/ARCHITECTURE.md](security-tooling/ARCHITECTURE.md)** - ✨ **NEW**: Complete system architecture
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - ✨ **NEW**: Implementation overview

### Configuration Files

- **[renovate.json](renovate.json)** - Base Renovate configuration (template for merging)
- **[docker-compose.yml](docker-compose.yml)** - Container orchestration and custom image definitions
- **[image_map.json](image_map.json)** - Origin image mapping for Renovate regex manager
- **[security-tooling/blackduck_report.json](security-tooling/blackduck_report.json)** - Black Duck vulnerability report (12 CVEs)
- **[security-tooling/component_ownership.json](security-tooling/component_ownership.json)** - Component-to-team mapping (11 components, 24 reviewers)

### Workflow Files

- **[.github/workflows/renovate.yml](.github/workflows/renovate.yml)** - Main Renovate automation workflow
- **[.github/workflows/blackduck-integration.yml](.github/workflows/blackduck-integration.yml)** - Black Duck scan integration

---

## Simulated Vulnerabilities

The current Black Duck report (`security-tooling/blackduck_report.json`) contains **16 vulnerabilities** across **5 categories**:

### Go Packages (2 CVEs)
- **github.com/gin-gonic/gin v1.8.0**
  - CVE-2023-29401 (HIGH, CVSS 7.5) - Directory traversal → Fix: v1.9.1
  - CVE-2023-26125 (MEDIUM, CVSS 5.3) - Denial of service → Fix: v1.9.1

### NPM Packages (3 CVEs)
- **axios 0.21.1**
  - CVE-2021-3749 (HIGH, CVSS 7.5) - SSRF vulnerability → Fix: v1.6.0
- **lodash 4.17.19/4.17.20**
  - CVE-2021-23337 (HIGH, CVSS 7.2) - Command injection → Fix: v4.17.21
  - CVE-2020-8203 (MEDIUM, CVSS 5.3) - Prototype pollution → Fix: v4.17.21

### Container Images (7 CVEs)

**Prebuilt Images:**
- **nginx 1.21.0** - CVE-2021-23017 (HIGH, CVSS 8.1) → Fix: v1.25.3
- **postgres 13.2** - CVE-2021-32027 (HIGH, CVSS 8.8) → Fix: v15.5
- **redis 6.0.9** - CVE-2021-32672 (MEDIUM, CVSS 6.5) → Fix: v7.2.3
- **node 16.14.0-alpine** - CVE-2022-21824 (HIGH, CVSS 8.2) → Fix: v20.10.0-alpine
- **golang 1.19.0-alpine** - CVE-2022-41716 (HIGH, CVSS 7.5) → Fix: v1.21.5-alpine

**Custom Images (inherit base image vulnerabilities):**
- **ghcr.io/company/api-gateway v2.3.1** - Inherits golang CVE → Fix: v2.4.1 + rebuild
- **ghcr.io/company/web-frontend v3.2.0** - Inherits node CVE → Fix: v3.3.2 + rebuild

### OS-Level Packages in Dockerfiles (4 CVEs) ✨ **NEW**
- **openssl 3.0.7-r0** (Alpine/apk) in `services/api-gateway/Dockerfile` - CVE-2023-0464 (HIGH, CVSS 7.5) → Fix: 3.0.9-r0
- **curl 7.88.0-r0** (Alpine/apk) in `services/api-gateway/Dockerfile` - CVE-2023-28321 (MEDIUM, CVSS 5.9) → Fix: 8.1.0-r0
- **libssl3 3.0.8-r0** (Alpine/apk) in `services/web-frontend/Dockerfile` - CVE-2023-2650 (MEDIUM, CVSS 6.5) → Fix: 3.0.9-r1
- **libcrypto3 3.0.8-r0** (Alpine/apk) in `services/web-frontend/Dockerfile` - CVE-2023-2650 (MEDIUM, CVSS 6.5) → Fix: 3.0.9-r1

### Unfixable Vulnerabilities (2 CVEs) ✨ **NEW**
These vulnerabilities have **no available fix** and will trigger GitHub Issue creation:
- **zlib 1.2.11** (Alpine) - CVE-2023-UNFIXED (CRITICAL, CVSS 9.8) → **No fix available**
- **github.com/vulnerable/package 1.0.0** (Go) - CVE-2023-NOFIX (HIGH, CVSS 8.1) → **No fix available**

---

## Complete Vulnerability Coverage

This system provides **100% automated remediation** across all vulnerability types:

| Vulnerability Type | Location | Handler | Status |
|--------------------|----------|---------|--------|
| **Go/npm packages** | `go.mod`, `package.json` | `generate_package_rules.py` | ✅ Automated PR |
| **Container base images** | `image_map.json`, `docker-compose.yml` | `generate_container_image_rules.py` | ✅ Automated PR |
| **OS packages (explicit install)** | `RUN apk/apt/yum add` in Dockerfile | `generate_dockerfile_rules.py` | ✅ Automated PR |
| **OS packages (base image)** | Base image layers | `detect_base_image_vulns.py`<br>`patch_base_image_dockerfiles.py`<br>`generate_upgrade_regex.py` | ✅ **NEW** - Auto-patch + PR |
| **Unfixable vulnerabilities** | Any ecosystem | `create_github_issues.py` | ✅ GitHub Issue |

**Result:** Every vulnerability detected by Black Duck is automatically remediated through either:
- Renovate PR (fixable vulnerabilities)
- Dockerfile modification + Renovate PR (base image OS packages)
- GitHub Issue (unfixable vulnerabilities)

### PR Title Format

All Renovate PRs include a **vulnerability type prefix** for easy identification:

| Vulnerability Type | PR Title Format | Example |
|--------------------|-----------------|---------|
| **Go packages** | `Go package upgrade: ...` | `Go package upgrade: update gin to v1.9.1 to fix CVE-2023-29401 (HIGH)` |
| **npm packages** | `npm package upgrade: ...` | `npm package upgrade: update axios to v1.6.0 to fix CVE-2021-3749 (HIGH)` |
| **Container base images (prebuilt)** | `Container base image upgrade: ...` | `Container base image upgrade: nginx to 1.25.3` |
| **Container base images (custom)** | `Custom container image upgrade: ...` | `Custom container image upgrade: rebuild api-gateway to fix CVE-2022-41716` |
| **OS packages (explicit)** | `OS package upgrade (explicit): ...` | `OS package upgrade (explicit): update openssl to 3.0.9-r0 in Dockerfile` |
| **OS packages (base image)** | `OS package upgrade (base image): ...` | `OS package upgrade (base image): upgrade libssl3 to 3.0.9-r1 to fix CVE-2023-2650` |

**Benefits:**
- Instantly recognize vulnerability type from PR list
- Easier prioritization and routing to subject matter experts
- Clear audit trail for security remediation

---

## Architecture Highlights

### Why This Approach?

1. **Single Source of Truth**: Black Duck report drives all automation
2. **Zero Hardcoding**: No manual package rules in `renovate.json`
3. **Intelligent Routing**: Reviewers auto-assigned based on actual code usage
4. **Minimal Disruption**: Version constraints prevent breaking changes
5. **Full Coverage**: Supports Go, npm, containers, and OS packages (explicit + base image)
6. **Scalable**: Adding new components/packages requires no code changes
7. **Self-Healing**: Dockerfile patches kept current by Renovate

### Key Design Decisions

- **Separate PRs per CVE**: Easier to review, test, and rollback individual fixes
- **Component Ownership**: Distributed responsibility across teams
- **Dynamic Configuration**: Renovate config regenerated on every run
- **Regex Manager for image_map.json**: Independent Docker image updates
- **Container Image Tracking**: Prebuilt images in `image_map.json`, custom images in source files
- **OS-Level Package Support (Explicit)**: Regex managers detect and update packages in Dockerfile RUN commands
- **OS-Level Package Support (Base Image)**: ✨ **NEW** - Automatic Dockerfile patching for base image vulnerabilities
- **Unfixable Vulnerability Handling**: GitHub Issues created automatically when no fix is available
- **Multi-Level Filtering**: Scripts automatically route vulnerabilities to the appropriate handler (Renovate PR vs GitHub Issue vs Dockerfile Patch)

---

## ✨ Enhanced Features

### 1. OS-Level Package Remediation in Dockerfiles (Explicit Installs)

The pipeline supports vulnerabilities found in OS-level packages (e.g., `apk`, `apt`, `yum`) **explicitly installed** via `RUN` commands in Dockerfiles.

**How It Works:**

1. **Black Duck Detection**: Black Duck scans Dockerfiles and reports vulnerabilities in OS-level packages with:
   - `ecosystem`: `alpine`, `debian`, `rhel`, `ubuntu`, etc.
   - `file_path`: Path to the specific Dockerfile
   - `package_manager`: Package manager used (`apk`, `apt`, `yum`)

2. **Rule Generation**: `generate_dockerfile_rules.py` creates:
   - **Regex Managers**: Pattern matching rules to detect package versions in `RUN` commands
   - **Package Rules**: Version constraints and PR configuration

3. **Renovate PR Creation**: When a newer version is available, Renovate:
   - Detects the current version using the regex pattern
   - Creates a PR to update the package version string in the Dockerfile
   - Includes CVE details and remediation guidance

**Example Dockerfile Before:**
```dockerfile
FROM alpine:latest
RUN apk --no-cache add openssl=3.0.7-r0 curl=7.88.0-r0
```

**Example Dockerfile After (via Renovate PR):**
```dockerfile
FROM alpine:latest
RUN apk --no-cache add openssl=3.0.9-r0 curl=8.1.0-r0
```

**Supported Package Managers:**
- `apk` (Alpine Linux)
- `apt` / `apt-get` (Debian, Ubuntu)
- `yum` (RHEL, CentOS)
- `dnf` (Fedora)

**Configuration:**
Regex managers are defined in `renovate.json` and dynamically extended by the generated rules in `renovate-dockerfile-regex.json`.

### 2. GitHub Issue Creation for Unfixable Vulnerabilities

When Black Duck reports vulnerabilities with no available fix, the pipeline automatically creates GitHub Issues instead of attempting Renovate PRs.

**Detection Criteria:**
A vulnerability is considered "unfixable" when:
- `recommended_version` is missing, empty, or `null`
- `fixed_versions` is missing, empty, or `[]`

**GitHub Issue Features:**

- **Detailed Context**: CVE ID, severity, CVSS score, affected component, ecosystem
- **Remediation Guidance**: 5-step action plan for handling unfixable vulnerabilities
- **Automatic Labels**: `security`, `unfixable`, `blackduck`, `{severity}-priority`, `{ecosystem}`
- **Monitoring Reminder**: Instructions to monitor vendor announcements
- **Risk Assessment**: Guidance to evaluate impact and implement mitigations

**Issue Creation Workflow:**

1. `create_github_issues.py` scans the Black Duck report
2. Generates a shell script with `gh issue create` commands
3. Workflow executes the script using GitHub CLI
4. Issues are created with proper labels and assignments

**Example Issue:**
```
Title: [Security] CVE-2023-UNFIXED (CRITICAL): No fix available for zlib

Labels: security, unfixable, blackduck, critical-priority, alpine

Body: Detailed markdown with CVE info, affected component, and remediation steps
```

**Benefits:**
- **Visibility**: Unfixable vulnerabilities are tracked and not silently ignored
- **Risk Management**: Security team can assess and prioritize mitigation strategies
- **Monitoring**: Issues remain open until a fix becomes available
- **Automation**: No manual intervention required for issue creation

### 3. Base Image OS Package Patching ✨ **NEW**

When OS-level packages in **base image layers** have vulnerabilities (packages NOT in RUN commands), the system automatically patches Dockerfiles to upgrade them.

**The Problem:**

Traditional Renovate regex managers can only update packages that appear in `RUN` commands. But many vulnerabilities exist in the base image itself:

```dockerfile
FROM node:16.14.0-alpine
# alpine:3.16 base layer contains libssl3=3.0.8-r0 (VULNERABLE)
# This package is NOT in any RUN command!
# Renovate regex managers CANNOT fix it!
```

**The Solution:**

Three new scripts work together to automatically patch Dockerfiles:

1. **`detect_base_image_vulns.py`** - Categorizes vulnerabilities
   - Detects which OS packages are in base images vs. explicit installs
   - Outputs: `vuln-categorization.json`

2. **`patch_base_image_dockerfiles.py`** - Modifies Dockerfiles
   - Adds `RUN apk/apt/yum upgrade` commands with pinned versions
   - Inserts after `FROM`, before `COPY` (optimal for caching)
   - Supports `--dry-run` for preview
   - Outputs: Modified Dockerfiles + `dockerfile-patches.json`

3. **`generate_upgrade_regex.py`** - Creates Renovate regex managers
   - Generates regex to match the new upgrade commands
   - Renovate keeps packages updated automatically
   - Outputs: `renovate-base-image-upgrades.json`

**Example Transformation:**

```dockerfile
# BEFORE (vulnerable base image packages)
FROM node:16.14.0-alpine
WORKDIR /app
COPY . .

# AFTER (automatically patched)
FROM node:16.14.0-alpine

# Security: Upgrade base image OS packages to fix vulnerabilities
# Fixes: CVE-2023-2650
RUN apk upgrade --no-cache libssl3=3.0.9-r1 libcrypto3=3.0.9-r1

WORKDIR /app
COPY . .
```

**Future Renovate PR:**

When `libssl3=3.0.10-r0` becomes available, Renovate automatically creates a PR:

```diff
-RUN apk upgrade --no-cache libssl3=3.0.9-r1 libcrypto3=3.0.9-r1
+RUN apk upgrade --no-cache libssl3=3.0.10-r0 libcrypto3=3.0.10-r0
```

**Benefits:**

✅ **Automated** - Runs in GitHub Actions<br>
✅ **Non-breaking** - Stays on same base image version (Node 16, not Node 20)<br>
✅ **Granular** - Updates specific packages, not entire base image<br>
✅ **Self-maintaining** - Renovate keeps packages current<br>
✅ **Complete coverage** - Handles ALL OS vulnerability types<br>

**Quick Start:**

```bash
# Run the complete workflow
./test_base_image_patching.sh

# Or step-by-step
python3 security-tooling/detect_base_image_vulns.py
python3 security-tooling/patch_base_image_dockerfiles.py --dry-run
python3 security-tooling/patch_base_image_dockerfiles.py
python3 security-tooling/generate_upgrade_regex.py
```

**Documentation:**
- **[security-tooling/BASE_IMAGE_PATCHING.md](security-tooling/BASE_IMAGE_PATCHING.md)** - Complete feature documentation
- **[security-tooling/QUICK_START.md](security-tooling/QUICK_START.md)** - Quick reference guide
- **[security-tooling/ARCHITECTURE.md](security-tooling/ARCHITECTURE.md)** - System architecture
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation overview

**Supported Package Managers:** `apk` (Alpine), `apt` (Debian/Ubuntu), `yum` (RHEL/CentOS)

---

## Contributing

When adding new components or services:

1. **Update Component Ownership**: Add entry to `security-tooling/component_ownership.json`
2. **Track Container Images**: Prebuilt images in `image_map.json`, custom images documented in `docker-compose.yml` with `# Owner:` and `# Base:` comments
3. **Test Reviewer Assignment**: Run `manage_reviewers.py analyze` to verify correct routing
4. **No Code Changes Needed**: Automation scripts auto-discover new packages

---

## License

This is a demonstration repository for educational purposes.

---

## Support

For questions or issues with the security automation pipeline, refer to:
- [security-tooling/DOCUMENTATION.md](security-tooling/DOCUMENTATION.md) - Technical deep dive
- [security-tooling/README.md](security-tooling/README.md) - Quick reference guide
