# Component Ownership & Automated Reviewer Assignment

This repository uses automated reviewer assignment based on component ownership and dependency analysis.

## Overview

When a dependency (e.g., `github.com/gin-gonic/gin`) needs to be updated:

1. **Dependency Analysis**: Find all files that import the dependency
2. **Component Mapping**: Map each file to its owning component by recursively checking parent directories
3. **Owner Identification**: Identify primary and secondary owners for each affected component
4. **Reviewer Assignment**: Automatically add owners as reviewers on the Renovate PR

## Configuration Files

### `component_ownership.json`

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

## Scripts

### `find_reviewers.py`

Analyzes which components are affected by a dependency update using Go's native `go list` command.

**Requirements:**
- Go toolchain installed
- Valid `go.mod` file

**Usage:**
```bash
# Find reviewers for gin update
python3 find_reviewers.py github.com/gin-gonic/gin

# Primary owners only
python3 find_reviewers.py github.com/gin-gonic/gin --primary-only
```

**Output:**
- Files affected by the update
- Components impacted
- Primary and secondary owners
- Complete list of reviewers to add

### `add_renovate_reviewers.py`

Generates Renovate configuration with automated reviewer assignments.

**Usage:**
```bash
python3 add_renovate_reviewers.py
```

**Inputs:**
- `blackduck_report.json` - Vulnerability findings
- `component_ownership.json` - Component ownership mapping

**Outputs:**
- `renovate-reviewers.json` - Renovate package rules with reviewers

## Integration with Renovate

The GitHub Actions workflow (`.github/workflows/renovate.yml`) automatically:

1. Generates Renovate rules from Black Duck findings
2. Analyzes affected components and identifies owners
3. Merges reviewer assignments into Renovate configuration
4. Creates PRs with appropriate reviewers and labels

### PR Labels

PRs automatically get labeled with affected components:
- `component:api-gateway`
- `component:authentication-service`
- `component:user-management`

### Reviewer Limits

To avoid overwhelming PRs, we limit reviewers to:
- **Maximum 5 reviewers** per PR
- **Priority**: Primary owners from most-affected components first

## Example

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
- `security`
- `high-priority`
- `component:api-gateway`
- `component:authentication-service`
- `component:user-management`

## Updating Component Ownership

To update ownership:

1. Edit `component_ownership.json`
2. Commit and push
3. Next Renovate run will use updated ownership

## Testing

Test the reviewer finder locally:

```bash
# Analyze gin dependency
python3 find_reviewers.py github.com/gin-gonic/gin

# Generate Renovate reviewer config
python3 add_renovate_reviewers.py

# Check output
cat renovate-reviewers.json
```
