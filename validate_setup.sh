#!/bin/bash

# Validation script for Renovate + Black Duck integration setup
# This script checks if all required files are present and valid

set -e

echo "========================================"
echo "Renovate + Black Duck Setup Validation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_CHECKS_PASSED=true

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 NOT FOUND"
        ALL_CHECKS_PASSED=false
        return 1
    fi
}

# Function to check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 NOT FOUND"
        ALL_CHECKS_PASSED=false
        return 1
    fi
}

# Function to validate JSON
validate_json() {
    if python3 -m json.tool "$1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $1 is valid JSON"
        return 0
    else
        echo -e "${RED}✗${NC} $1 has invalid JSON syntax"
        ALL_CHECKS_PASSED=false
        return 1
    fi
}

echo "1. Checking required files..."
echo "------------------------------"
check_file "renovate.json"
check_file "blackduck.json"
check_file "blackduck_report.json"
check_file "simulate_blackduck.py"
check_file "generate_renovate_rules.py"
check_file "go.mod"
check_file "main.go"
check_file "README.md"
check_file "RENOVATE_SETUP.md"
check_file "QUICK_START.md"
echo ""

echo "2. Checking GitHub Actions workflows..."
echo "----------------------------------------"
check_dir ".github/workflows"
check_file ".github/workflows/renovate.yml"
check_file ".github/workflows/blackduck-integration.yml"
echo ""

echo "3. Validating JSON files..."
echo "---------------------------"
validate_json "renovate.json"
validate_json "blackduck.json"
validate_json "blackduck_report.json"
echo ""

echo "4. Checking Python scripts..."
echo "------------------------------"
if python3 -m py_compile simulate_blackduck.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} simulate_blackduck.py syntax is valid"
else
    echo -e "${RED}✗${NC} simulate_blackduck.py has syntax errors"
    ALL_CHECKS_PASSED=false
fi

if python3 -m py_compile generate_renovate_rules.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} generate_renovate_rules.py syntax is valid"
else
    echo -e "${RED}✗${NC} generate_renovate_rules.py has syntax errors"
    ALL_CHECKS_PASSED=false
fi
echo ""

echo "5. Checking Go module..."
echo "------------------------"
if go mod verify > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} go.mod is valid"
else
    echo -e "${YELLOW}⚠${NC} go.mod verification failed (run 'go mod download')"
fi
echo ""

echo "6. Testing Black Duck simulation..."
echo "------------------------------------"
if python3 simulate_blackduck.py --simple > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Black Duck simulation works"
else
    echo -e "${RED}✗${NC} Black Duck simulation failed"
    ALL_CHECKS_PASSED=false
fi
echo ""

echo "7. Testing Renovate rule generation..."
echo "---------------------------------------"
if python3 generate_renovate_rules.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Renovate rule generation works"
    if [ -f "renovate-blackduck-generated.json" ]; then
        echo -e "${GREEN}✓${NC} Generated renovate-blackduck-generated.json"
    fi
else
    echo -e "${RED}✗${NC} Renovate rule generation failed"
    ALL_CHECKS_PASSED=false
fi
echo ""

echo "8. Checking Renovate configuration..."
echo "--------------------------------------"
if grep -q "github.com/gin-gonic/gin" renovate.json; then
    echo -e "${GREEN}✓${NC} Renovate config includes Gin package"
else
    echo -e "${YELLOW}⚠${NC} Renovate config may not include Gin package"
fi

if grep -q "CVE-2023-29401" renovate.json; then
    echo -e "${GREEN}✓${NC} Renovate config references CVE-2023-29401"
else
    echo -e "${YELLOW}⚠${NC} Renovate config may not reference CVEs"
fi
echo ""

echo "========================================"
echo "Summary"
echo "========================================"

if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push changes to GitHub"
    echo "2. Set up Renovate (see QUICK_START.md)"
    echo "3. Wait for PRs to be created"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Please fix the issues above before proceeding."
    exit 1
fi
