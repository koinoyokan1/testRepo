# Architecture Documentation

This directory contains PlantUML architecture diagrams for the Automated Security Remediation Pipeline.

## 📊 Diagrams

### 1. High-Level Component Diagram
**File:** `architecture-diagram.puml`

**Purpose:** Shows the overall architecture with main components, data flows, and the 6 vulnerability types handled by the system.

**Best for:** 
- Executive presentations
- Onboarding documentation
- High-level architecture reviews

**Key Elements:**
- Input data sources (Black Duck report, component ownership)
- Processing layers (vulnerability analysis, reviewer mapping, rule generation)
- Intermediate artifacts (5 JSON rule fragments)
- Final output (consolidated Renovate configuration)
- Execution environment (GitHub Actions)
- End results (automated PRs with metadata)

---

### 2. Detailed Flow Diagram
**File:** `architecture-diagram-detailed.puml`

**Purpose:** Shows the detailed data flow through 6 phases with specific scripts and file inputs/outputs.

**Best for:**
- Developer onboarding
- Technical deep-dives
- Debugging workflow issues

**Key Elements:**
- Phase 1: Input sources with vulnerability counts
- Phase 2: Python script execution details
- Phase 3: Rule generation by type (1-6)
- Phase 4: Configuration merging process
- Phase 5: GitHub Actions workflow execution
- Phase 6: PR creation with metadata examples

---

## 🔧 How to Use These Diagrams

### Prerequisites

Install PlantUML renderer:

**Option 1: VS Code Extension**
```bash
# Install PlantUML extension
code --install-extension jebbs.plantuml
```

**Option 2: Command-line (requires Java)**
```bash
# macOS
brew install plantuml

# Ubuntu/Debian
sudo apt-get install plantuml
```

**Option 3: Online**
Visit: https://www.plantuml.com/plantuml/uml/

---

### Rendering Diagrams

**VS Code:**
1. Open `.puml` file
2. Press `Alt+D` (or `Cmd+D` on macOS)
3. Preview appears in split pane

**Command-line:**
```bash
# Generate PNG
plantuml docs/architecture-diagram.puml

# Generate SVG (better for docs)
plantuml -tsvg docs/architecture-diagram.puml

# Generate both
plantuml -tpng -tsvg docs/*.puml
```

**Online:**
1. Copy contents of `.puml` file
2. Paste into https://www.plantuml.com/plantuml/uml/
3. Diagram renders automatically

---

## 📚 Understanding the Pipeline

### The 6 Vulnerability Types

The pipeline handles 6 distinct vulnerability categories:

| Type | Scope | Example | Handler Script |
|------|-------|---------|----------------|
| **Type 1** | Go Modules | `github.com/sirupsen/logrus` | `generate_package_rules.py` |
| **Type 2** | npm Packages | `axios`, `lodash` | `generate_package_rules.py` |
| **Type 3** | OS Explicit Install | `RUN apk add curl=8.0.1-r0` | `generate_dockerfile_rules.py` |
| **Type 4** | OS Base Image | `openssl` in FROM layer | `patch_base_image_dockerfiles.py` |
| **Type 5** | Custom Containers | `ghcr.io/company/api-gateway` | `generate_container_image_rules.py` |
| **Type 6** | Prebuilt Containers | `postgres:13.2`, `nginx:1.21.0` | `generate_base_image_rules.py` |

---

### Key Architectural Decisions

**1. External Scanner Integration**
- Black Duck report is the **single source of truth**
- No reliance on Renovate's built-in vulnerability detection
- Allows integration with any security scanner (Snyk, Trivy, etc.)

**2. Dynamic Configuration Generation**
- Renovate config is **generated** at runtime from Black Duck findings
- Not manually maintained (reduces human error)
- Ensures exact version pinning based on scanner recommendations

**3. Component-Based Reviewer Assignment**
- Analyzes codebase to determine which components use each dependency
- Maps affected files to component owners
- Automatically assigns correct reviewers to PRs

**4. Custom File Parsing**
- Uses Renovate's regex managers for non-standard files
- Handles `image_map.json`, Dockerfile `RUN` commands, etc.
- Extends Renovate beyond its native capabilities

**5. Security Metadata Propagation**
- CVE IDs in PR titles, branch names, and labels
- CVSS scores and severity levels in PR bodies
- Enables security team tracking and prioritization

---

## 🔄 Data Flow Summary

```
Black Duck Report (14 vulnerabilities)
         ↓
   [Categorization & Analysis]
         ↓
   5 Python Generators (parallel execution)
         ↓
   5 JSON Rule Fragments
         ↓
   [Configuration Merger]
         ↓
   renovate-merged.json (31 rules, 8 regex managers)
         ↓
   [GitHub Actions → Renovate Bot]
         ↓
   14 Automated Pull Requests
   (exact versions, CVE metadata, assigned reviewers)
```

---

## 📖 Related Documentation

- **Main README:** `../README.md` - Full project documentation
- **Security Tooling README:** `../security-tooling/README.md` - Script-level details
- **Architecture Guide:** `../security-tooling/ARCHITECTURE.md` - Technical specifications

---

## 🎨 Customizing Diagrams

To modify the diagrams:

1. **Edit the `.puml` files** in a text editor
2. **PlantUML syntax reference:** https://plantuml.com/
3. **Color scheme:** Defined at top of each file
4. **Component types:** 
   - `database` = Data storage
   - `component` = Processing unit
   - `file` = File artifact
   - `cloud` = External system
   - `card` = Metadata container

**Example customization:**
```plantuml
!define MY_COLOR #FF5722

component "My Component" as my_comp #MY_COLOR {
  [Sub-component 1]
  [Sub-component 2]
}
```

---

## 🤝 Contributing

When updating the architecture:

1. **Update diagrams first** - Keep visuals in sync with code
2. **Regenerate images** - Commit both `.puml` and rendered `.png/.svg`
3. **Update this README** - Document any new components or flows
4. **Test rendering** - Ensure diagrams display correctly in all viewers

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-04 | Initial architecture diagrams created |

---

## 📧 Questions?

For questions about the architecture or diagrams, please refer to:
- Technical design decisions: See `../security-tooling/ARCHITECTURE.md`
- Implementation details: See individual Python script docstrings
- Renovate configuration: See `../renovate.json` and generated files
