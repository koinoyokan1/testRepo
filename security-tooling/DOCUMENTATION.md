# Complete Documentation - Black Duck + Renovate Integration

## Table of Contents

1. [Multi-Ecosystem Overview](#multi-ecosystem-overview)
2. [Architecture](#architecture)
3. [Component Ownership System](#component-ownership-system)
4. [Nested Go Modules Support](#nested-go-modules-support)
5. [TypeScript/npm Support](#typescriptnpm-support)
6. [Automated Reviewer Assignment](#automated-reviewer-assignment)

---

## Multi-Ecosystem Overview

### 🎯 What This System Does

A **fully automated security vulnerability remediation system** that:
1. ✅ Reads Black Duck vulnerability reports (Go + npm)
2. ✅ Generates Renovate rules for each CVE
3. ✅ Finds which components use each vulnerable package
4. ✅ Automatically assigns correct reviewers based on component ownership
5. ✅ Creates separate PRs per vulnerability with context and reviewers

### 📊 Current Repository State

**Ecosystems Supported:**
- **Go**: 4 modules (main + 3 nested contrib modules)
- **npm**: 3 packages (2 services + 1 contrib plugin)
- **Total**: 11 components with ownership

**Vulnerabilities Being Tracked:**

| Package | Ecosystem | CVE | Severity | Current | Fixed | Components Affected |
|---------|-----------|-----|----------|---------|-------|---------------------|
| gin-gonic/gin | Go | CVE-2023-29401 | HIGH | 1.8.0 | 1.9.1 | 8 (all Go services) |
| gin-gonic/gin | Go | CVE-2023-26125 | MEDIUM | 1.8.0 | 1.9.1 | 8 (all Go services) |
| axios | npm | CVE-2021-3749 | HIGH | 0.21.1 | 1.6.0 | 3 (all TypeScript services) |
| lodash | npm | CVE-2021-23337 | HIGH | 4.17.20 | 4.17.21 | 2 (admin + analytics) |
| lodash | npm | CVE-2020-8203 | MEDIUM | 4.17.19 | 4.17.21 | 2 (admin + analytics) |

**Reviewers Required:**

**Total unique reviewers**: 24

**Go reviewers (18)**:
- alice@, bob@, charlie@ (API Gateway)
- david@, eve@ (Auth)
- frank@, grace@, henry@ (Users)
- iris@, jack@ (Payment)
- nancy@, oliver@ (Utilities)
- rachel@, steve@ (Plugin A)
- tina@, uma@ (Plugin B)
- techleads@, architects@ (Default)

**npm reviewers (6)**:
- xavier@, yvonne@ (Web Frontend)
- zoe@, adam@ (Admin Dashboard)
- blake@, clara@ (Analytics Plugin)

### 🔧 How Each Tool Works

#### 1. `find_reviewers.py` (Go)
```bash
python3 find_reviewers.py github.com/gin-gonic/gin
```

**What it does:**
1. Finds all `go.mod` files in repository
2. Runs `go list -json ./...` in each module directory
3. Identifies packages that import `github.com/gin-gonic/gin`
4. Maps files to components via directory matching
5. Collects owners from `component_ownership.json`

**Output:**
- 8 components affected
- 18 reviewers needed
- JSON report with files, components, owners

#### 2. `find_npm_reviewers.py` (TypeScript/JavaScript)
```bash
python3 find_npm_reviewers.py axios
```

**What it does:**
1. Finds all `package.json` files (excluding node_modules)
2. Checks if package is in dependencies/devDependencies
3. Uses `grep` to find TypeScript/JavaScript files importing the package
4. Maps files to components via directory matching
5. Collects owners from `component_ownership.json`

**Output:**
- 3 components affected
- 6 reviewers needed
- JSON report with files, components, owners

#### 3. `find_all_reviewers.py` (Unified)
```bash
python3 find_all_reviewers.py
```

**What it does:**
1. Reads `blackduck_report.json`
2. For each vulnerability:
   - Detects ecosystem (go/npm)
   - Calls appropriate reviewer finder
   - Deduplicates same package across multiple CVEs
3. Generates consolidated summary
4. Saves `generated/reviewer_analysis.json`

**Output:**
```
📊 Overall Statistics:
  • Vulnerable packages: 3
  • Total unique reviewers: 24

📦 Packages:
  GO: github.com/gin-gonic/gin → 8 components, 18 reviewers
  NPM: axios → 3 components, 6 reviewers
  NPM: lodash → 2 components, 4 reviewers
```

#### 4. `generate_renovate_rules.py`
```bash
python3 generate_renovate_rules.py
```

**What it does:**
1. Reads `blackduck_report.json`
2. For each vulnerability:
   - Creates a Renovate `packageRule`
   - Sets `matchDatasources` based on ecosystem
   - Constrains version to same minor (e.g., `>=1.9.1 <1.10.0`)
   - Adds CVE details to PR title and body
3. Outputs `generated/renovate-blackduck-generated.json`

**Example Output:**
```json
{
  "matchDatasources": ["npm"],
  "matchPackageNames": ["axios"],
  "allowedVersions": ">=1.6.0 <1.7.0",
  "prTitle": "fix(security): update axios to v1.6.0 to fix CVE-2021-3749 (HIGH)",
  "labels": ["security", "high-priority", "blackduck", "npm"]
}
```

### 🚀 End-to-End Flow

**Step 1: Black Duck Scan**
Black Duck scans the repository and generates `blackduck_report.json`:
- Identifies 5 vulnerabilities across 3 packages
- Provides CVE IDs, severity, current/fixed versions
- Includes ecosystem metadata (go/npm)

**Step 2: Generate Renovate Rules**
GitHub Action runs:
```bash
python3 generate_renovate_rules.py
```
Creates 5 package rules (one per CVE) in `generated/renovate-blackduck-generated.json`

**Step 3: Find Reviewers**
GitHub Action runs:
```bash
python3 find_all_reviewers.py
```
Analyzes impact across all ecosystems and saves `generated/reviewer_analysis.json`

**Step 4: Add Reviewers to PRs**
GitHub Action runs:
```bash
python3 add_renovate_reviewers.py
```
Merges reviewer data into Renovate config

**Step 5: Renovate Creates PRs**

Renovate creates separate PRs for each unique package:

**PR #1: gin Update (Go)**
```
Title: fix(security): update gin to v1.9.1 to fix CVE-2023-29401 (HIGH)
Files:
  - go.mod (main module)
  - contrib/plugin-a/go.mod
  - contrib/plugin-b/go.mod
  - go.sum files
Reviewers: alice@, bob@, charlie@, david@, eve@, frank@, grace@, henry@,
           iris@, jack@, nancy@, oliver@, rachel@, steve@, tina@, uma@,
           techleads@, architects@
Labels: security, high-priority, blackduck, cve-2023-29401, go
```

**PR #2: axios Update (npm)**
```
Title: fix(security): update axios to v1.6.0 to fix CVE-2021-3749 (HIGH)
Files:
  - services/web-frontend/package.json
  - services/admin-dashboard/package.json
  - contrib/analytics-plugin/package.json
  - package-lock.json files
Reviewers: xavier@, yvonne@, zoe@, adam@, blake@, clara@
Labels: security, high-priority, blackduck, cve-2021-3749, npm
```

### 📁 Repository Structure

```
testRepo/
├── go.mod                              # Main Go module (gin v1.8.0)
├── services/
│   ├── api-gateway/                    # Go service
│   ├── auth/                           # Go service
│   ├── users/                          # Go service
│   ├── payment/                        # Go service
│   ├── web-frontend/                   # TypeScript service
│   │   ├── package.json               # axios 0.21.1, express 4.17.1
│   │   └── src/index.ts
│   └── admin-dashboard/                # TypeScript service
│       ├── package.json               # axios 0.21.1, lodash 4.17.20
│       └── src/server.ts
│
├── contrib/                            # Nested modules
│   ├── plugin-a/
│   │   └── go.mod                     # Go module (gin v1.8.0)
│   ├── plugin-b/
│   │   └── go.mod                     # Go module (gin v1.9.0)
│   ├── shared-lib/
│   │   └── go.mod                     # Go module (no gin)
│   └── analytics-plugin/               # TypeScript plugin
│       ├── package.json               # axios 0.21.1, lodash 4.17.19
│       └── src/index.ts
│
├── blackduck_report.json               # Input: vulnerability scan
├── component_ownership.json            # Input: ownership mapping
│
├── find_reviewers.py                   # Tool: Go reviewer finder
├── find_npm_reviewers.py               # Tool: npm reviewer finder
├── find_all_reviewers.py               # Tool: unified finder
├── generate_renovate_rules.py          # Tool: rule generator
├── add_renovate_reviewers.py           # Tool: reviewer integration
│
├── renovate.json                       # Config: base settings
└── generated/                          # Generated files
    ├── renovate-blackduck-generated.json   # Generated: package rules
    ├── renovate-reviewers.json             # Generated: reviewer config
    └── reviewer_analysis.json              # Generated: reviewer data
```

### 🎓 Key Design Decisions

1. **Ecosystem Detection** - Uses `ecosystem` field in Black Duck JSON to route to correct tool
2. **Version Constraints** - Constrains to same minor version to avoid breaking changes (e.g., `1.9.1` → `>=1.9.1 <1.10.0`)
3. **Separate PRs Per Package** - Each package gets its own PR with targeted reviewers
4. **Component-Based Ownership** - Files inherit ownership from directory structure, supporting nested modules
5. **Multi-Ecosystem Design** - Each ecosystem has dedicated finder, unified by common interface

---

## Architecture

### Component Ownership & Reviewer Assignment System

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions Workflow                      │
│                     (.github/workflows/renovate.yml)                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐ ┌──────────────┐ ┌────────────────┐
        │  Black Duck   │ │  Component   │ │   Codebase     │
        │  Report       │ │  Ownership   │ │   (Go files)   │
        │  (JSON)       │ │  (JSON)      │ │                │
        └───────────────┘ └──────────────┘ └────────────────┘
                │               │                   │
                ▼               ▼                   │
        ┌───────────────────────────────────┐      │
        │  generate_renovate_rules.py       │      │
        │  • Parse vulnerabilities          │      │
        │  • Create package rules           │      │
        │  • Add version constraints        │      │
        └───────────────────────────────────┘      │
                │                                   │
                │  generated/renovate-blackduck-generated.json
                │                                   │
                ▼                                   ▼
        ┌───────────────────────────────────────────────┐
        │  add_renovate_reviewers.py                    │
        │  ┌──────────────────────────────────────────┐ │
        │  │ 1. find_reviewers.py (go list)           │ │
        │  │    • Run 'go list -json ./...'           │ │
        │  │    • Find packages importing dependency  │ │
        │  │    • Map files → components              │ │
        │  │    • Collect component owners            │ │
        │  └──────────────────────────────────────────┘ │
        │  ┌──────────────────────────────────────────┐ │
        │  │ 2. Generate reviewer config              │ │
        │  │    • Limit to 5 reviewers max            │ │
        │  │    • Add component labels                │ │
        │  └──────────────────────────────────────────┘ │
        └───────────────────────────────────────────────┘
                │
                │  generated/renovate-reviewers.json
                │
                ▼
        ┌───────────────────────────────────┐
        │  Merge Configs (Python)           │
        │  • Combine Black Duck rules       │
        │  • Add reviewer assignments       │
        │  • Merge component labels         │
        └───────────────────────────────────┘
                │
                │  renovate-merged.json
                │
                ▼
        ┌───────────────────────────────────┐
        │  Renovate Bot                     │
        │  • Scan dependencies              │
        │  • Apply package rules            │
        │  • Create PR                      │
        └───────────────────────────────────┘
                │
                ▼
        ┌───────────────────────────────────┐
        │  Pull Request                     │
        │  ✓ Version: v1.9.1 (constrained)  │
        │  ✓ Reviewers: alice@, david@, ... │
        │  ✓ Labels: component:api-gateway  │
        │  ✓ Description: CVE details       │
        └───────────────────────────────────┘
```

### Directory to Component Mapping

```
Repository Root
├── services/
│   ├── api-gateway/          → API Gateway (alice@)
│   │   ├── main.go
│   │   └── handlers/
│   │       └── user.go       → Inherits: API Gateway
│   │
│   ├── auth/                 → Auth Service (david@)
│   │   └── server.go
│   │
│   ├── users/                → User Management (frank@, grace@)
│   │   └── handler.go
│   │
│   └── payment/              → Payment Processing (iris@)
│       └── api.go
│
├── pkg/
│   ├── utils/                → Shared Utilities (nancy@)
│   │   └── middleware.go
│   │
│   └── database/             → Data Layer (paul@)
│       └── connection.go
│
└── main.go                   → Default (techleads@)
```

### Dependency Impact Flow

```
github.com/gin-gonic/gin update detected
                │
                ▼
        go list -json ./...
                │
                ▼
   Parse Imports for each package
                │
        ┌───────┴───────┬────────┬─────────┬──────────┐
        ▼               ▼        ▼         ▼          ▼
    api-gateway    auth     users    payment     utils
        │               │        │         │          │
        ▼               ▼        ▼         ▼          ▼
  alice@company  david@     frank@    iris@      nancy@
                           grace@
```

### Component Ownership Resolution

```
File: services/api-gateway/handlers/users/create.go
                │
                ▼
Check: services/api-gateway/handlers/users
                │  (no match)
                ▼
Check: services/api-gateway/handlers
                │  (no match)
                ▼
Check: services/api-gateway
                │  ✓ MATCH!
                ▼
        API Gateway Component
                │
                ▼
        alice@company.com (primary)
        bob@company.com (secondary)
        charlie@company.com (secondary)
```

### Version Constraint Logic

```
Black Duck Report:
  "recommended_version": "1.9.1"
                │
                ▼
    Parse version: [1, 9, 1]
                │
                ▼
    Calculate constraint:
      major = 1
      minor = 9
      next_minor = 10
                │
                ▼
    allowedVersions: ">=1.9.1 <1.10.0"
                │
                ▼
    Renovate picks: v1.9.1 ✓
    (not v1.12.0 which requires Go 1.25)
```

---

## Component Ownership System

### Overview

When a dependency (e.g., `github.com/gin-gonic/gin`) needs to be updated:

1. **Dependency Analysis**: Find all files that import the dependency
2. **Component Mapping**: Map each file to its owning component by recursively checking parent directories
3. **Owner Identification**: Identify primary and secondary owners for each affected component
4. **Reviewer Assignment**: Automatically add owners as reviewers on the Renovate PR

### Configuration: `component_ownership.json`

Defines the mapping of directories to components and their owners:

```json
{
  "components": [
    {
      "name": "API Gateway",
      "directories": ["services/api-gateway", "cmd/api-gateway"],
      "owners": {
        "primary": ["alice@company.com"],
        "secondary": ["bob@company.com"]
      }
    }
  ],
  "default_reviewers": {
    "primary": ["techleads@company.com"],
    "secondary": ["architects@company.com"]
  }
}
```

**Key concepts:**
- **Components**: Logical groupings of code (e.g., "API Gateway", "User Management")
- **Directories**: One component can own multiple directories
- **Primary Owners**: Main responsible parties
- **Secondary Owners**: Backup reviewers
- **Default Reviewers**: Used when no component matches (e.g., root-level files)

### Directory Matching Algorithm

For a file like `services/api-gateway/handlers/user.go`:

1. Start at `services/api-gateway/handlers`
2. Check if any component owns `services/api-gateway/handlers` → No
3. Move up to `services/api-gateway`
4. Check if any component owns `services/api-gateway` → Yes! "API Gateway" component
5. Assign API Gateway owners as reviewers

This works recursively, so subdirectories automatically inherit ownership.

### Scripts

**`find_reviewers.py`** - Analyzes which components are affected by a dependency update using Go's native `go list` command.

**Usage:**
```bash
# Find reviewers for gin update
python3 find_reviewers.py github.com/gin-gonic/gin

# Primary owners only
python3 find_reviewers.py github.com/gin-gonic/gin --primary-only
```

**`add_renovate_reviewers.py`** - Generates Renovate configuration with automated reviewer assignments.

**Usage:**
```bash
python3 add_renovate_reviewers.py
```

### Integration with Renovate

The GitHub Actions workflow (`.github/workflows/renovate.yml`) automatically:

1. Generates Renovate rules from Black Duck findings
2. Analyzes affected components and identifies owners
3. Merges reviewer assignments into Renovate configuration
4. Creates PRs with appropriate reviewers and labels

**PR Labels** - PRs automatically get labeled with affected components:
- `component:api-gateway`
- `component:authentication-service`
- `component:user-management`

**Reviewer Limits** - To avoid overwhelming PRs:
- **Maximum 5 reviewers** per PR
- **Priority**: Primary owners from most-affected components first

### Example

**Scenario**: `github.com/gin-gonic/gin` needs security update

**Files Affected:**
- `services/api-gateway/main.go`
- `services/auth/server.go`
- `services/users/handler.go`
- `services/payment/api.go`
- `pkg/utils/middleware.go`

**Components Affected:**
- API Gateway (alice@company.com)
- Authentication Service (david@company.com)
- User Management (frank@company.com, grace@company.com)
- Payment Processing (iris@company.com)
- Shared Utilities (nancy@company.com)

**Reviewers Added:**
- alice@company.com (API Gateway primary)
- david@company.com (Auth primary)
- frank@company.com (Users primary)
- grace@company.com (Users primary)
- iris@company.com (Payment primary)

**Labels Added:**
- `security`, `high-priority`
- `component:api-gateway`
- `component:authentication-service`
- `component:user-management`

---

## Nested Go Modules Support

### Overview

This repository supports **nested Go modules** - multiple independent `go.mod` files in subdirectories. This is useful for:
- **Monorepos** with multiple independent projects
- **Contrib/plugin directories** with separate versioning
- **Multi-module workspaces**

### Repository Structure

```
testRepo/
├── go.mod                          # Main module: example.com/oldversion
├── services/
│   ├── api-gateway/                # Part of main module
│   ├── auth/                       # Part of main module
│   └── ...
│
└── contrib/                        # Nested modules
    ├── plugin-a/
    │   ├── go.mod                  # Independent module: example.com/contrib/plugin-a
    │   └── main.go                 # Uses gin v1.8.0
    │
    ├── plugin-b/
    │   ├── go.mod                  # Independent module: example.com/contrib/plugin-b
    │   └── plugin.go               # Uses gin v1.9.0
    │
    └── shared-lib/
        ├── go.mod                  # Independent module: example.com/contrib/shared-lib
        └── utils.go                # Doesn't use gin
```

### How It Works

**Automatic Module Discovery**

The `find_reviewers.py` script automatically discovers all `go.mod` files:

```python
def find_all_go_modules(root_dir: str = ".") -> List[str]:
    """Find all go.mod files in the repository"""
    # Finds:
    # - ./go.mod (main module)
    # - ./contrib/plugin-a/go.mod
    # - ./contrib/plugin-b/go.mod
    # - ./contrib/shared-lib/go.mod
```

**Independent Scanning**

Each module is scanned independently:

```bash
# For main module
cd . && go list -json ./...

# For contrib/plugin-a
cd contrib/plugin-a && go list -json ./...

# For contrib/plugin-b
cd contrib/plugin-b && go list -json ./...
```

### Example: gin-gonic/gin Update

When `github.com/gin-gonic/gin` needs updating:

**Modules Affected**
```
Found 4 Go module(s):
  - . (main module)
  - ./contrib/shared-lib (doesn't use gin)
  - ./contrib/plugin-a (uses gin v1.8.0)
  - ./contrib/plugin-b (uses gin v1.9.0)
```

**Components Affected**
```
8 components affected:
  1. API Gateway (main module)
  2. Auth Service (main module)
  3. Users Service (main module)
  4. Payment Service (main module)
  5. Shared Utilities (main module)
  6. Default (main.go in root)
  7. Contrib Plugin A ← nested module
  8. Contrib Plugin B ← nested module
```

**Reviewers Assigned**
```
18 total reviewers (including contrib owners):
  ✓ rachel@company.com (Plugin A primary)
  ✓ steve@company.com (Plugin A secondary)
  ✓ tina@company.com (Plugin B primary)
  ✓ uma@company.com (Plugin B secondary)
  ... plus all main module owners
```

### Version Management

**Different Versions Per Module**

Each module can have **different versions** of the same dependency:

- **Main module**: `github.com/gin-gonic/gin v1.8.0`
- **contrib/plugin-a**: `github.com/gin-gonic/gin v1.8.0` (same)
- **contrib/plugin-b**: `github.com/gin-gonic/gin v1.9.0` (different!)

**Renovate Behavior**

Renovate will create **separate PRs** for each module:

1. **PR #1**: Update main module + plugin-a to v1.9.1
2. **PR #2**: Update plugin-b from v1.9.0 to v1.9.1 (smaller change)

Each PR will have **different reviewers** based on affected components.

### Component Ownership for Nested Modules

Add each nested module to `component_ownership.json`:

```json
{
  "name": "Contrib Plugin A",
  "directories": ["contrib/plugin-a"],
  "owners": {
    "primary": ["rachel@company.com"],
    "secondary": ["steve@company.com"]
  }
}
```

### Benefits

1. **Independent Versioning** - Main module can stay on stable versions; contrib plugins can use latest features
2. **Isolated Updates** - Update plugin-a without affecting main module
3. **Clear Ownership** - Each plugin has its own owners; reviewers automatically assigned per module

### Limitations

**Circular Dependencies** - Nested modules **cannot** import the parent module:

```go
// ❌ NOT ALLOWED in contrib/plugin-a
import "example.com/oldversion/pkg/utils"

// ✅ OK - use shared-lib instead
import "example.com/contrib/shared-lib"
```

**Build Complexity**
- Multiple `go.sum` files to maintain
- Separate `go mod tidy` for each module
- More complex CI/CD pipelines

**Renovate Considerations**
- More PRs (one per module per dependency)
- Potentially overwhelming for large monorepos
- Consider grouping with Renovate's `groupName` config

### Go Workspace (Optional)

For better IDE support, create a `go.work` file:

```go
go 1.20

use (
    .
    ./contrib/plugin-a
    ./contrib/plugin-b
    ./contrib/shared-lib
)
```

This allows your IDE to understand all modules at once, while keeping them independent.

---

## TypeScript/npm Support

### Overview

The Black Duck + Renovate integration supports **both Go and npm (TypeScript/JavaScript)** ecosystems. The reviewer assignment system automatically detects which files use vulnerable packages and assigns the appropriate team members.

### Added Components

**TypeScript Services**

```
services/
├── web-frontend/          # TypeScript frontend service
│   ├── package.json      # Uses axios 0.21.1, express 4.17.1
│   ├── tsconfig.json
│   └── src/index.ts
│
└── admin-dashboard/       # TypeScript admin service
    ├── package.json      # Uses axios 0.21.1, lodash 4.17.20
    ├── src/server.ts
    └── ...

contrib/
└── analytics-plugin/      # Analytics plugin
    ├── package.json      # Uses axios 0.21.1, lodash 4.17.19
    └── src/index.ts
```

**Component Ownership**

New TypeScript components added to `component_ownership.json`:

| Component | Directory | Primary | Secondary |
|-----------|-----------|---------|-----------|
| Web Frontend | services/web-frontend | xavier@ | yvonne@ |
| Admin Dashboard | services/admin-dashboard | zoe@ | adam@ |
| Analytics Plugin | contrib/analytics-plugin | blake@ | clara@ |

### Black Duck Vulnerabilities (npm)

**axios CVE-2021-3749 (HIGH)**
- **Severity**: HIGH (CVSS 7.5)
- **Description**: Server-Side Request Forgery (SSRF)
- **Current Version**: 0.21.1
- **Fixed Version**: 1.6.0
- **Affected**: services/web-frontend, services/admin-dashboard, contrib/analytics-plugin

**lodash CVE-2021-23337 (HIGH)**
- **Severity**: HIGH (CVSS 7.2)
- **Description**: Command injection vulnerability
- **Current Version**: 4.17.20
- **Fixed Version**: 4.17.21
- **Affected**: services/admin-dashboard (4.17.20), contrib/analytics-plugin (4.17.19)

### How It Works

**1. Dependency Discovery**

Find all `package.json` files (excluding `node_modules/`):

```bash
find . -name "package.json" -type f -not -path "*/node_modules/*"
```

Found:
- `./services/web-frontend/package.json`
- `./services/admin-dashboard/package.json`
- `./contrib/analytics-plugin/package.json`

**2. Import Analysis**

For each package, search for imports in TypeScript/JavaScript files:

```bash
grep -r -l --include=*.ts --include=*.js \
  -E "(import.*from ['\"]axios['\"]|require\\(['\"]axios['\"]\\))"
```

**3. Component Mapping**

Files are mapped to components by directory prefix, same as Go:
- `services/web-frontend/src/index.ts` → **Web Frontend** component
- `services/admin-dashboard/src/server.ts` → **Admin Dashboard** component

**4. Reviewer Assignment**

Reviewers are collected from affected components:
- **axios** update → 6 reviewers (xavier@, yvonne@, zoe@, adam@, blake@, clara@)
- **lodash** update → 4 reviewers (zoe@, adam@, blake@, clara@)

### Testing

**Test npm Reviewer Finder**

```bash
python3 find_npm_reviewers.py axios
```

Output:
```
Found 3 npm package(s)
📦 NPM Packages:
  - ./contrib/analytics-plugin
  - ./services/admin-dashboard
  - ./services/web-frontend

🔍 Components Affected:
  📦 Web Frontend
     Files (1): ./services/web-frontend/src/index.ts
     Owners: xavier@, yvonne@

  📦 Admin Dashboard
     Files (1): ./services/admin-dashboard/src/server.ts
     Owners: zoe@, adam@

  📦 Analytics Plugin
     Files (1): ./contrib/analytics-plugin/src/index.ts
     Owners: blake@, clara@

👥 Reviewers: 6 total
```

**Test Unified Finder (Go + npm)**

```bash
python3 find_all_reviewers.py
```

Output:
```
📊 Overall Statistics:
  • Vulnerable packages: 3
  • Total unique reviewers: 24

📦 Packages Requiring Updates:
  GO: github.com/gin-gonic/gin
    └─ CVE-2023-29401 (HIGH)
    └─ 8 component(s) affected
    └─ 18 reviewer(s) needed

  NPM: axios
    └─ CVE-2021-3749 (HIGH)
    └─ 3 component(s) affected
    └─ 6 reviewer(s) needed

  NPM: lodash
    └─ CVE-2021-23337 (HIGH)
    └─ 2 component(s) affected
    └─ 4 reviewer(s) needed
```

### Renovate Configuration

**Updated Settings**

`renovate.json` now enables both Go and npm:

```json
{
  "enabledManagers": ["gomod", "npm"]
}
```

**Generated Package Rules**

The `generate_renovate_rules.py` script generates rules for both ecosystems:

**Go Rule:**
```json
{
  "matchDatasources": ["go"],
  "matchPackageNames": ["github.com/gin-gonic/gin"],
  "allowedVersions": ">=1.9.1 <1.10.0"
}
```

**npm Rule:**
```json
{
  "matchDatasources": ["npm"],
  "matchPackageNames": ["axios"],
  "allowedVersions": ">=1.6.0 <1.7.0"
}
```

### Expected Renovate PRs

When Renovate runs, it creates **separate PRs** for each vulnerability:

**PR #1: axios Update**
- **Package**: axios 0.21.1 → 1.6.0
- **Reviewers**: xavier@, yvonne@, zoe@, adam@, blake@, clara@
- **Files Changed**: services/web-frontend/package.json, services/admin-dashboard/package.json, contrib/analytics-plugin/package.json

**PR #2: lodash Update (Admin Dashboard)**
- **Package**: lodash 4.17.20 → 4.17.21
- **Reviewers**: zoe@, adam@
- **Files Changed**: services/admin-dashboard/package.json, services/admin-dashboard/package-lock.json

**PR #3: lodash Update (Analytics Plugin)**
- **Package**: lodash 4.17.19 → 4.17.21
- **Reviewers**: blake@, clara@
- **Files Changed**: contrib/analytics-plugin/package.json, contrib/analytics-plugin/package-lock.json

### Multi-Ecosystem Summary

The system now handles:

| Ecosystem | Files | Tool | Reviewer Finder |
|-----------|-------|------|-----------------|
| Go | `go.mod` | `go list -json ./...` | `find_reviewers.py` |
| npm | `package.json` | `grep` for imports | `find_npm_reviewers.py` |
| Unified | All | Both | `find_all_reviewers.py` |

**Total in this repo:**
- **4 Go modules** (main + 3 contrib)
- **3 npm packages** (2 services + 1 contrib)
- **11 total components** with ownership
- **24 unique reviewers**

---

## Automated Reviewer Assignment

### 🎯 What Was Built

A complete system for automatically assigning code reviewers to Renovate PRs based on:
1. **Component ownership** - Which teams own which directories
2. **Dependency impact analysis** - Which files use the updated dependency
3. **Recursive directory matching** - Automatically inherit ownership up the directory tree

### 📁 Key Files

**Configuration**
- **`component_ownership.json`** - Maps directories to components and their owners (11 components total)

**Core Scripts**
- **`find_reviewers.py`** - Go dependency analyzer (uses `go list`)
- **`find_npm_reviewers.py`** - npm dependency analyzer (uses grep for imports)
- **`find_all_reviewers.py`** - Unified multi-ecosystem analyzer
- **`add_renovate_reviewers.py`** - Renovate integration (generates reviewer configs)
- **`generate_renovate_rules.py`** - Dynamic rule generator from Black Duck findings

### 🔄 How It Works

```
Black Duck Report
       ↓
[Package: github.com/gin-gonic/gin needs update]
       ↓
find_reviewers.py runs 'go list -json ./...'
       ↓
Go packages found (that import gin):
  - services/api-gateway/main.go
  - services/auth/server.go
  - services/users/handler.go
  - services/payment/api.go
  - pkg/utils/middleware.go
  - main.go
       ↓
Directory matching:
  services/api-gateway → API Gateway component → alice@company.com
  services/auth → Auth Service → david@company.com
  services/users → User Management → frank@, grace@company.com
  services/payment → Payment Processing → iris@company.com
  pkg/utils → Shared Utilities → nancy@company.com
  main.go → Default → techleads@company.com
       ↓
add_renovate_reviewers.py generates config
       ↓
Renovate PR created with:
  ✓ 5 reviewers (alice, architects, bob, charlie, david)
  ✓ Labels: component:api-gateway, component:authentication-service
  ✓ Version constraint: >=1.9.1 <1.10.0 (not v1.12.0!)
```

### 🧪 Testing

Run the complete test:
```bash
./test_reviewer_assignment.sh
```

Or test individual components:
```bash
# Find reviewers for gin package
python3 find_reviewers.py github.com/gin-gonic/gin

# Find reviewers for npm package
python3 find_npm_reviewers.py axios

# Unified analysis (all ecosystems)
python3 find_all_reviewers.py

# Generate Renovate reviewer config
python3 add_renovate_reviewers.py

# View results
cat generated/renovate-reviewers.json
```

### 📊 Example Output

For `github.com/gin-gonic/gin` update:

**Files Affected:** 6
**Components Affected:** 6
**Reviewers:** 14 total (limited to 5 in PR)

```json
{
  "reviewers": [
    "alice@company.com",        // API Gateway primary
    "architects@company.com",   // Default secondary
    "bob@company.com",          // API Gateway secondary
    "charlie@company.com",      // API Gateway secondary
    "david@company.com"         // Auth primary
  ],
  "addLabels": [
    "component:api-gateway",
    "component:authentication-service",
    "component:default"
  ]
}
```

### 🔧 Configuration

**Adding a New Component**

Edit `component_ownership.json`:

```json
{
  "name": "New Service",
  "directories": [
    "services/new-service",
    "pkg/new-service"
  ],
  "owners": {
    "primary": ["owner1@company.com"],
    "secondary": ["owner2@company.com"]
  }
}
```

**Directory Inheritance**

If you add a file at `services/api-gateway/handlers/users/create.go`:
1. Checks `services/api-gateway/handlers/users` → no match
2. Checks `services/api-gateway/handlers` → no match
3. Checks `services/api-gateway` → **MATCH!** (API Gateway component)
4. Assigns alice@company.com (API Gateway primary owner)

### 🎁 Bonus Features

**Version Constraints**
- ❌ Old: `"allowedVersions": ">=1.9.1"` → upgraded to v1.12.0
- ✅ New: `"allowedVersions": ">=1.9.1 <1.10.0"` → stays on v1.9.x

**Component Labels**
- PRs automatically tagged with affected components for easy filtering

### 🔍 Key Learnings

1. **One package can affect multiple components** - gin is used by 6 different teams
2. **Shared utilities are high-impact** - pkg/utils affects everyone who imports it
3. **Default reviewers matter** - Root-level files need ownership too
4. **Version constraints are critical** - Prevent unnecessary major version jumps
