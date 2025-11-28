"""
MCP Filesystem Client Service
Provides file operations through the Model Context Protocol filesystem server
"""
import os
import json
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPFilesystemClient:
    """Client for MCP Filesystem Server"""
    
    def __init__(self, root_path: str = None):
        """
        Initialize MCP Filesystem client
        
        Args:
            root_path: Root path for filesystem operations (defaults to /github/workspace in Actions)
        """
        self.root_path = root_path or os.getenv('GITHUB_WORKSPACE', '/github/workspace')
        self.session: Optional[ClientSession] = None
        self.enabled = os.getenv('MCP_FILESYSTEM_ENABLED', 'false').lower() == 'true'
        
        if self.enabled:
            self._connect()
    
    def _connect(self):
        """Connect to MCP filesystem server"""
        try:
            # MCP filesystem server should be running on stdio
            # Started by action-entrypoint.sh
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", self.root_path],
                env=None
            )
            
            # Create client session
            self.session = ClientSession(server_params)
            print(f"✅ Connected to MCP Filesystem Server (root: {self.root_path})")
        except Exception as e:
            print(f"⚠️  Could not connect to MCP Filesystem Server: {e}")
            print("   Falling back to direct file operations")
            self.enabled = False
            self.session = None
    
    async def read_file(self, file_path: str) -> Optional[str]:
        """
        Read file contents using MCP
        
        Args:
            file_path: Relative path to file from root
            
        Returns:
            File contents or None if error
        """
        if not self.enabled or not self.session:
            return self._fallback_read_file(file_path)
        
        try:
            # Use MCP read_file tool
            result = await self.session.call_tool(
                "read_file",
                arguments={"path": file_path}
            )
            return result.get("content", "")
        except Exception as e:
            print(f"MCP read_file error: {e}, falling back")
            return self._fallback_read_file(file_path)
    
    async def list_directory(self, dir_path: str = ".") -> List[Dict[str, Any]]:
        """
        List directory contents using MCP
        
        Args:
            dir_path: Relative path to directory
            
        Returns:
            List of file/directory entries
        """
        if not self.enabled or not self.session:
            return self._fallback_list_directory(dir_path)
        
        try:
            result = await self.session.call_tool(
                "list_directory",
                arguments={"path": dir_path}
            )
            return result.get("entries", [])
        except Exception as e:
            print(f"MCP list_directory error: {e}, falling back")
            return self._fallback_list_directory(dir_path)
    
    async def search_files(self, pattern: str, path: str = ".") -> List[str]:
        """
        Search for files matching pattern using MCP
        
        Args:
            pattern: Search pattern (regex or glob)
            path: Starting path for search
            
        Returns:
            List of matching file paths
        """
        if not self.enabled or not self.session:
            return self._fallback_search_files(pattern, path)
        
        try:
            result = await self.session.call_tool(
                "search_files",
                arguments={"pattern": pattern, "path": path}
            )
            return result.get("files", [])
        except Exception as e:
            print(f"MCP search_files error: {e}, falling back")
            return self._fallback_search_files(pattern, path)
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata using MCP
        
        Args:
            file_path: Relative path to file
            
        Returns:
            File metadata dict
        """
        if not self.enabled or not self.session:
            return self._fallback_get_file_info(file_path)
        
        try:
            result = await self.session.call_tool(
                "get_file_info",
                arguments={"path": file_path}
            )
            return result
        except Exception as e:
            print(f"MCP get_file_info error: {e}, falling back")
            return self._fallback_get_file_info(file_path)
    
    # Fallback methods using direct filesystem access
    
    def _fallback_read_file(self, file_path: str) -> Optional[str]:
        """Fallback: Read file directly"""
        try:
            full_path = os.path.join(self.root_path, file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def _fallback_list_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """Fallback: List directory directly"""
        try:
            full_path = os.path.join(self.root_path, dir_path)
            entries = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                entries.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "path": os.path.join(dir_path, item)
                })
            return entries
        except Exception as e:
            print(f"Error listing directory {dir_path}: {e}")
            return []
    
    def _fallback_search_files(self, pattern: str, path: str) -> List[str]:
        """Fallback: Search files directly"""
        import re
        import glob
        
        try:
            full_path = os.path.join(self.root_path, path)
            # Try glob pattern first
            if '*' in pattern or '?' in pattern:
                matches = glob.glob(os.path.join(full_path, pattern), recursive=True)
                return [os.path.relpath(m, self.root_path) for m in matches]
            
            # Otherwise use regex search
            regex = re.compile(pattern)
            matches = []
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    if regex.search(file):
                        file_path = os.path.join(root, file)
                        matches.append(os.path.relpath(file_path, self.root_path))
            return matches
        except Exception as e:
            print(f"Error searching files: {e}")
            return []
    
    def _fallback_get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Fallback: Get file info directly"""
        try:
            full_path = os.path.join(self.root_path, file_path)
            stat = os.stat(full_path)
            return {
                "path": file_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_directory": os.path.isdir(full_path),
                "exists": True
            }
        except Exception as e:
            return {"path": file_path, "exists": False, "error": str(e)}
    
    def close(self):
        """Close MCP connection"""
        if self.session:
            try:
                # Close session if needed
                pass
            except Exception as e:
                print(f"Error closing MCP session: {e}")
