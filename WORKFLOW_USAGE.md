# Using Agentic AI PR Reviewer in Your Workflow

This guide shows you how to use the Agentic AI PR Reviewer in your GitHub Actions workflow.

## Quick Start

### 1. Create Workflow File

Create `.github/workflows/pr-review.yml` in your repository:

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
          openai_model: gpt-4-turbo-preview
```

### 2. Add OpenAI API Key

1. Go to your repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `OPENAI_API_KEY`
4. Value: Your OpenAI API key (starts with `sk-`)
5. Click **Add secret**

### 3. Create a Pull Request

That's it! The agentic AI will automatically review your PR.

## Configuration Options

### Using Different Branches/Versions

```yaml
# Use the AGENTIC_AI branch (latest agentic features)
uses: yourusername/pr-reviewer-action@AGENTIC_AI

# Use a specific version tag
uses: yourusername/pr-reviewer-action@v1.0.0

# Use main branch
uses: yourusername/pr-reviewer-action@main
```

### Model Selection

For **Agentic AI mode**, use models that support function calling:

```yaml
# Recommended for agentic mode
openai_model: gpt-4-turbo-preview  # Best balance of quality and speed
openai_model: gpt-4                # Highest quality, slower
openai_model: gpt-4-turbo          # Fast and capable
```

**Note**: Agentic mode requires function calling support. Models like `gpt-3.5-turbo` may fall back to traditional mode.

### Minimal Configuration

```yaml
- name: AI PR Review
  uses: yourusername/pr-reviewer-action@AGENTIC_AI
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    # github_token defaults to ${{ github.token }}
    # openai_model defaults to gpt-4-turbo-preview
```

## Advanced Usage

### Custom Permissions

If you need additional permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
  checks: write  # If you want to create check runs
```

### Fork PRs

For PRs from forks, you may need a Personal Access Token (PAT):

```yaml
- name: AI PR Review
  uses: yourusername/pr-reviewer-action@AGENTIC_AI
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.PAT_TOKEN }}  # PAT with repo scope
```

### Multiple Review Jobs

Review different aspects in parallel:

```yaml
jobs:
  security-review:
    runs-on: ubuntu-latest
    steps:
      - name: Security Review
        uses: yourusername/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          openai_model: gpt-4  # Use more capable model for security
  
  code-quality-review:
    runs-on: ubuntu-latest
    steps:
      - name: Code Quality Review
        uses: yourusername/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          openai_model: gpt-4-turbo-preview
```

## What the Agentic AI Does

When you create a PR, the agentic AI:

1. **Plans**: Analyzes the PR and creates a review strategy
2. **Uses Tools**: 
   - Analyzes code files for bugs and issues
   - Checks dependencies for security vulnerabilities
   - Scans for security patterns
   - Validates code style
   - Searches for related files
   - Retrieves past reviews for consistency
3. **Reasons**: Iteratively refines findings through multiple steps
4. **Finalizes**: Compiles comprehensive review with reasoning chain

## Review Output

The agentic AI posts a comment on your PR with:

- **Overall Score**: Code quality rating (0-100)
- **Summary**: High-level review insights
- **Issues Found**: Categorized by severity:
  - 🔴 High Priority: Critical bugs, security issues
  - 🟡 Medium Priority: Code quality, best practices
  - 🔵 Low Priority: Style, minor improvements
- **Suggestions**: Actionable improvements
- **Reasoning Chain**: (In agentic mode) Full transparency of agent decisions

## Troubleshooting

### 403 Forbidden Error

**Problem**: Action can't post comments

**Solution**: Add permissions block:

```yaml
permissions:
  pull-requests: write
  issues: write
```

### Agentic Mode Not Working

**Problem**: Falls back to traditional mode

**Solutions**:
1. Check that `OPENAI_API_KEY` is set correctly
2. Use a model that supports function calling (gpt-4, gpt-4-turbo)
3. Check action logs for errors

### No Review Posted

**Possible Causes**:
- PR is from a fork (use PAT token)
- Permissions not set correctly
- API key invalid or expired
- Model doesn't support function calling

**Check**: Look at the action logs for error messages

## Example Workflows

### Basic Workflow

```yaml
name: Code Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      issues: write
    steps:
      - uses: yourusername/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

### With Checkout Step

```yaml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v3
      - uses: yourusername/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          openai_model: gpt-4-turbo-preview
```

### Multiple Triggers

```yaml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
  pull_request_target:
    types: [opened]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      issues: write
    steps:
      - uses: yourusername/pr-reviewer-action@AGENTIC_AI
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

## Best Practices

1. **Use Appropriate Model**: 
   - `gpt-4-turbo-preview` for most cases (good balance)
   - `gpt-4` for critical security reviews
   - `gpt-3.5-turbo` for simple reviews (may not use agentic mode)

2. **Set Permissions**: Always include the permissions block

3. **Checkout Code**: Include checkout step if you need file access

4. **Monitor Costs**: Agentic mode uses more tokens due to multiple reasoning steps

5. **Review Logs**: Check action logs to see agent reasoning

## Cost Considerations

Agentic mode uses more API calls than traditional mode:
- Multiple reasoning steps
- Tool execution
- Iterative refinement

**Estimated costs** (varies by PR size):
- Small PR (< 100 lines): ~$0.10-0.30
- Medium PR (100-500 lines): ~$0.30-1.00
- Large PR (> 500 lines): ~$1.00-3.00

## See Also

- [AGENTIC_AI.md](AGENTIC_AI.md) - Complete agentic AI documentation
- [ACTION_README.md](ACTION_README.md) - Action reference
- [README.md](README.md) - Main documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

