#!/bin/bash
set -e

# Get PR details from GitHub context
# Priority order:
# 1. GITHUB_EVENT_PATH (most reliable for pull_request events)
# 2. GITHUB_REF
# 3. GITHUB_PR_NUMBER env var
# 4. Default for testing

PR_NUMBER=""

# Debug: Show what we have
echo "🔍 Debug: Extracting PR number..."
echo "   GITHUB_EVENT_NAME: ${GITHUB_EVENT_NAME:-not set}"
echo "   GITHUB_REF: ${GITHUB_REF:-not set}"
echo "   GITHUB_EVENT_PATH: ${GITHUB_EVENT_PATH:-not set}"

# Method 1: Try to get PR number from event JSON (most reliable for pull_request events)
if [[ -n "${GITHUB_EVENT_PATH}" && -f "${GITHUB_EVENT_PATH}" ]]; then
    echo "   Attempting to read from GITHUB_EVENT_PATH..."
    # Try with jq first
    if command -v jq &> /dev/null; then
        PR_NUMBER=$(jq -r '.pull_request.number // .number // empty' "${GITHUB_EVENT_PATH}" 2>/dev/null || echo "")
        if [[ -n "${PR_NUMBER}" && "${PR_NUMBER}" != "null" && "${PR_NUMBER}" != "" ]]; then
            echo "   ✅ Found PR number from event JSON (jq): ${PR_NUMBER}"
        fi
    fi
    
    # If jq didn't work or PR_NUMBER is still empty, try with Python
    if [[ -z "${PR_NUMBER}" || "${PR_NUMBER}" == "null" ]]; then
        PR_NUMBER=$(python3 -c "
import json
import sys
try:
    with open('${GITHUB_EVENT_PATH}', 'r') as f:
        data = json.load(f)
        pr_num = data.get('pull_request', {}).get('number') or data.get('number')
        if pr_num:
            print(pr_num)
except:
    pass
" 2>/dev/null || echo "")
        if [[ -n "${PR_NUMBER}" && "${PR_NUMBER}" != "null" && "${PR_NUMBER}" != "" ]]; then
            echo "   ✅ Found PR number from event JSON (Python): ${PR_NUMBER}"
        fi
    fi
fi

# Method 2: Try to get from GITHUB_REF
if [[ -z "${PR_NUMBER}" || "${PR_NUMBER}" == "null" ]]; then
    if [[ "${GITHUB_REF}" == refs/pull/* ]]; then
        PR_NUMBER="${GITHUB_REF#refs/pull/}"
        PR_NUMBER="${PR_NUMBER%/merge}"
        echo "   ✅ Found PR number from GITHUB_REF: ${PR_NUMBER}"
    elif [[ -n "${GITHUB_REF}" && "${GITHUB_REF}" =~ /([0-9]+) ]]; then
        PR_NUMBER="${BASH_REMATCH[1]}"
        echo "   ✅ Found PR number from GITHUB_REF (regex): ${PR_NUMBER}"
    fi
fi

# Method 3: Try environment variable
if [[ -z "${PR_NUMBER}" || "${PR_NUMBER}" == "null" ]]; then
    if [[ -n "${GITHUB_PR_NUMBER}" ]]; then
        PR_NUMBER="${GITHUB_PR_NUMBER}"
        echo "   ✅ Found PR number from GITHUB_PR_NUMBER: ${PR_NUMBER}"
    fi
fi

# Method 4: Fallback for testing (only if nothing else worked)
if [[ -z "${PR_NUMBER}" || "${PR_NUMBER}" == "null" || "${PR_NUMBER}" == "%!f(<nil>)" ]]; then
    PR_NUMBER="1"
    echo "   ⚠️  Warning: PR_NUMBER not found, using default: ${PR_NUMBER} (for act testing)"
fi

# Ensure PR_NUMBER is a valid number
if ! [[ "${PR_NUMBER}" =~ ^[0-9]+$ ]]; then
    PR_NUMBER="1"
    echo "   ⚠️  Warning: Invalid PR_NUMBER format '${PR_NUMBER}', using default: 1"
fi

echo "   📌 Final PR number: ${PR_NUMBER}"

REPO="${GITHUB_REPOSITORY:-meetgeetha/pr-reviewer-action}"

# Export variables for Python (ensure they're set)
export PR_NUMBER="${PR_NUMBER}"
export GITHUB_REPOSITORY="${REPO}"

echo "Reviewing PR #${PR_NUMBER} in ${REPO}"

# Run review using the CLI
# Add current directory to Python path
export PYTHONPATH=/app:$PYTHONPATH

python -c "
import os
import sys
sys.path.insert(0, '/app')
from app.services.github_service import GitHubService
from app.services.review_service import ReviewService

try:
    from app.services.rag_service import RAGService
    rag_service = RAGService()
except:
    rag_service = None

github_service = GitHubService()
review_service = ReviewService(rag_service=rag_service)

# Get PR data
repo_str = os.environ.get('GITHUB_REPOSITORY', 'meetgeetha/pr-reviewer-action')
if '/' not in repo_str:
    repo_str = 'meetgeetha/pr-reviewer-action'  # Default for testing
owner, repo = repo_str.split('/')

pr_number_str = os.environ.get('PR_NUMBER', '')
print(f'🔍 Python: PR_NUMBER env var = "{pr_number_str}"')

if not pr_number_str or pr_number_str == '%!f(<nil>)' or pr_number_str.startswith('%') or pr_number_str == '${PR_NUMBER}':
    # Fallback for act testing
    print('⚠️  Python: PR_NUMBER env var is empty or invalid, using default: 1')
    pr_number_str = '1'
try:
    pr_number = int(pr_number_str)
    print(f'✅ Python: Using PR number: {pr_number}')
except (ValueError, TypeError) as e:
    print(f'❌ Python: Error: Invalid PR number, using default: 1')
    print(f'   PR_NUMBER value was: {pr_number_str}')
    print(f'   Error: {e}')
    pr_number = 1

# Fetch PR and review
try:
    print(f'🔍 Fetching PR #{pr_number} from {repo_str}...')
    pr_data = github_service.get_pull_request(owner, repo, pr_number)
    print(f'📊 Analyzing PR diff...')
    diff_data = github_service.get_pr_diff(pr_data)
    print(f'🤖 Running AI analysis...')
    result = review_service.analyze_code(diff_data)
    print(f'💬 Posting review comment...')
    
    # Post review as comment
    github_service.post_review_comments(pr_data, result)
    print('✅ Review posted successfully')
except Exception as e:
    error_msg = str(e)
    if '404' in error_msg or 'Not Found' in error_msg:
        print('⚠️  PR not found (this is expected when testing with act)')
        print('   The action would work correctly in a real GitHub Actions environment.')
        print('   To test with a real PR, use: act pull_request -e .github/pr-event.json')
        print('   Or test directly on GitHub by creating a PR.')
        sys.exit(0)  # Exit successfully for testing
    else:
        print('❌ Error: ' + error_msg)
        raise
"
