# Agentic AI System for PR Reviewer

This PR Reviewer has been enhanced with **Agentic AI** capabilities, transforming it from a simple reactive system into an autonomous agent that can plan, reason, and make decisions.

## What is Agentic AI?

Agentic AI refers to AI systems that can:
- **Plan**: Create strategies and decide what actions to take
- **Use Tools**: Call functions to gather information and perform analysis
- **Reason**: Think through problems step-by-step
- **Iterate**: Refine their approach based on findings
- **Learn**: Adapt from past reviews and feedback

## Key Features

### 1. **Autonomous Planning**
The agent analyzes the PR and creates a review plan, deciding:
- Which files need deep analysis
- What security checks are necessary
- Whether to check dependencies
- When to search for similar patterns

### 2. **Tool-Based Analysis**
The agent has access to multiple tools:

- **`analyze_code_file`**: Deep analysis of specific files
- **`get_file_content`**: Get full file contents for context
- **`check_dependencies`**: Analyze package dependencies for security
- **`analyze_security_patterns`**: Security vulnerability scanning
- **`check_code_style`**: Code style and best practices
- **`get_related_files`**: Find related files
- **`search_codebase`**: Search for patterns
- **`get_past_reviews`**: Learn from past reviews
- **`prioritize_issues`**: Organize and prioritize findings

### 3. **Iterative Reasoning**
The agent uses a reasoning loop:
1. **Planning Phase**: Understands the PR scope
2. **Analysis Phase**: Uses tools to gather information
3. **Review Phase**: Synthesizes findings
4. **Finalization**: Compiles comprehensive review

### 4. **Memory & State Management**
The agent tracks:
- All steps taken during review
- Tools used and their results
- Decisions made
- Files analyzed
- Issues found

This creates a transparent reasoning chain that can be reviewed.

### 5. **Intelligent Decision Making**
The agent decides:
- When to use which tool
- How deep to analyze each file
- When it has enough information to finalize
- What issues are most critical

## Architecture

```
┌─────────────────────────────────────────┐
│         AgenticAgent                     │
│  - Planning & Execution Loop            │
│  - Tool Orchestration                   │
│  - Decision Making                      │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│ AgentTools  │  │AgentMemory  │
│ - Tool Defs │  │ - State Mgmt│
│ - Execution │  │ - History   │
└─────────────┘  └─────────────┘
       │
       ├──► analyze_code_file
       ├──► check_dependencies
       ├──► analyze_security_patterns
       ├──► get_file_content
       └──► ... (9 tools total)
```

## Usage

### Automatic (Default)
The system automatically uses agentic mode when `OPENAI_API_KEY` is set:

```python
from app.services.review_service import ReviewService

review_service = ReviewService(rag_service=rag_service, use_agentic=True)
review_result = review_service.analyze_code(diff_data, github_service=github_service)
```

### Manual Control
You can explicitly enable/disable agentic mode:

```python
# Enable agentic mode
review_service = ReviewService(use_agentic=True)

# Disable (use traditional mode)
review_service = ReviewService(use_agentic=False)
```

### Environment Variables

```bash
# Required for agentic mode
OPENAI_API_KEY=sk-...

# Optional configuration
OPENAI_MODEL=gpt-4-turbo-preview  # Model to use
OPENAI_TEMPERATURE=0.3            # Temperature (0-1)
```

## Review Output

The agentic review includes additional information:

```json
{
  "pr_number": 123,
  "repository": "owner/repo",
  "summary": "...",
  "issues": [...],
  "suggestions": [...],
  "overall_score": 85,
  
  // Agentic-specific fields
  "agent_reasoning": [
    {
      "step_number": 1,
      "thought": "Analyzing PR scope...",
      "tool_used": null,
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "step_number": 2,
      "thought": "Using tool: analyze_code_file",
      "tool_used": "analyze_code_file",
      "tool_arguments": {...},
      "tool_result": {...}
    }
  ],
  "decisions_made": [
    "Focusing on security-critical files first",
    "Running dependency check for package.json changes"
  ],
  "files_analyzed": ["src/main.py", "package.json"],
  "review_summary": {
    "phase": "completed",
    "files_analyzed": 2,
    "issues_found": 5,
    "steps_taken": 8,
    "duration_seconds": 12.5
  }
}
```

## How It Works

### 1. Initialization
```python
agent = AgenticAgent(
    github_service=github_service,
    review_service=review_service,
    rag_service=rag_service
)
```

### 2. Review Process
```python
review_result = agent.review_pr(diff_data)
```

The agent:
1. **Plans**: Analyzes PR and creates strategy
2. **Executes**: Uses tools to gather information
3. **Reasons**: Processes findings and makes decisions
4. **Iterates**: Refines analysis based on discoveries
5. **Finalizes**: Compiles comprehensive review

### 3. Tool Execution
When the agent decides to use a tool:
- LLM generates function call
- Tool is executed with arguments
- Results are fed back to LLM
- Agent processes results and continues

### 4. Finalization
Agent determines when it has enough information:
- No more critical issues to investigate
- All important files analyzed
- Security checks completed
- Ready to compile final review

## Benefits

### vs. Traditional Approach

| Feature | Traditional | Agentic AI |
|---------|------------|------------|
| **Planning** | Fixed workflow | Adaptive planning |
| **Tool Use** | All tools always | Selective tool use |
| **Reasoning** | Single pass | Iterative refinement |
| **Context** | Limited | Rich, multi-step |
| **Transparency** | Basic | Full reasoning chain |
| **Efficiency** | Analyzes all files | Focuses on important |

### Key Advantages

1. **Smarter Analysis**: Focuses on what matters most
2. **Better Context**: Understands relationships between changes
3. **Adaptive**: Adjusts approach based on findings
4. **Transparent**: Shows reasoning process
5. **Efficient**: Doesn't waste time on trivial changes

## Configuration

### Max Iterations
Control how many reasoning steps the agent takes:

```python
agent = AgenticAgent(max_iterations=15)  # Default: 10
```

### Tool Selection
The agent automatically selects tools, but you can customize:

```python
# Tools are automatically available
# Agent decides when to use each one
```

## Troubleshooting

### Agent Not Using Tools
- Check that `OPENAI_API_KEY` is set
- Verify model supports function calling (gpt-4, gpt-4-turbo, etc.)
- Check logs for errors

### Fallback to Traditional Mode
If agentic mode fails, it automatically falls back to traditional analysis:
- No API key available
- Function calling errors
- Model doesn't support tools

### Performance
Agentic mode may take longer due to:
- Multiple LLM calls
- Tool execution
- Iterative reasoning

This is normal and results in better reviews.

## Future Enhancements

- [ ] Multi-agent collaboration
- [ ] Learning from feedback
- [ ] Custom tool definitions
- [ ] Parallel tool execution
- [ ] Advanced planning strategies
- [ ] Cost optimization

## Examples

### Simple PR Review
```python
# Agent automatically handles everything
review_result = review_service.analyze_code(diff_data, github_service=github_service)
```

### Custom Agent Configuration
```python
from app.services.agentic_agent import AgenticAgent

agent = AgenticAgent(
    github_service=github_service,
    review_service=review_service,
    rag_service=rag_service,
    max_iterations=20  # More thorough analysis
)

review_result = agent.review_pr(diff_data)
```

## See Also

- [README.md](README.md) - Main documentation
- [ACTION_README.md](ACTION_README.md) - GitHub Action usage
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

