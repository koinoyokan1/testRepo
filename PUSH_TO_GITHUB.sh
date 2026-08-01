#!/bin/bash

# Script to push Renovate + Black Duck integration to GitHub
# Run this after validating the setup

set -e

echo "=========================================="
echo "Push to GitHub - Renovate Integration"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if we're in a git repo
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Show status
echo "Git status:"
echo "-----------"
git status --short
echo ""

# Ask for confirmation
read -p "Do you want to add all files and commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Add all files
echo "Adding files..."
git add .

# Show what will be committed
echo ""
echo "Files to be committed:"
echo "----------------------"
git status --short
echo ""

# Commit
echo "Creating commit..."
git commit -m "feat: add Renovate + Black Duck integration

- Add Renovate configuration for automated dependency updates
- Add Black Duck vulnerability simulation (2 Gin CVEs)
- Configure GitHub Actions workflows for automation
- Add comprehensive documentation and setup guides
- Configure separate PRs per CVE fix
- Add validation and testing scripts

Features:
- Automated PR creation for each vulnerability
- Rich security context in PRs (CVE details, CVSS scores)
- Scheduled runs (hourly Renovate, daily Black Duck)
- Dynamic rule generation from Black Duck findings

Simulated vulnerabilities:
- CVE-2023-29401 (HIGH): Directory traversal in Gin v1.8.0
- CVE-2023-26125 (MEDIUM): DoS in Gin v1.8.0

Files created:
- renovate.json - Main Renovate configuration
- .github/workflows/renovate.yml - Renovate workflow
- .github/workflows/blackduck-integration.yml - Black Duck integration
- blackduck.json & blackduck_report.json - Vulnerability data
- simulate_blackduck.py - Black Duck simulator
- generate_renovate_rules.py - Dynamic rule generator
- validate_setup.sh - Setup validation
- Comprehensive documentation (README, setup guides, etc.)
"

echo ""
echo -e "${GREEN}✓${NC} Commit created successfully"
echo ""

# Ask about pushing
read -p "Do you want to push to origin/$CURRENT_BRANCH? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Commit created but not pushed."
    echo "To push later, run: git push origin $CURRENT_BRANCH"
    exit 0
fi

# Push
echo "Pushing to origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo ""
echo -e "${GREEN}✓${NC} Successfully pushed to GitHub!"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Verify files on GitHub:"
echo "   https://github.com/koinoyokan1/testRepo"
echo ""
echo "2. Set up Self-Hosted Renovate:"
echo ""
echo "   • Create GitHub token (repo + workflow scopes)"
echo "   • Add as RENOVATE_TOKEN secret"
echo "   • Enable GitHub Actions"
echo ""
echo "3. See detailed instructions:"
echo "   • QUICK_START.md - 5-minute setup"
echo "   • RENOVATE_SETUP.md - Complete guide"
echo "   • GITHUB_SETUP_COMMANDS.md - Command reference"
echo ""
echo "4. Monitor for PRs:"
echo "   https://github.com/koinoyokan1/testRepo/pulls"
echo ""
echo "=========================================="
