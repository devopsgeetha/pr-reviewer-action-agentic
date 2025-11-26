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

### Basic Usage (Agentic AI - Recommended)

Add to your repository's `.github/workflows/pr-review.yml`:

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
        uses: yourusername/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_model: gpt-4-turbo-preview  # Recommended for agentic mode
```

### Using a Specific Version

```yaml
- name: AI PR Review
  uses: yourusername/pr-reviewer-action@v1  # or @main, @AGENTIC_AI
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
     uses: yourusername/pr-reviewer-action@v1
     with:
       openai_api_key: ${{ secrets.OPENAI_API_KEY }}
       github_token: ${{ secrets.PAT_TOKEN }}  # Use PAT instead of GITHUB_TOKEN
   ```

4. **Repository settings**: Check that your repository allows GitHub Actions to write to issues/comments in Settings → Actions → General → Workflow permissions.

For more detailed troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `openai_api_key` | Yes | - | OpenAI API key for GPT-4 |
| `github_token` | No | `${{ github.token }}` | GitHub token for API access |
| `openai_model` | No | `gpt-4-turbo-preview` | OpenAI model to use (use gpt-4 or gpt-4-turbo for agentic mode) |

## Agentic AI Features

When using the `AGENTIC_AI` branch or a version with agentic support, the action automatically:

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

See [AGENTIC_AI.md](../AGENTIC_AI.md) for complete documentation.

## Example Review Output

The action will post a comment on your PR with:

- **Overall Score**: Code quality rating
- **Issues Found**: Categorized by severity (high/medium/low)
- **Suggestions**: Actionable improvements
- **AI Summary**: High-level review insights

## Self-Hosting

Want to run your own instance? You can build and run the Docker container locally:

```bash
docker build -f Dockerfile.action -t pr-reviewer-action .
docker run -e OPENAI_API_KEY=your-key -e GITHUB_TOKEN=your-token pr-reviewer-action
```

## License

MIT
