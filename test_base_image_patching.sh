#!/bin/bash
# Integration test for base image patching
echo "Testing base image vulnerability patching..."
echo ""
echo "Step 1: Detect base image vulnerabilities"
python3 security-tooling/detect_base_image_vulns.py
echo ""
echo "Step 2: Preview patches (dry-run)"
python3 security-tooling/patch_base_image_dockerfiles.py --dry-run
echo ""
echo "Complete! Review the output above."
