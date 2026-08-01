#!/bin/bash

echo "=================================="
echo "Testing Component Ownership System"
echo "=================================="
echo ""

echo "📋 Step 1: Analyze dependency impact"
echo "--------------------------------------"
python3 find_reviewers.py github.com/gin-gonic/gin
echo ""

echo "📋 Step 2: Generate Renovate reviewer config"
echo "--------------------------------------"
python3 add_renovate_reviewers.py
echo ""

echo "📋 Step 3: Show generated reviewer config"
echo "--------------------------------------"
cat renovate-reviewers.json
echo ""

echo "✅ Test complete!"
echo ""
echo "Summary:"
echo "  - Analyzed which files import github.com/gin-gonic/gin"
echo "  - Mapped files to component owners"
echo "  - Generated Renovate configuration with reviewers"
echo ""
echo "Next steps:"
echo "  1. Close existing PR #6 (has wrong version v1.12.0)"
echo "  2. Trigger Renovate workflow"
echo "  3. New PR will have:"
echo "     - Upgrade to gin v1.9.1 (not v1.12.0)"
echo "     - Minimal dependency changes"
echo "     - Auto-assigned reviewers from affected components"
echo "     - Component labels"
