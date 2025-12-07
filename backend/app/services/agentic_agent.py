"""
Agentic AI Agent for autonomous code review.
Implements planning, tool use, and iterative reasoning.
"""
from typing import Dict, Any, List, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage

from app.services.agent_tools import AgentTools
from app.services.agent_memory import AgentMemory


class AgenticAgent:
    """
    Autonomous agent that plans, executes, and iterates on code reviews.
    Uses function calling to interact with tools and make decisions.
    """
    
    def __init__(
        self,
        github_service=None,
        review_service=None,
        rag_service=None,
        max_iterations: int = 10
    ):
        self.github_service = github_service
        self.review_service = review_service
        self.rag_service = rag_service
        self.max_iterations = max_iterations
        
        # Initialize MCP Filesystem client
        mcp_filesystem = None
        try:
            from app.services.mcp_filesystem import MCPFilesystemClient
            mcp_filesystem = MCPFilesystemClient()
        except Exception as e:
            print(f"Warning: Could not initialize MCP Filesystem: {e}")
        
        # Initialize components
        self.tools = AgentTools(
            github_service=github_service,
            review_service=review_service,
            rag_service=rag_service,
            mcp_filesystem=mcp_filesystem
        )
        self.memory = AgentMemory()
        
        # Initialize LLM with function calling
        self._init_llm()
        
        # System prompt for the agent
        self.system_prompt = self._create_system_prompt()
    
    def _init_llm(self):
        """Initialize LLM with function calling support"""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.3))
        
        if api_key:
            try:
                # Try using bind_tools for newer LangChain versions
                tools_schema = self.tools.get_tools_schema()
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=temperature,
                    api_key=api_key,
                )
                # Bind functions/tools - try different methods for compatibility
                try:
                    self.llm = self.llm.bind_tools(tools_schema)
                except AttributeError:
                    # Fallback to bind_functions for older versions
                    try:
                        self.llm = self.llm.bind_functions(tools_schema)
                    except AttributeError:
                        # If neither works, use tools parameter
                        self.llm = ChatOpenAI(
                            model=model,
                            temperature=temperature,
                            api_key=api_key,
                            model_kwargs={"functions": tools_schema}
                        )
            except Exception as e:
                print(f"Warning: Could not initialize LLM with function calling: {e}")
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=temperature,
                    api_key=api_key,
                )
        else:
            self.llm = None
            print("⚠️  Warning: OPENAI_API_KEY not set. Agentic mode disabled.")
    
    def _invoke_with_tools(self, messages: List, tool_schemas: List[Dict[str, Any]]):
        """
        Invoke LLM with tool/function calling enabled
        
        Args:
            messages: Conversation history
            tool_schemas: Available tool schemas for function calling
            
        Returns:
            LLM response (may include tool calls)
        """
        # For OpenAI with LangChain, we can use the bound LLM directly
        # This method provides a consistent interface and allows for future customization
        try:
            # Convert LangChain messages if needed (they should already be in correct format)
            response = self.llm.invoke(messages)
            return response
        except Exception as e:
            print(f"Error invoking LLM with tools: {e}")
            # Fallback to simple invocation without tools
            try:
                # Create a simple LLM without tool binding for fallback
                import os
                from langchain_openai import ChatOpenAI
                fallback_llm = ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                    temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.3)),
                    api_key=os.getenv("OPENAI_API_KEY"),
                )
                return fallback_llm.invoke(messages)
            except Exception as fallback_error:
                print(f"Fallback LLM invocation also failed: {fallback_error}")
                raise
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent"""
        return """You are an autonomous AI code review agent with access to specialized tools. Your goal is to thoroughly review pull requests by:

1. **Planning**: Analyze the PR and create a review plan
2. **Investigating**: Use available tools to gather information and analyze code
3. **Reasoning**: Think through findings and prioritize issues
4. **Iterating**: Refine your review based on what you discover
5. **Finalizing**: Compile a comprehensive review with actionable feedback

