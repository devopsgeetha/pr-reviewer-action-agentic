# AI PR Reviewer - GitHub Action

Automated code review using GPT-4 with **Agentic AI** and RAG-enhanced context for smarter, more consistent reviews.

## Features

- 🤖 **Agentic AI**: Autonomous agent that plans, reasons, and makes decisions
- 🧠 **RAG Enhancement**: Learns from past reviews and best practices
- 🔧 **Tool-Based Analysis**: Uses specialized tools for security, dependencies, and code quality
- 🔍 **Comprehensive Analysis**: Checks for bugs, security, performance, and style
- 📊 **Detailed Feedback**: Provides actionable suggestions with severity levels
- 🔄 **Iterative Reasoning**: Refines analysis through multiple reasoning steps
- 📝 **Transparent**: Full reasoning chain showing agent decisions
- ⚡ **Fast**: ~70ms overhead with local embeddings

## Usage

### Advanced Usage (AGENTIC_AI Branch)

For the latest agentic AI features, use the `AGENTIC_AI` branch:

```yaml
name: AI Code Review (Agentic)
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - name: Checkout PR code
        uses: actions/checkout@v3
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          repository: ${{ github.event.pull_request.head.repo.full_name }}
          fetch-depth: 0
      
      - name: AI PR Review (Agentic)
        uses: meetgeetha/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_model: gpt-4-turbo-preview  # Recommended for agentic mode
```

> **Note**: The `AGENTIC_AI` branch contains the latest agentic AI features. For a stable release, use the `agentic_ai_v2` tag or the `main` branch.

### Using a Specific Version

```yaml
- name: AI PR Review
  uses: meetgeetha/pr-reviewer-action@main        # stable branch
# or:
  uses: meetgeetha/pr-reviewer-action@AGENTIC_AI  # latest agentic branch
# or:
  uses: meetgeetha/pr-reviewer-action@agentic_ai_v2  # agentic release tag
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    openai_model: gpt-4-turbo-preview
```

## Setup

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Add it to your repository secrets as `OPENAI_API_KEY`
3. Add the workflow file above (make sure to include the `permissions` block!)
4. Create a PR and watch the magic happen! ✨

**Important**: 
- The `permissions` block is required for the action to post comments on PRs. Without it, you'll get a 403 "Resource not accessible by integration" error.
- For **Agentic AI mode**, use a model that supports function calling (gpt-4, gpt-4-turbo-preview, gpt-4-turbo). The system will automatically use agentic mode when `OPENAI_API_KEY` is set.

## Troubleshooting

### 403 Forbidden Error

If you're getting a 403 error when the action tries to post comments:

1. **Check your workflow file has permissions**: Make sure your workflow includes the `permissions` block as shown in the example above.

2. **Verify the permissions are correct**: The job needs:
   ```yaml
   permissions:
     issues: write
     pull-requests: read
   ```

3. **Fork PRs**: If the PR is from a fork, `GITHUB_TOKEN` has limited permissions. You may need to use a Personal Access Token (PAT) with `repo` scope instead:
   ```yaml
   - name: AI PR Review
     uses: meetgeetha/pr-reviewer-action@main
     with:
       openai_api_key: ${{ secrets.OPENAI_API_KEY }}
       github_token: ${{ secrets.PAT_TOKEN }}  # Use PAT instead of GITHUB_TOKEN
   ```

4. **Repository settings**: Check that your repository allows GitHub Actions to write to issues/comments in Settings → Actions → General → Workflow permissions.

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `openai_api_key` | Yes | - | OpenAI API key for GPT-4 |
| `github_token` | No | `${{ github.token }}` | GitHub token for API access |
| `openai_model` | No | `gpt-4-turbo-preview` | OpenAI model to use (use gpt-4 or gpt-4-turbo for agentic mode) |
| `comment_mode` | No | `inline` | Comment mode: `inline` for line-specific review comments, `general` for single issue comment |

## Agentic AI Features

When using the `AGENTIC_AI` branch (or the `agentic_ai_v2` release tag), the action automatically:

- **Plans** the review strategy based on PR changes
- **Uses Tools** for specialized analysis (security, dependencies, code style)
- **Reasons Iteratively** through multiple steps
- **Learns** from past reviews using RAG
- **Provides Transparency** with full reasoning chain

The agentic system includes 9 specialized tools:
- Code file analysis
- Dependency security checks
- Security pattern scanning
- Code style validation
- Related file discovery
- Codebase pattern search
- Past review retrieval
- Issue prioritization
- And more...

The agentic agent automatically activates when using gpt-4 or gpt-4-turbo models.

## Comment Modes

### Inline Comments (Default)

