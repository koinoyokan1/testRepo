# System Architecture

## Component Ownership & Reviewer Assignment System

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
                │  renovate-blackduck-generated.json│
                │                                   │
                ▼                                   ▼
        ┌───────────────────────────────────────────────┐
        │  add_renovate_reviewers.py                    │
        │  ┌──────────────────────────────────────────┐ │
        │  │ 1. find_reviewers.py                     │ │
        │  │    • Find files importing package        │ │
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
                │  renovate-reviewers.json
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

## Directory to Component Mapping

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

## Dependency Impact Flow

```
github.com/gin-gonic/gin update detected
                │
                ▼
        grep -r "gin-gonic/gin"
                │
        ┌───────┴───────┬────────┬─────────┬──────────┐
        ▼               ▼        ▼         ▼          ▼
    api-gateway    auth     users    payment     utils
        │               │        │         │          │
        ▼               ▼        ▼         ▼          ▼
  alice@company  david@     frank@    iris@      nancy@
                           grace@
```

## Component Ownership Resolution

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

## Version Constraint Logic

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

## Data Flow Summary

1. **Input:**
   - Black Duck vulnerability report
   - Component ownership mapping
   - Codebase (Go files)

2. **Processing:**
   - Parse vulnerabilities
   - Analyze dependency impact
   - Map files to components
   - Identify owners

3. **Output:**
   - Renovate configuration with:
     - Package rules (what to update)
     - Version constraints (how to update)
     - Reviewers (who to notify)
     - Labels (how to categorize)

4. **Result:**
   - Automated PR with correct reviewers
   - Minimal breaking changes
   - Security vulnerabilities fixed
