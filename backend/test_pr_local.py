"""
Local test script for PR reviewer
Run with: python test_pr_local.py
"""
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
from app.services.github_service import GitHubService
from app.services.review_service import ReviewService

# Load environment variables
load_dotenv()

try:
    from app.services.rag_service import RAGService
    rag_service = RAGService()
except Exception as e:
    print(f'Warning: RAG not available: {e}')
    rag_service = None

# Initialize services
github_service = GitHubService()
review_service = ReviewService(rag_service=rag_service)

# Get PR data from environment
repo = os.environ.get('GITHUB_REPOSITORY', 'meetgeetha/pr-reviewer-action')
owner, repo_name = repo.split('/')
pr_number = int(os.environ.get('PR_NUMBER', '5'))

print(f'📥 Fetching PR #{pr_number} from {owner}/{repo_name}...')
pr_data = github_service.get_pull_request(owner, repo_name, pr_number)

print(f'📊 Getting PR diff...')
diff_data = github_service.get_pr_diff(pr_data)

print(f'🤖 Analyzing code...')
result = review_service.analyze_code(diff_data)

print(f'\n✅ Review completed!')
print(f'\nSummary: {result.get("summary", "No summary")}')
print(f'Issues found: {len(result.get("issues", []))}')
print(f'Suggestions: {len(result.get("suggestions", []))}')
print(f'Overall Score: {result.get("overall_score", 0)}/100')

# Optionally post comment (set POST_COMMENT=true to actually post)
if os.environ.get('POST_COMMENT', '').lower() == 'true':
    print(f'\n💬 Posting review comment...')
    github_service.post_review_comments(pr_data, result)
    print(f'✅ Comment posted!')
else:
    print(f'\nℹ️  Set POST_COMMENT=true to post the comment to GitHub')