When `comment_mode: inline` (default), the action posts **line-specific review comments** directly on the code changes in your PR. This creates a more interactive experience where each issue is highlighted exactly where it occurs in the code.

**Requirements for inline comments:**
```yaml
permissions:
  pull-requests: write  # Required for inline comments
  contents: read
```

**Example inline comment on line 42:**
```diff
function authenticateUser(username, password) {
+   const jwt = "hardcoded-secret-key";  // 🔴 HIGH: JWT secret is hardcoded
    return generateToken(jwt, username);
}
```

### General Comments

When `comment_mode: general`, the action posts a **single comprehensive comment** on the PR with all findings summarized in one place.

**Requirements for general comments:**
```yaml
permissions:
  issues: write  # Required for general comments
  contents: read
```

The action automatically falls back to general comments if inline comments fail due to permissions.

## Example Review Output

The action will post a comment on your PR with:

- **Overall Score**: Code quality rating
- **Issues Found**: Categorized by severity (high/medium/low)
- **Suggestions**: Actionable improvements
- **AI Summary**: High-level review insights

## Local Testing

There are several ways to test this action locally before deploying:

### Method 1: Using Act (Recommended for GitHub Actions Testing)

[Act](https://github.com/nektos/act) is a tool that runs GitHub Actions locally using Docker.

1. **Install Act**:
   ```bash
   # Windows (using winget)
   winget install nektos.act
   
   # Mac (using Homebrew)
   brew install act
   
   # Linux (using the install script)
   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

2. **Create a test PR event file** (`.github/pr-event.json`):
   ```json
   {
     "action": "opened",
     "pull_request": {
       "number": 1,
       "head": {
         "sha": "abc123",
         "repo": {
           "full_name": "owner/repo"
         }
       },
       "base": {
         "repo": {
           "full_name": "owner/repo"
         }
       }
     },
     "repository": {
       "full_name": "owner/repo"
     }
   }
   ```

3. **Run the action with act**:
   ```bash
   act pull_request \
     -W .github/workflows/test-action.yml \
     -e .github/pr-event.json \
     -s OPENAI_API_KEY=your-openai-key \
     -s GITHUB_TOKEN=your-github-token \
     --container-architecture linux/amd64
   ```

   **Note**: For Windows users, use WSL for best compatibility. Docker must be running.

### Method 2: Direct Docker Testing

Test the Docker container directly without GitHub Actions:

1. **Build the Docker image**:
   ```bash
   docker build -f Dockerfile.action -t pr-reviewer-action .
   ```

2. **Run with environment variables**:
   ```bash
   docker run --rm \
     -e OPENAI_API_KEY=your-openai-key \
     -e GITHUB_TOKEN=your-github-token \
     -e OPENAI_MODEL=gpt-4-turbo-preview \
     -e PR_NUMBER=1 \
     -e GITHUB_REPOSITORY=owner/repo \
     pr-reviewer-action
   ```

### Method 3: Testing the Backend Directly (Python)

For development and debugging, you can run the backend Python code directly:

1. **Set up the environment**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-openai-key"
   $env:GITHUB_TOKEN="your-github-token"
   $env:OPENAI_MODEL="gpt-4-turbo-preview"
   $env:PR_NUMBER="1"
   $env:GITHUB_REPOSITORY="owner/repo"
   
   # Linux/Mac
   export OPENAI_API_KEY="your-openai-key"
   export GITHUB_TOKEN="your-github-token"
   export OPENAI_MODEL="gpt-4-turbo-preview"
   export PR_NUMBER="1"
   export GITHUB_REPOSITORY="owner/repo"
   ```

3. **Test OpenAI connection**:
   ```bash
   # Make sure backend/.env is configured with OPENAI_API_KEY
   ./test-openai-connection.sh
   ```
   
   This will test:
   - OpenAI API connectivity
   - Python imports
   - LLM service initialization
   - Code analysis functionality

### Method 4: Testing with Unit Tests

Run the existing test suite:

```bash
cd backend
pytest tests/ -v
```

### Tips for Local Testing

- **Use a test repository**: Create a test repository with a simple PR to avoid affecting real projects
- **Mock API calls**: For faster iteration, consider mocking GitHub API calls in unit tests
- **Check logs**: The action provides detailed debug output - check console logs for troubleshooting
- **Test with real PRs**: For final validation, test with an actual PR in a test repository

## Self-Hosting

Want to run your own instance? You can build and run the Docker container locally:

```bash
docker build -f Dockerfile.action -t pr-reviewer-action .
docker run -e OPENAI_API_KEY=your-key -e GITHUB_TOKEN=your-token pr-reviewer-action
```

## License

MIT
