#!/bin/bash

# Script to clean up all Renovate-related PRs, issues, and branches
# This will start fresh with Renovate

REPO_OWNER="koinoyokan1"
REPO_NAME="testRepo"
REPO="${REPO_OWNER}/${REPO_NAME}"

echo "🧹 Cleaning up Renovate artifacts for ${REPO}..."
echo ""

# Check if GitHub token is available
if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ Error: GITHUB_TOKEN environment variable not set"
  echo "Please set it with: export GITHUB_TOKEN=your_token_here"
  exit 1
fi

# Function to call GitHub API
github_api() {
  local method=$1
  local endpoint=$2
  local data=$3
  
  if [ -n "$data" ]; then
    curl -s -X "$method" \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      -d "$data" \
      "https://api.github.com/repos/${REPO}${endpoint}"
  else
    curl -s -X "$method" \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/${REPO}${endpoint}"
  fi
}

echo "1️⃣ Fetching all PRs..."
prs=$(github_api GET "/pulls?state=all&per_page=100")
pr_numbers=$(echo "$prs" | grep -o '"number": [0-9]*' | grep -o '[0-9]*')

if [ -n "$pr_numbers" ]; then
  echo "Found PRs: $pr_numbers"
  for pr in $pr_numbers; do
    pr_data=$(echo "$prs" | grep -A 20 "\"number\": $pr")
    pr_title=$(echo "$pr_data" | grep '"title"' | head -1 | cut -d'"' -f4)
    echo "  - PR #$pr: $pr_title"
    
    # Close PR if open
    state=$(echo "$pr_data" | grep '"state"' | head -1 | cut -d'"' -f4)
    if [ "$state" = "open" ]; then
      echo "    Closing PR #$pr..."
      github_api PATCH "/pulls/$pr" '{"state": "closed"}' > /dev/null
    fi
    
    # Delete the branch
    branch=$(echo "$pr_data" | grep '"ref"' | head -1 | cut -d'"' -f4)
    if [ -n "$branch" ] && [ "$branch" != "main" ]; then
      echo "    Deleting branch: $branch"
      github_api DELETE "/git/refs/heads/$branch" > /dev/null 2>&1
    fi
  done
else
  echo "  No PRs found"
fi
echo ""

echo "2️⃣ Fetching all issues..."
issues=$(github_api GET "/issues?state=all&per_page=100")
issue_numbers=$(echo "$issues" | grep -o '"number": [0-9]*' | grep -o '[0-9]*')

if [ -n "$issue_numbers" ]; then
  echo "Found issues: $issue_numbers"
  for issue in $issue_numbers; do
    issue_data=$(echo "$issues" | grep -A 10 "\"number\": $issue")
    issue_title=$(echo "$issue_data" | grep '"title"' | head -1 | cut -d'"' -f4)
    
    # Skip if it's a PR (PRs are also listed as issues in GitHub API)
    if echo "$issue_data" | grep -q '"pull_request"'; then
      continue
    fi
    
    echo "  - Issue #$issue: $issue_title"
    
    # Close issue if open
    state=$(echo "$issue_data" | grep '"state"' | head -1 | cut -d'"' -f4)
    if [ "$state" = "open" ]; then
      echo "    Closing issue #$issue..."
      github_api PATCH "/issues/$issue" '{"state": "closed"}' > /dev/null
    fi
  done
else
  echo "  No issues found"
fi
echo ""

echo "3️⃣ Deleting remaining Renovate branches..."
branches=$(git ls-remote --heads origin | grep -E '(renovate|blackduck)' | awk '{print $2}' | sed 's/refs\/heads\///')

if [ -n "$branches" ]; then
  echo "$branches" | while read -r branch; do
    echo "  Deleting branch: $branch"
    github_api DELETE "/git/refs/heads/$branch" > /dev/null 2>&1 || echo "    (already deleted or error)"
  done
else
  echo "  No Renovate branches found"
fi
echo ""

echo "✅ Cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Manually trigger the Renovate workflow in GitHub Actions"
echo "  2. Or wait for the next hourly run"
echo "  3. Renovate will create fresh PRs based on your Black Duck findings"
