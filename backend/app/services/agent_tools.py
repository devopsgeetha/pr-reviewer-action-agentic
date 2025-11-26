"""
Tool definitions for the agentic AI system.
These tools allow the agent to interact with the codebase and make decisions.
"""
from typing import Dict, Any, List, Optional
import json
import re
from dataclasses import dataclass


@dataclass
class Tool:
    """Represents a tool that the agent can use"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class AgentTools:
    """Collection of tools available to the agent"""
    
    def __init__(self, github_service=None, review_service=None, rag_service=None):
        self.github_service = github_service
        self.review_service = review_service
        self.rag_service = rag_service
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize all available tools"""
        tools = {}
        
        # Code analysis tools
        tools["analyze_code_file"] = Tool(
            name="analyze_code_file",
            description="Analyze a specific file from the PR for bugs, security issues, and code quality. Use this when you need to deeply examine a particular file.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to analyze"
                    },
                    "code": {
                        "type": "string",
                        "description": "The code content or diff to analyze"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, typescript, etc.)"
                    }
                },
                "required": ["filename", "code", "language"]
            },
            function=self._analyze_code_file
        )
        
        tools["get_file_content"] = Tool(
            name="get_file_content",
            description="Get the full content of a file from the repository. Use this to understand context or check related files.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The path to the file"
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name in format owner/repo"
                    }
                },
                "required": ["filename", "repo_name"]
            },
            function=self._get_file_content
        )
        
        tools["check_dependencies"] = Tool(
            name="check_dependencies",
            description="Check if new dependencies are added and analyze their security and compatibility. Use this when package files are modified.",
            parameters={
                "type": "object",
                "properties": {
                    "package_file": {
                        "type": "string",
                        "description": "Content of package file (requirements.txt, package.json, etc.)"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "Type of package file (requirements, package.json, pom.xml, etc.)"
                    }
                },
                "required": ["package_file", "file_type"]
            },
            function=self._check_dependencies
        )
        
        tools["analyze_security_patterns"] = Tool(
            name="analyze_security_patterns",
            description="Perform deep security analysis looking for common vulnerabilities like SQL injection, XSS, authentication issues, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze for security issues"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language"
                    }
                },
                "required": ["code", "language"]
            },
            function=self._analyze_security_patterns
        )
        
        tools["check_code_style"] = Tool(
            name="check_code_style",
            description="Check code style and adherence to best practices for the specific language.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to check"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename for context"
                    }
                },
                "required": ["code", "language"]
            },
            function=self._check_code_style
        )
        
        tools["get_related_files"] = Tool(
            name="get_related_files",
            description="Get list of related files that might be affected by changes. Use this to understand the impact of changes.",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file that changed"
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["filename", "repo_name"]
            },
            function=self._get_related_files
        )
        
        tools["search_codebase"] = Tool(
            name="search_codebase",
            description="Search the codebase for patterns, similar code, or related implementations. Use this to find similar patterns or check consistency.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or pattern to look for"
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["query", "repo_name"]
            },
            function=self._search_codebase
        )
        
        tools["get_past_reviews"] = Tool(
            name="get_past_reviews",
            description="Retrieve similar past reviews from the knowledge base to maintain consistency and learn from previous feedback.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code snippet to find similar reviews for"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language"
                    }
                },
                "required": ["code", "language"]
            },
            function=self._get_past_reviews
        )
        
        tools["prioritize_issues"] = Tool(
            name="prioritize_issues",
            description="Analyze and prioritize found issues based on severity, impact, and risk. Use this to organize findings.",
            parameters={
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "description": "List of issues found",
                        "items": {"type": "object"}
                    }
                },
                "required": ["issues"]
            },
            function=self._prioritize_issues
        )
        
        return tools
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get OpenAI function calling schema for all tools"""
        return [tool.to_openai_schema() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        tool = self.tools[tool_name]
        try:
            result = tool.function(**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Tool implementations
    def _analyze_code_file(self, filename: str, code: str, language: str) -> Dict[str, Any]:
        """Analyze a code file"""
        if not self.review_service:
            return {"error": "Review service not available"}
        
        file_data = {
            "filename": filename,
            "patch": code,
            "language": language
        }
        
        analysis = self.review_service._analyze_file(file_data)
        return {
            "filename": filename,
            "analysis": analysis,
            "issues_count": len(analysis.get("issues", [])),
            "suggestions_count": len(analysis.get("suggestions", []))
        }
    
    def _get_file_content(self, filename: str, repo_name: str) -> Dict[str, Any]:
        """Get file content from repository"""
        if not self.github_service or not self.github_service.client:
            return {"error": "GitHub service not available"}
        
        try:
            repo = self.github_service.client.get_repo(repo_name)
            file_content = repo.get_contents(filename)
            return {
                "filename": filename,
                "content": file_content.decoded_content.decode("utf-8"),
                "size": file_content.size
            }
        except Exception as e:
            return {"error": f"Could not fetch file: {str(e)}"}
    
    def _check_dependencies(self, package_file: str, file_type: str) -> Dict[str, Any]:
        """Check dependencies for security and compatibility"""
        issues = []
        suggestions = []
        
        # Parse dependencies based on file type
        if file_type == "requirements":
            # Check for common security issues in requirements.txt
            lines = package_file.split("\n")
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Check for pinned versions
                if "==" not in line and ">=" not in line and "~=" not in line:
                    issues.append({
                        "severity": "medium",
                        "message": f"Unpinned dependency: {line}",
                        "suggestion": "Pin dependency to specific version for reproducibility"
                    })
                
                # Check for known vulnerable packages
                vulnerable_packages = ["django<2.0", "flask<1.0", "requests<2.20"]
                for vuln in vulnerable_packages:
                    if vuln.split("<")[0] in line.lower():
                        issues.append({
                            "severity": "high",
                            "message": f"Potentially vulnerable package version: {line}",
                            "suggestion": "Update to latest secure version"
                        })
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "dependencies_count": len([l for l in package_file.split("\n") if l.strip() and not l.startswith("#")])
        }
    
    def _analyze_security_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code for security patterns"""
        security_issues = []
        
        # Common security patterns to check
        patterns = {
            "python": [
                (r"eval\s*\(", "Use of eval() - security risk", "high"),
                (r"exec\s*\(", "Use of exec() - security risk", "high"),
                (r"pickle\.loads", "Unsafe pickle usage", "high"),
                (r"subprocess\.call", "Potential command injection", "medium"),
                (r"os\.system", "Use of os.system() - security risk", "high"),
            ],
            "javascript": [
                (r"eval\s*\(", "Use of eval() - XSS risk", "high"),
                (r"innerHTML\s*=", "Direct innerHTML assignment - XSS risk", "high"),
                (r"document\.write", "Use of document.write() - XSS risk", "medium"),
            ]
        }
        
        lang_patterns = patterns.get(language.lower(), [])
        for pattern, message, severity in lang_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count("\n") + 1
                security_issues.append({
                    "severity": severity,
                    "message": message,
                    "line": line_num,
                    "pattern": pattern
                })
        
        return {
            "security_issues": security_issues,
            "count": len(security_issues)
        }
    
    def _check_code_style(self, code: str, language: str, filename: str = None) -> Dict[str, Any]:
        """Check code style"""
        style_issues = []
        
        # Basic style checks
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                style_issues.append({
                    "severity": "low",
                    "message": f"Line {i} exceeds 120 characters",
                    "line": i
                })
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                style_issues.append({
                    "severity": "low",
                    "message": f"Line {i} has trailing whitespace",
                    "line": i
                })
        
        return {
            "style_issues": style_issues,
            "count": len(style_issues)
        }
    
    def _get_related_files(self, filename: str, repo_name: str) -> Dict[str, Any]:
        """Get related files"""
        # This is a simplified version - in production, you'd use AST analysis
        related = []
        
        # Extract imports/dependencies from filename context
        # For now, return empty list - can be enhanced with actual file analysis
        return {
            "related_files": related,
            "count": len(related)
        }
    
    def _search_codebase(self, query: str, repo_name: str) -> Dict[str, Any]:
        """Search codebase"""
        if not self.github_service or not self.github_service.client:
            return {"error": "GitHub service not available"}
        
        try:
            repo = self.github_service.client.get_repo(repo_name)
            # Use GitHub code search API
            results = repo.get_contents("")
            return {
                "query": query,
                "results": [],  # Simplified - would use actual search
                "count": 0
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def _get_past_reviews(self, code: str, language: str) -> Dict[str, Any]:
        """Get similar past reviews"""
        if not self.rag_service:
            return {"error": "RAG service not available"}
        
        try:
            context = self.rag_service.get_relevant_context(code, "", language, top_k=3)
            return {
                "context": context,
                "found": bool(context)
            }
        except Exception as e:
            return {"error": f"Could not retrieve past reviews: {str(e)}"}
    
    def _prioritize_issues(self, issues: List[Dict]) -> Dict[str, Any]:
        """Prioritize issues"""
        high = [i for i in issues if i.get("severity", "").lower() == "high"]
        medium = [i for i in issues if i.get("severity", "").lower() == "medium"]
        low = [i for i in issues if i.get("severity", "").lower() == "low"]
        
        return {
            "prioritized": {
                "high": high,
                "medium": medium,
                "low": low
            },
            "summary": {
                "total": len(issues),
                "high_count": len(high),
                "medium_count": len(medium),
                "low_count": len(low)
            }
        }

