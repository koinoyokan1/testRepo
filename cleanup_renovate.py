#!/usr/bin/env python3
"""
Clean up all Renovate-related PRs, issues, and branches to start fresh.
Requires: pip install requests (or use urllib from stdlib)
"""

import os
import sys
import json

try:
    import requests
except ImportError:
    print("❌ Error: requests library not found")
    print("Install with: pip install requests")
    print("Or use the bash script: ./cleanup_renovate.sh")
    sys.exit(1)

REPO_OWNER = "koinoyokan1"
REPO_NAME = "testRepo"
REPO = f"{REPO_OWNER}/{REPO_NAME}"
API_BASE = f"https://api.github.com/repos/{REPO}"

def get_github_token():
    """Get GitHub token from environment"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("Get a token from: https://github.com/settings/tokens")
        print("Then: export GITHUB_TOKEN=your_token_here")
        sys.exit(1)
    return token

def github_request(method, endpoint, data=None):
    """Make a GitHub API request"""
    token = get_github_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"{API_BASE}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    return response

def cleanup_prs():
    """Close all PRs and delete their branches"""
    print("1️⃣ Fetching all PRs...")
    response = github_request("GET", "/pulls?state=all&per_page=100")
    
    if response.status_code != 200:
        print(f"  ❌ Error fetching PRs: {response.status_code}")
        return
    
    prs = response.json()
    
    if not prs:
        print("  No PRs found")
        return
    
    print(f"  Found {len(prs)} PRs")
    
    for pr in prs:
        pr_num = pr['number']
        pr_title = pr['title']
        pr_state = pr['state']
        branch = pr['head']['ref']
        
        print(f"  - PR #{pr_num}: {pr_title}")
        
        # Close PR if open
        if pr_state == 'open':
            print(f"    Closing PR #{pr_num}...")
            github_request("PATCH", f"/pulls/{pr_num}", {"state": "closed"})
        
        # Delete branch
        if branch != 'main':
            print(f"    Deleting branch: {branch}")
            response = github_request("DELETE", f"/git/refs/heads/{branch}")
            if response.status_code not in [204, 404]:
                print(f"      Warning: Failed to delete branch (status {response.status_code})")

def cleanup_issues():
    """Close all issues (excluding PRs)"""
    print("\n2️⃣ Fetching all issues...")
    response = github_request("GET", "/issues?state=all&per_page=100")
    
    if response.status_code != 200:
        print(f"  ❌ Error fetching issues: {response.status_code}")
        return
    
    issues = response.json()
    
    # Filter out PRs (GitHub API returns PRs as issues too)
    actual_issues = [i for i in issues if 'pull_request' not in i]
    
    if not actual_issues:
        print("  No issues found")
        return
    
    print(f"  Found {len(actual_issues)} issues")
    
    for issue in actual_issues:
        issue_num = issue['number']
        issue_title = issue['title']
        issue_state = issue['state']
        
        print(f"  - Issue #{issue_num}: {issue_title}")
        
        # Close issue if open
        if issue_state == 'open':
            print(f"    Closing issue #{issue_num}...")
            github_request("PATCH", f"/issues/{issue_num}", {"state": "closed"})

def main():
    print(f"🧹 Cleaning up Renovate artifacts for {REPO}...\n")
    
    try:
        cleanup_prs()
        cleanup_issues()
        
        print("\n✅ Cleanup complete!\n")
        print("Next steps:")
        print("  1. Manually trigger the Renovate workflow in GitHub Actions")
        print("  2. Or wait for the next hourly run")
        print("  3. Renovate will create fresh PRs based on your Black Duck findings")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