**Available Tools (USE THESE!):**
- analyze_code_file: Deep analysis of specific files for bugs, security, quality
- get_file_content: Get full file contents for context
- check_dependencies: Analyze package dependencies for security
- analyze_security_patterns: Security vulnerability scanning (SQL injection, XSS, etc.)
- check_code_style: Code style and best practices
- get_related_files: Find related files that might be affected
- search_codebase: Search for patterns or similar code
- get_past_reviews: Learn from past reviews (RAG)
- prioritize_issues: Organize and prioritize findings

**Your Approach:**
1. Start by analyzing 2-3 most critical changed files using analyze_code_file
2. For security-sensitive code, use analyze_security_patterns
3. If dependencies changed, use check_dependencies
4. Use get_past_reviews to maintain consistency with previous feedback
5. Prioritize findings with prioritize_issues before finalizing

**Decision Making:**
- **ALWAYS** use analyze_code_file for any file with significant changes
- **ALWAYS** use analyze_security_patterns for authentication, database, or API code
- **ALWAYS** use check_dependencies if package files are modified
- Use tools strategically but don't over-analyze trivial changes
- When you have analyzed the key files and found issues, say "finalize" to complete

**Output Format:**
After using tools and gathering findings, provide your final analysis with:
- Specific issues found (severity, category, message, line number)
- Actionable suggestions
- Overall assessment

