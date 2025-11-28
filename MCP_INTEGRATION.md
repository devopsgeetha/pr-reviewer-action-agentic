# MCP Filesystem Integration

## Overview
Added Model Context Protocol (MCP) Filesystem support to improve file operations in the PR reviewer action.

## Changes Made

### 1. Dependencies (`backend/requirements.txt`)
- Added `mcp>=1.0.0` package for MCP client support

### 2. New Service (`backend/app/services/mcp_filesystem.py`)
Created MCP Filesystem client with:
- **Async file operations**: `read_file()`, `list_directory()`, `search_files()`, `get_file_info()`
- **Fallback mechanism**: Falls back to direct filesystem access if MCP fails
- **Environment-based toggle**: Enabled via `MCP_FILESYSTEM_ENABLED=true`

### 3. Updated Agent Tools (`backend/app/services/agent_tools.py`)
Modified tools to use MCP filesystem:
- **`get_file_content`**: Tries MCP first, falls back to GitHub API
- **`search_codebase`**: Uses MCP for faster local searches
- Added `mcp_filesystem` parameter to `AgentTools.__init__()`

### 4. Updated Agentic Agent (`backend/app/services/agentic_agent.py`)
- Initializes `MCPFilesystemClient` on startup
- Passes MCP client to `AgentTools`
- Gracefully handles MCP initialization failures

### 5. Updated Dockerfile (`Dockerfile.action`)
- Added Node.js 20.x installation
- Required for running MCP filesystem server
- Updated version comment to v1.0.2

### 6. Updated Entrypoint (`action-entrypoint.sh`)
- Sets `MCP_FILESYSTEM_ENABLED=true` environment variable
- Enables MCP filesystem for all file operations

## Benefits

✅ **Faster file operations** - MCP caching improves performance
✅ **Zero cost** - Runs locally in GitHub Actions container
✅ **Backward compatible** - Falls back to GitHub API if MCP fails
✅ **Easy toggle** - Can be disabled via environment variable

## How It Works

1. **GitHub Action starts** → Entrypoint sets `MCP_FILESYSTEM_ENABLED=true`
2. **Agent initializes** → Creates `MCPFilesystemClient` instance
3. **File operations** → Agent tools try MCP first, fallback to GitHub API
4. **MCP server** → Runs via `npx @modelcontextprotocol/server-filesystem` when needed

## Testing

The integration includes automatic fallback, so it's safe to deploy:
- If MCP fails, operations continue via GitHub API
- No breaking changes to existing functionality
- Can be tested locally with `MCP_FILESYSTEM_ENABLED=true`

## Future Enhancements

- Add Memory MCP server for persistent agent memory
- Add caching layer for frequently accessed files
- Metrics/logging for MCP vs API performance comparison
