# TypeScript/npm Support

## Overview

The Black Duck + Renovate integration now supports **both Go and npm (TypeScript/JavaScript)** ecosystems. The reviewer assignment system automatically detects which files use vulnerable packages and assigns the appropriate team members.

## Added Components

### TypeScript Services

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

### Component Ownership

New TypeScript components added to `component_ownership.json`:

| Component | Directory | Primary | Secondary |
|-----------|-----------|---------|-----------|
| Web Frontend | services/web-frontend | xavier@ | yvonne@ |
| Admin Dashboard | services/admin-dashboard | zoe@ | adam@ |
| Analytics Plugin | contrib/analytics-plugin | blake@ | clara@ |

## Black Duck Vulnerabilities (npm)

### axios CVE-2021-3749 (HIGH)
- **Severity**: HIGH (CVSS 7.5)
- **Description**: Server-Side Request Forgery (SSRF)
- **Current Version**: 0.21.1
- **Fixed Version**: 1.6.0
- **Affected**:
  - services/web-frontend
  - services/admin-dashboard
  - contrib/analytics-plugin

### lodash CVE-2021-23337 (HIGH)
- **Severity**: HIGH (CVSS 7.2)
- **Description**: Command injection vulnerability
- **Current Version**: 4.17.20
- **Fixed Version**: 4.17.21
- **Affected**:
  - services/admin-dashboard (uses 4.17.20)
  - contrib/analytics-plugin (uses 4.17.19)

## How It Works

### 1. Dependency Discovery

The system finds all `package.json` files (excluding `node_modules/`):

```bash
find . -name "package.json" -type f -not -path "*/node_modules/*"
```

Found:
- `./services/web-frontend/package.json`
- `./services/admin-dashboard/package.json`
- `./contrib/analytics-plugin/package.json`

### 2. Import Analysis

For each package, the system searches for imports in TypeScript/JavaScript files:

```bash
grep -r -l --include=*.ts --include=*.js \
  -E "(import.*from ['\"]axios['\"]|require\\(['\"]axios['\"]\\))"
```

### 3. Component Mapping

Files are mapped to components by directory prefix, same as Go:
- `services/web-frontend/src/index.ts` → **Web Frontend** component
- `services/admin-dashboard/src/server.ts` → **Admin Dashboard** component

### 4. Reviewer Assignment

Reviewers are collected from affected components:
- **axios** update → 6 reviewers (xavier@, yvonne@, zoe@, adam@, blake@, clara@)
- **lodash** update → 4 reviewers (zoe@, adam@, blake@, clara@)

## Testing

### Test npm Reviewer Finder

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

### Test Unified Finder (Go + npm)

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

## Renovate Configuration

### Updated Settings

`renovate.json` now enables both Go and npm:

```json
{
  "enabledManagers": ["gomod", "npm"]
}
```

### Generated Package Rules

The `generate_renovate_rules.py` script now generates rules for both ecosystems:

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

## Expected Renovate PRs

When Renovate runs, it will create **separate PRs** for each vulnerability:

### PR #1: axios Update
- **Package**: axios 0.21.1 → 1.6.0
- **Reviewers**: xavier@, yvonne@, zoe@, adam@, blake@, clara@
- **Files Changed**:
  - services/web-frontend/package.json
  - services/admin-dashboard/package.json
  - contrib/analytics-plugin/package.json
  - package-lock.json files

### PR #2: lodash Update (Admin Dashboard)
- **Package**: lodash 4.17.20 → 4.17.21
- **Reviewers**: zoe@, adam@
- **Files Changed**:
  - services/admin-dashboard/package.json
  - services/admin-dashboard/package-lock.json

### PR #3: lodash Update (Analytics Plugin)
- **Package**: lodash 4.17.19 → 4.17.21  
- **Reviewers**: blake@, clara@
- **Files Changed**:
  - contrib/analytics-plugin/package.json
  - contrib/analytics-plugin/package-lock.json

## Multi-Ecosystem Summary

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