Be thorough but efficient. Focus on high-impact issues."""
    
    def review_pr(self, diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for PR review using agentic approach
        
        Args:
            diff_data: PR diff data containing files and changes
            
        Returns:
            Complete review result with agent reasoning
        """
        pr_number = diff_data.get("pr_number")
        repository = diff_data.get("repository")
        
        # Initialize review session
        self.memory.initialize_review(pr_number, repository)
        self.memory.update_phase("planning")
        
        # Build initial context
        context = self._build_initial_context(diff_data)
        
        # Get tool schemas for function calling
        tool_schemas = self.tools.get_tools_schema()
        
        # Agent reasoning loop
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]
        
        review_result = {
            "pr_number": pr_number,
            "repository": repository,
            "summary": "",
            "issues": [],
            "suggestions": [],
            "file_issues": [],
            "overall_score": 0,
            "agent_reasoning": [],
            "decisions_made": [],
            "tools_used": []
        }
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            print(f"\n🤖 Agent Iteration {iteration}/{self.max_iterations}")
            
            # Get LLM response with tool schemas (enables function calling)
            try:
                response = self._invoke_with_tools(messages, tool_schemas)
                messages.append(response)
                
                # Record agent's thought
                thought = response.content if response.content else "Analyzing..."
                self.memory.add_step(thought)
                print(f"💭 Agent thought: {thought[:200]}...")
                
                # Check if LLM wants to call functions/tools
                tool_calls = None
                if hasattr(response, "tool_calls") and response.tool_calls:
                    tool_calls = response.tool_calls
                    print(f"🔧 Tool calls requested: {len(tool_calls)}")
                elif hasattr(response, "additional_kwargs") and "tool_calls" in response.additional_kwargs:
                    tool_calls = response.additional_kwargs["tool_calls"]
                    print(f"🔧 Tool calls requested (legacy): {len(tool_calls) if isinstance(tool_calls, list) else 1}")
                else:
                    print("ℹ️  No tool calls in this iteration")
                
                if tool_calls:
                    # Execute tool calls
                    print(f"   Executing {len(tool_calls) if isinstance(tool_calls, list) else 1} tool(s)...")
                    for tool_call in tool_calls:
                        # Handle different tool call formats
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get("function", {}).get("name") or tool_call.get("name")
                            tool_args_str = tool_call.get("function", {}).get("arguments") or tool_call.get("args", "{}")
                        else:
                            # Handle tool call objects
                            tool_name = getattr(tool_call, "name", None) or getattr(tool_call, "function", {}).get("name")
                            tool_args_str = getattr(tool_call, "args", "{}") or getattr(tool_call, "function", {}).get("arguments", "{}")
                        
                        if not tool_name:
                            continue
                        
                        print(f"   📌 Calling tool: {tool_name}")
                        
                        # Parse arguments
                        try:
                            tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                        except (json.JSONDecodeError, TypeError):
                            tool_args = {}
                        
                        # Execute tool
                        tool_result = self.tools.execute_tool(tool_name, tool_args)
                        print(f"   ✅ Tool result: {tool_result.get('success', False)}")
                        
                        # Record tool usage
                        self.memory.add_step(
                            thought=f"Using tool: {tool_name}",
                            tool_used=tool_name,
                            tool_arguments=tool_args,
                            tool_result=tool_result
                        )
                        
                        # Track unique tools used
                        if tool_name not in review_result["tools_used"]:
                            review_result["tools_used"].append(tool_name)
                        
                        # Add tool result to messages
                        try:
                            from langchain_core.messages import ToolMessage
                            # Try ToolMessage for newer versions
                            tool_call_id = None
                            if isinstance(tool_call, dict):
                                tool_call_id = tool_call.get("id")
                            elif hasattr(tool_call, "id"):
                                tool_call_id = tool_call.id
                            
                            messages.append(
                                ToolMessage(
                                    name=tool_name,
                                    content=json.dumps(tool_result),
                                    tool_call_id=tool_call_id
                                )
                            )
                        except (ImportError, TypeError):
                            # Fallback to FunctionMessage
                            messages.append(
                                FunctionMessage(
                                    name=tool_name,
                                    content=json.dumps(tool_result)
                                )
                            )
                        
                        # Process tool results
                        self._process_tool_result(tool_name, tool_result, review_result, diff_data)
                
                # Check if agent is ready to finalize (only if no tool calls)
                if not tool_calls and self._should_finalize(response, review_result):
                    print(f"✨ Agent ready to finalize after {iteration} iterations")
                    self.memory.update_phase("finalizing")
                    break
                
                # Update phase based on progress
                if iteration > 3:
                    self.memory.update_phase("analyzing")
                if iteration > 6:
                    self.memory.update_phase("reviewing")
            
            except Exception as e:
                print(f"❌ Error in iteration {iteration}: {str(e)}")
                self.memory.add_step(f"Error in iteration {iteration}: {str(e)}")
                # Continue with next iteration or break if critical
                if iteration >= 3:
                    break
        
        print(f"\n📊 Agent completed {iteration} iterations")
        print(f"   Issues found: {len(review_result.get('issues', []))}")
        print(f"   Tools used: {', '.join(review_result.get('tools_used', [])) or 'None'}")
        
        # Finalize review
        self.memory.update_phase("finalizing")
        review_result = self._finalize_review(review_result, diff_data)
        
        # Finalize memory
        finalized_state = self.memory.finalize_review()
        review_result["agent_reasoning"] = self.memory.get_reasoning_chain()
        review_result["decisions_made"] = finalized_state.decisions_made
        review_result["files_analyzed"] = finalized_state.files_analyzed
        review_result["review_summary"] = self.memory.get_review_summary()
        
        return review_result
    
    def _build_initial_context(self, diff_data: Dict[str, Any]) -> str:
        """Build initial context for the agent"""
        files = diff_data.get("files", [])
        context_parts = [
            f"Pull Request #{diff_data.get('pr_number')}",
            f"Repository: {diff_data.get('repository')}",
            f"Title: {diff_data.get('title', 'N/A')}",
            f"Description: {diff_data.get('description', 'N/A')[:500]}",
            f"\nFiles Changed: {len(files)}",
        ]
        
        for file in files[:10]:  # Limit to first 10 files
            context_parts.append(
                f"\n- {file.get('filename')} ({file.get('status')}) "
                f"[+{file.get('additions', 0)}/-{file.get('deletions', 0)}] "
                f"({file.get('language', 'unknown')})"
            )
        
        context_parts.append(
            "\n\nYour task: Review this PR thoroughly. Start by planning your approach, "
            "then use tools to analyze the code. Focus on security, bugs, code quality, "
            "and best practices. Provide specific, actionable feedback."
        )
        
        return "\n".join(context_parts)
    
    def _process_tool_result(
        self,
        tool_name: str,
        tool_result: Dict[str, Any],
        review_result: Dict[str, Any],
        diff_data: Dict[str, Any]
    ):
        """Process results from tool execution"""
        if not tool_result.get("success", True):
            return
        
        result_data = tool_result.get("result", {})
        
        if tool_name == "analyze_code_file":
            # Extract issues and suggestions from analysis
            analysis = result_data.get("analysis", {})
            if analysis.get("issues"):
                review_result["issues"].extend(analysis["issues"])
            if analysis.get("suggestions"):
                review_result["suggestions"].extend(analysis["suggestions"])
            if analysis.get("file_issues"):
                review_result["file_issues"].extend(analysis["file_issues"])
            
            filename = result_data.get("filename")
            if filename:
                self.memory.mark_file_analyzed(filename)
        
        elif tool_name == "analyze_security_patterns":
            # Add security issues
            security_issues = result_data.get("security_issues", [])
            for issue in security_issues:
                review_result["issues"].append({
                    "severity": issue.get("severity", "high"),
                    "category": "security",
                    "message": issue.get("message"),
                    "line": issue.get("line"),
                    "suggestion": "Review and fix security vulnerability"
                })
        
        elif tool_name == "check_dependencies":
            # Add dependency issues
            dep_issues = result_data.get("issues", [])
            for issue in dep_issues:
                review_result["issues"].append({
                    "severity": issue.get("severity", "medium"),
                    "category": "dependencies",
                    "message": issue.get("message"),
                    "suggestion": issue.get("suggestion", "Review dependency")
                })
        
        elif tool_name == "prioritize_issues":
            # Reorganize issues by priority
            prioritized = result_data.get("prioritized", {})
            # Could reorganize review_result["issues"] here if needed
    
    def _should_finalize(self, response, review_result: Dict[str, Any]) -> bool:
        """Determine if agent should finalize review"""
        # Check if agent explicitly says it's done
        content = response.content.lower() if response.content else ""
        if any(phrase in content for phrase in ["finalize", "complete", "done", "finished", "summary"]):
            return True
        
        # Check if we have sufficient information
        if len(review_result.get("issues", [])) > 0 or len(review_result.get("suggestions", [])) > 0:
            # If we have findings and no pending tool calls, we can finalize
            has_tool_calls = (
                (hasattr(response, "tool_calls") and response.tool_calls) or
                (hasattr(response, "additional_kwargs") and "tool_calls" in response.additional_kwargs)
            )
            if not has_tool_calls:
                return True
        
        return False
    
    def _finalize_review(self, review_result: Dict[str, Any], diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the review by generating summary and calculating score"""
        # Generate summary using LLM if available
        if self.review_service and self.review_service.llm_service:
            try:
                context = {
                    "title": diff_data.get("title"),
                    "description": diff_data.get("description"),
                    "files_changed": len(diff_data.get("files", [])),
                    "total_issues": len(review_result.get("issues", [])),
                    "total_suggestions": len(review_result.get("suggestions", [])),
                }
                review_result["summary"] = self.review_service.llm_service.generate_summary(
                    context, review_result
                )
            except Exception as e:
                review_result["summary"] = f"Review completed. Found {len(review_result.get('issues', []))} issues."
        
        # Calculate overall score
        review_result["overall_score"] = self._calculate_score(review_result)
        
        return review_result
    
    def _calculate_score(self, review_result: Dict[str, Any]) -> int:
        """Calculate overall code quality score"""
        issues = review_result.get("issues", [])
        score = 100
        
        for issue in issues:
            severity = issue.get("severity", "low").lower()
            if severity == "high":
                score -= 15
            elif severity == "medium":
                score -= 10
            else:
                score -= 5
        
        return max(0, min(100, score))

