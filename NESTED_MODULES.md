# Nested Go Modules Support

## Overview

This repository supports **nested Go modules** - multiple independent `go.mod` files in subdirectories. This is useful for:
- **Monorepos** with multiple independent projects
- **Contrib/plugin directories** with separate versioning
- **Multi-module workspaces**

## Repository Structure

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

## How It Works

### Automatic Module Discovery

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

### Independent Scanning

Each module is scanned independently:

```bash
# For main module
cd . && go list -json ./...

# For contrib/plugin-a
cd contrib/plugin-a && go list -json ./...

# For contrib/plugin-b
cd contrib/plugin-b && go list -json ./...

# etc.
```

## Example: gin-gonic/gin Update

When `github.com/gin-gonic/gin` needs updating:

### Modules Affected

```
Found 4 Go module(s):
  - . (main module)
  - ./contrib/shared-lib (doesn't use gin)
  - ./contrib/plugin-a (uses gin v1.8.0)
  - ./contrib/plugin-b (uses gin v1.9.0)
```

### Components Affected

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

### Reviewers Assigned

```
18 total reviewers (including contrib owners):
  ✓ rachel@company.com (Plugin A primary)
  ✓ steve@company.com (Plugin A secondary)
  ✓ tina@company.com (Plugin B primary)
  ✓ uma@company.com (Plugin B secondary)
  ... plus all main module owners
```

## Version Management

### Different Versions Per Module

Each module can have **different versions** of the same dependency:

- **Main module**: `github.com/gin-gonic/gin v1.8.0`
- **contrib/plugin-a**: `github.com/gin-gonic/gin v1.8.0` (same)
- **contrib/plugin-b**: `github.com/gin-gonic/gin v1.9.0` (different!)

### Renovate Behavior

Renovate will create **separate PRs** for each module:

1. **PR #1**: Update main module + plugin-a to v1.9.1
2. **PR #2**: Update plugin-b from v1.9.0 to v1.9.1 (smaller change)

Each PR will have **different reviewers** based on affected components.

## Component Ownership for Nested Modules

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

The directory matching works the same - files under `contrib/plugin-a/` are owned by the Plugin A team.

## Benefits

### 1. Independent Versioning
- Main module can stay on stable versions
- Contrib plugins can use latest features
- Shared libraries can have different dependencies

### 2. Isolated Updates
- Update plugin-a without affecting main module
- Test changes in isolation
- Gradual rollout of dependency updates

### 3. Clear Ownership
- Each plugin has its own owners
- Reviewers automatically assigned per module
- No cross-contamination of reviews

## Testing

```bash
# Test reviewer assignment with nested modules
python3 find_reviewers.py github.com/gin-gonic/gin

# Output shows all modules:
# Found 4 Go module(s): ['.', './contrib/shared-lib', './contrib/plugin-a', './contrib/plugin-b']
```

## Go Workspace (Optional)

For better IDE support, you can create a `go.work` file:

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

## Limitations

### Circular Dependencies

Nested modules **cannot** import the parent module:

```go
// ❌ NOT ALLOWED in contrib/plugin-a
import "example.com/oldversion/pkg/utils"

// ✅ OK - use shared-lib instead
import "example.com/contrib/shared-lib"
```

### Build Complexity

Multiple modules mean:
- Multiple `go.sum` files to maintain
- Separate `go mod tidy` for each module
- More complex CI/CD pipelines

### Renovate Considerations

- More PRs (one per module per dependency)
- Potentially overwhelming for large monorepos
- Consider grouping with Renovate's `groupName` config
