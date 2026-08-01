# Automated Reviewer Assignment - Complete Setup

## 🎯 What We Built

A complete system for automatically assigning code reviewers to Renovate PRs based on:
1. **Component ownership** - Which teams own which directories
2. **Dependency impact analysis** - Which files use the updated dependency
3. **Recursive directory matching** - Automatically inherit ownership up the directory tree

## 📁 Files Created

### Configuration
- **`component_ownership.json`** - Maps directories to components and their owners
  - 7 mock components (API Gateway, Auth, Users, Payment, Web, Utilities, Data Layer)
  - Each has primary and secondary owners
  - Default reviewers for unowned code

### Core Scripts
- **`find_reviewers.py`** - Main analysis tool (uses `go list`)
  - Uses Go's native tooling to find all packages importing a dependency
  - Respects Go module boundaries, build tags, and Go build system
  - Maps files to components via recursive directory matching
  - Outputs affected components and reviewers
  
- **`add_renovate_reviewers.py`** - Renovate integration
  - Reads Black Duck vulnerability report
  - Generates Renovate package rules with reviewers
  - Limits to 5 reviewers max per PR
  - Adds component labels

### Mock Codebase
Created realistic Go service structure to demonstrate:
```
services/
  ├── api-gateway/main.go      → Uses gin
  ├── auth/server.go           → Uses gin
  ├── users/handler.go         → Uses gin
  └── payment/api.go           → Uses gin
pkg/
  ├── utils/middleware.go      → Uses gin
  └── database/connection.go   → Doesn't use gin
```

### Utilities
- **`cleanup_renovate.sh`** - Bash script to delete all Renovate PRs/branches
- **`cleanup_renovate.py`** - Python alternative for cleanup
- **`test_reviewer_assignment.sh`** - End-to-end test script

### Documentation
- **`COMPONENT_OWNERSHIP.md`** - Complete guide to the ownership system
- **`REVIEWER_ASSIGNMENT_SUMMARY.md`** - This file

## 🔄 How It Works

### Flow Diagram

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

## 🧪 Testing

Run the complete test:
```bash
./test_reviewer_assignment.sh
```

Or test individual components:
```bash
# Find reviewers for gin package
python3 find_reviewers.py github.com/gin-gonic/gin

# Generate Renovate reviewer config
python3 add_renovate_reviewers.py

# View results
cat renovate-reviewers.json
```

## 📊 Example Output

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

## 🔧 Configuration

### Adding a New Component

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

### Directory Inheritance

If you add a file at `services/api-gateway/handlers/users/create.go`:
1. Checks `services/api-gateway/handlers/users` → no match
2. Checks `services/api-gateway/handlers` → no match
3. Checks `services/api-gateway` → **MATCH!** (API Gateway component)
4. Assigns alice@company.com (API Gateway primary owner)

## 🚀 Integration with Renovate

The GitHub Actions workflow automatically:

1. Runs `generate_renovate_rules.py` → Creates security fix rules from Black Duck
2. Runs `add_renovate_reviewers.py` → Analyzes component ownership
3. Merges both configs → Final Renovate configuration
4. Creates PR with reviewers and labels

## 🎁 Bonus Features

### Version Constraints
Fixed the issue where Renovate was upgrading to v1.12.0 (requires Go 1.25):
- ❌ Old: `"allowedVersions": ">=1.9.1"` → upgraded to v1.12.0
- ✅ New: `"allowedVersions": ">=1.9.1 <1.10.0"` → stays on v1.9.x

### Component Labels
PRs automatically tagged with affected components for easy filtering

### Cleanup Scripts
Easy way to reset and start fresh when testing

## 📝 Next Steps

1. **Close PR #6** (has wrong version v1.12.0)
2. **Trigger Renovate workflow** (or wait for hourly cron)
3. **New PR will have:**
   - Correct version (v1.9.1)
   - Auto-assigned reviewers
   - Component labels
   - Minimal dependency changes

## 🔍 Key Learnings

1. **One package can affect multiple components** - gin is used by 6 different teams
2. **Shared utilities are high-impact** - pkg/utils affects everyone who imports it
3. **Default reviewers matter** - Root-level files need ownership too
4. **Version constraints are critical** - Prevent unnecessary major version jumps
