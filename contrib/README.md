# Contrib Directory - Nested Go Modules

This directory contains **independent Go modules** that are separate from the main project but share the same repository.

## Structure

```
contrib/
├── plugin-a/           # Module: example.com/contrib/plugin-a
│   ├── go.mod         # gin v1.8.0 (vulnerable)
│   └── main.go
│
├── plugin-b/           # Module: example.com/contrib/plugin-b
│   ├── go.mod         # gin v1.9.0 (safe)
│   └── plugin.go
│
└── shared-lib/         # Module: example.com/contrib/shared-lib
    ├── go.mod         # No gin dependency
    └── utils.go
```

## Ownership

Each plugin has its own team:

| Module | Primary Owner | Secondary Owner |
|--------|---------------|-----------------|
| plugin-a | rachel@company.com | steve@company.com |
| plugin-b | tina@company.com | uma@company.com |
| shared-lib | victor@company.com | wendy@company.com |

## Dependency Versions

Each module manages its own dependencies independently:

### plugin-a
- **gin**: v1.8.0 (has CVE-2023-29401)
- **Status**: Needs update to v1.9.1+

### plugin-b
- **gin**: v1.9.0 (fixed CVE-2023-29401)
- **Status**: Could update to v1.9.1 for patch fixes

### shared-lib
- **gin**: Not used
- **Status**: No action needed

## How Renovate Handles This

When a gin security update is needed:

1. **Scan**: Renovate finds 4 modules (main + 3 contrib)
2. **Analyze**: Determines which modules use gin:
   - ✅ Main module (v1.8.0)
   - ✅ plugin-a (v1.8.0)
   - ✅ plugin-b (v1.9.0)
   - ❌ shared-lib (doesn't use gin)

3. **Create PRs**:
   - **PR #1**: Update main module to v1.9.1
     - Reviewers: alice@, david@, frank@, ... (main module teams)
   - **PR #2**: Update plugin-a to v1.9.1
     - Reviewers: rachel@, steve@ (plugin-a team)
   - **PR #3**: Update plugin-b from v1.9.0 to v1.9.1
     - Reviewers: tina@, uma@ (plugin-b team)

Each PR is **independent** and can be merged separately.

## Testing

```bash
# Test reviewer assignment
cd ../..
python3 find_reviewers.py github.com/gin-gonic/gin

# Should show:
# - 8 components affected
# - 18 reviewers (including rachel@, steve@, tina@, uma@)
```

## Development

### Adding a New Plugin

1. Create directory: `mkdir contrib/my-plugin`
2. Initialize module: `cd contrib/my-plugin && go mod init example.com/contrib/my-plugin`
3. Add code and dependencies
4. Update `component_ownership.json`:
   ```json
   {
     "name": "Contrib My Plugin",
     "directories": ["contrib/my-plugin"],
     "owners": {
       "primary": ["yourname@company.com"],
       "secondary": ["teammate@company.com"]
     }
   }
   ```

### Building

Each module builds independently:

```bash
# Build plugin-a
cd contrib/plugin-a && go build

# Build plugin-b
cd contrib/plugin-b && go build
```

### IDE Support (Optional)

Create `go.work` in repository root:

```go
go 1.20

use (
    .
    ./contrib/plugin-a
    ./contrib/plugin-b
    ./contrib/shared-lib
)
```

This allows your IDE (VS Code, GoLand) to understand all modules.

## Benefits

✅ **Independent versioning** - Each plugin controls its own dependencies  
✅ **Isolated updates** - Update one plugin without affecting others  
✅ **Clear ownership** - Each plugin has dedicated team  
✅ **Gradual rollout** - Test updates in one plugin before applying to all  
✅ **Separate release cycles** - Plugins can release independently  

## Gotchas

⚠️ **No circular dependencies** - Contrib modules cannot import main module  
⚠️ **Multiple go.sum files** - Need to run `go mod tidy` in each module  
⚠️ **More PRs** - One Renovate PR per module per dependency update  
