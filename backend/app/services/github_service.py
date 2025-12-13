"""
Service for handling GitHub operations
"""
import os
import requests
from github import Github
from typing import Dict, List, Any, Tuple, Optional
import re


class GitHubService:
    """Handle GitHub API operations"""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.client = Github(self.token) if self.token else None
        
    def _check_token_permissions(self, repo_name: str) -> Dict[str, Any]:
        """
        Check what permissions the token has
        Returns a dict with permission info for debugging
        """
        try:
            owner, repo = repo_name.split("/")
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "PR-Reviewer-Action"
            }
            
            # Check repository access
            response = requests.get(api_url, headers=headers, timeout=10)
            return {
                "repo_access": response.status_code == 200,
                "repo_status": response.status_code,
                "token_present": bool(self.token),
                "token_preview": f"{self.token[:10]}..." if self.token and len(self.token) > 10 else "None"
            }
        except Exception:
            return {"error": "Could not check permissions"}

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict:
        """
        Get pull request data from GitHub API

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            Dictionary containing PR data
        """
        try:
            repo_name = f"{owner}/{repo}"
            print(f"🔍 Fetching PR #{pr_number} from {repo_name}...")
            repository = self.client.get_repo(repo_name)
            pr = repository.get_pull(pr_number)
            
            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": {"login": pr.user.login},
                "base": {
                    "repo": {
                        "full_name": repo_name
                    }
                }
            }
            
            print(f"✅ Retrieved PR #{pr_data['number']}: {pr_data['title']}")
            return pr_data
        except Exception as e:
            print(f"❌ Error fetching PR #{pr_number}: {str(e)}")
            raise Exception(f"Error getting pull request: {str(e)}")

    def get_pr_diff(self, pr_data: Dict) -> Dict[str, Any]:
        """
        Get the diff for a pull request

        Args:
            pr_data: Pull request data from webhook

        Returns:
            Dictionary containing PR diff information
        """
        try:
            repo_name = pr_data["base"]["repo"]["full_name"]
            pr_number = pr_data["number"]

            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            # Get files changed
            files = pr.get_files()

            diff_data = {
                "pr_number": pr_number,
                "title": pr.title,
                "description": pr.body,
                "author": pr.user.login,
                "repository": repo_name,
                "files": [],
            }

            for file in files:
                diff_data["files"].append(
                    {
                        "filename": file.filename,
                        "status": file.status,
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "patch": file.patch if hasattr(file, "patch") else None,
                        "language": self._detect_language(file.filename),
                    }
                )

            return diff_data

        except Exception as e:
            raise Exception(f"Error getting PR diff: {str(e)}")

    def _parse_diff_ranges(self, diff_data: Dict[str, Any]) -> Dict[str, List[tuple]]:
        """
        Parse PR diff to find valid line ranges for comments.
        Returns a dict mapping filename -> list of (start_line, end_line) tuples
        """
        valid_ranges = {}
        
        for file in diff_data.get("files", []):
            filename = file.get("filename")
            patch = file.get("patch", "")
            if not filename or not patch:
                continue
                
            ranges = []
            # Parse hunks: @@ -original,count +new,count @@
            # We only care about the new line numbers (the one with +)
            # Regex captures start_line and optional count
            hunk_headers = re.finditer(r'@@\s*-[0-9,]+\s*\+(\d+)(?:,(\d+))?\s*@@', patch)
            
            for match in hunk_headers:
                start_line = int(match.group(1))
                # If count is missing, it defaults to 1
                count = int(match.group(2)) if match.group(2) else 1
                
                # The valid range covers these lines
                end_line = start_line + count - 1
                ranges.append((start_line, end_line))
                
            if ranges:
                valid_ranges[filename] = ranges
                
        return valid_ranges

    def post_review_comments(self, pr_data: Dict, review_result: Dict, use_inline: bool = True) -> None:
        """
        Post review comments to a pull request
        
        Args:
            pr_data: Pull request data from webhook
            review_result: Analysis results from LLM
            use_inline: If True, post as inline review comments. If False, post as issue comment
                       Inline comments require 'pull-requests: write' permission
                       Issue comments require 'issues: write' permission
        """
        try:
            repo_name = pr_data["base"]["repo"]["full_name"]
            pr_number = pr_data["number"]
            
            print(f"📝 Preparing to post review comment...")
            print(f"   Repository: {repo_name}")
            print(f"   PR Number: {pr_number}")
            print(f"   Mode: {'Inline comments' if use_inline else 'General comment'}")
            
            # Verify PR number matches what we expect
            actual_pr_number = pr_data.get("number", pr_number)
            if actual_pr_number != pr_number:
                print(f"⚠️  Warning: PR number mismatch. Using {actual_pr_number} from PR data (expected {pr_number})")
                pr_number = actual_pr_number  # Use the actual PR number from the data

            # Try inline comments first (preferred method)
            if use_inline:
                try:
                    self.post_inline_review_comments(pr_data, review_result)
                    return  # Success!
                except Exception as inline_error:
                    error_msg = str(inline_error)
                    if "403" in error_msg or "Permission denied" in error_msg:
                        print(f"⚠️  Inline comments failed due to permissions: {error_msg}")
                        print(f"   Falling back to general comment...")
                        # Fall through to issue comment below
                    else:
                        print(f"⚠️  Inline comments failed: {error_msg}")
                        print(f"   Falling back to general comment...")
                        # Fall through to issue comment below

            # Fallback to issue comment
            print(f"   Using issue comment fallback...")

            # Create review comment body with inline comments included
            comment_body = self._format_review_comment(review_result, include_inline=True)
            print(f"   Comment length: {len(comment_body)} characters")
            print(f"   Comment preview (first 200 chars): {comment_body[:200]}...")
            
            if not comment_body or len(comment_body.strip()) == 0:
                raise Exception("Comment body is empty! Cannot post empty comment.")

            # Try using REST API directly first (more reliable for permissions)
            try:
                owner, repo = repo_name.split("/")
                api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
                print(f"   API URL: {api_url}")
                
                headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "PR-Reviewer-Action"
                }
                
                response = requests.post(
                    api_url,
                    json={"body": comment_body},
                    headers=headers,
                    timeout=30
                )
                
                # Handle success status codes (201 Created is standard, but 200 OK might also occur)
                if response.status_code in [200, 201]:
                    try:
                        response_data = response.json()
                        comment_url = response_data.get("html_url", "N/A")
                        comment_id = response_data.get("id", "N/A")
                        print(f"✅ Comment posted successfully!")
                        print(f"   Status code: {response.status_code}")
                        print(f"   Comment ID: {comment_id}")
                        print(f"   Comment URL: {comment_url}")
                        print(f"   PR #{pr_number} in {repo_name}")
                        print(f"   View PR: https://github.com/{repo_name}/pull/{pr_number}")
                        
                        # Verify the comment was actually created by fetching it back
                        if comment_id and comment_id != "N/A":
                            verify_url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
                            verify_response = requests.get(verify_url, headers=headers, timeout=10)
                            if verify_response.status_code == 200:
                                verify_data = verify_response.json()
                                verified_pr_number = verify_data.get("issue_url", "").split("/")[-1]
                                print(f"   ✅ Verified: Comment exists and is accessible")
                                print(f"   Verified on issue/PR: #{verified_pr_number}")
                                if str(verified_pr_number) != str(pr_number):
                                    print(f"   ⚠️  WARNING: Comment was posted to issue #{verified_pr_number}, not PR #{pr_number}!")
                            else:
                                print(f"   ⚠️  Warning: Could not verify comment (status {verify_response.status_code})")
                                print(f"   Response: {verify_response.text[:200]}")
                        
                        return  # Success!
                    except Exception as parse_error:
                        print(f"⚠️  Comment created but couldn't parse response: {parse_error}")
                        print(f"   Response status: {response.status_code}")
                        print(f"   Response text: {response.text[:500]}")
                        return  # Still consider it success if status was 200/201
                elif response.status_code == 403:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("message", "Forbidden")
                    raise Exception(
                        f"Permission denied (403): Unable to post comment on PR #{pr_number}.\n"
                        f"Repository: {repo_name}\n"
                        f"This usually means the workflow is missing required permissions.\n\n"
                        f"SOLUTION: Add this to your workflow file under the job:\n\n"
                        f"  permissions:\n"
                        f"    issues: write\n"
                        f"    pull-requests: read\n\n"
                        f"If the PR is from a fork, you may need to use a Personal Access Token (PAT)\n"
                        f"instead of GITHUB_TOKEN. See ACTION_README.md for details.\n\n"
                        f"GitHub API error: {error_msg}"
                    )
                else:
                    # Log the error and try PyGithub as fallback
                    print(f"⚠️  REST API returned status {response.status_code}")
                    print(f"   Response: {response.text[:500]}")
                    print(f"   Attempting fallback to PyGithub...")
                    # Don't raise here, let it fall through to PyGithub fallback
                    raise requests.RequestException(f"REST API returned {response.status_code}: {response.text}")
                    
            except (requests.RequestException, Exception) as rest_error:
                # Fallback to PyGithub if REST API fails
                error_msg = str(rest_error)
                print(f"⚠️  REST API failed: {error_msg}")
                print(f"   Attempting fallback to PyGithub...")
                try:
                    repo = self.client.get_repo(repo_name)
                    issue = repo.get_issue(pr_number)
                    print(f"   Creating comment via PyGithub on issue #{pr_number}...")
                    comment = issue.create_comment(comment_body)
                    print(f"✅ Comment posted successfully via PyGithub!")
                    print(f"   Comment ID: {comment.id}")
                    print(f"   Comment URL: {comment.html_url}")
                    print(f"   PR #{pr_number} in {repo_name}")
                    print(f"   View PR: https://github.com/{repo_name}/pull/{pr_number}")
                    return
                except Exception as pygithub_error:
                    # If both fail, raise a comprehensive error
                    print(f"❌ Both REST API and PyGithub failed!")
                    print(f"   REST API error: {error_msg}")
                    print(f"   PyGithub error: {str(pygithub_error)}")
                    raise Exception(
                        f"Failed to post comment using both methods.\n"
                        f"REST API error: {error_msg}\n"
                        f"PyGithub error: {str(pygithub_error)}"
                    )

        except Exception as e:
            error_msg = str(e)
            # Provide helpful error message for 403 errors
            if "403" in error_msg or "Resource not accessible by integration" in error_msg or "Permission denied" in error_msg:
                # Error message already includes helpful info, just re-raise
                raise
            raise Exception(f"Error posting review comments: {error_msg}")

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".rs": "rust",
        }

        ext = os.path.splitext(filename)[1].lower()
        return extensions.get(ext, "unknown")

    def _format_review_comment(self, review_result: Dict, include_inline: bool = False) -> str:
        """Format the review result into a markdown comment with rich formatting"""
        # Check if this is an agentic AI review
        is_agentic = bool(review_result.get("agent_reasoning") or review_result.get("review_summary"))
        
        if is_agentic:
            comment = "## 🤖 Agentic AI Code Review\n\n"
            comment += "<details>\n<summary><b>✨ Powered by Autonomous AI Agent</b></summary>\n\n"
            comment += "This review was generated by an **autonomous AI agent** that:\n"
            comment += "- 🧠 Plans review strategy based on PR changes\n"
            comment += "- 🔧 Uses specialized tools for analysis\n"
            comment += "- 🔄 Iteratively refines findings\n"
            comment += "- 📚 Learns from past reviews\n\n"
            comment += "</details>\n\n"
        else:
            comment = "## 🤖 Automated Code Review\n\n"

        # Summary section with rich formatting
        if review_result.get("summary"):
            comment += "### 📋 Executive Summary\n\n"
            comment += f"> {review_result['summary']}\n\n"
        
        # Overall score with visual indicator
        score = review_result.get("overall_score", 0)
        if score >= 90:
            score_emoji = "🟢"
            score_text = "Excellent"
            score_bar = "████████████████████"
        elif score >= 75:
            score_emoji = "🟡"
            score_text = "Good"
            score_bar = "██████████████░░░░░░"
        elif score >= 60:
            score_emoji = "🟠"
            score_text = "Needs Improvement"
            score_bar = "████████░░░░░░░░░░░░"
        else:
            score_emoji = "🔴"
            score_text = "Critical Issues"
            score_bar = "████░░░░░░░░░░░░░░░░"
        
        comment += "### 📊 Code Quality Score\n\n"
        comment += f"{score_emoji} **{score}/100** - {score_text}\n\n"
        comment += f"```\n{score_bar}\n```\n\n"

        # Agentic Review Metadata (if available)
        if is_agentic and review_result.get("review_summary"):
            summary = review_result.get("review_summary", {})
            comment += "### 🔍 Review Process\n\n"
            comment += "| Metric | Value |\n"
            comment += "|--------|-------|\n"
            comment += f"| **Files Analyzed** | {summary.get('files_analyzed', 0)} |\n"
            comment += f"| **Issues Found** | {summary.get('issues_found', 0)} |\n"
            comment += f"| **Reasoning Steps** | {summary.get('steps_taken', 0)} |\n"
            comment += f"| **Review Phase** | {summary.get('phase', 'completed').title()} |\n"
            if summary.get('duration_seconds'):
                comment += f"| **Duration** | {summary.get('duration_seconds', 0):.1f}s |\n"
            comment += "\n"
        
        # Issues Found section with enhanced details and rich formatting
        if review_result.get("issues"):
            comment += "### 🐛 Issues Found\n\n"
            for idx, issue in enumerate(review_result["issues"], 1):
                severity = issue.get("severity", "info").upper()
                category = issue.get("category", "general").capitalize()
                
                # Enhanced emoji based on severity
                if severity == "HIGH":
                    emoji = "🔴"
                    badge = "🔴 **HIGH PRIORITY**"
                elif severity == "MEDIUM":
                    emoji = "🟡"
                    badge = "🟡 **MEDIUM PRIORITY**"
                else:
                    emoji = "🔵"
                    badge = "🔵 **LOW PRIORITY**"
                
                # Issue card style formatting
                # Use \u0023 to prevent GitHub from auto-linking #number to issues/PRs
                comment += f"#### {emoji} Issue \\#{idx}: {badge}\n\n"
                comment += f"**{issue.get('message')}**\n\n"
                
                # Details table
                comment += "| Detail | Information |\n"
                comment += "|-------|-------------|\n"
                
                # Location details
                file_path = issue.get('file', '')
                line_num = issue.get('line', '')
                if file_path:
                    location = f"`{file_path}`"
                    if line_num:
                        location += f":{line_num}"
                    comment += f"| 📍 **Location** | {location} |\n"
                
                # Category/Risk
                if category != "General":
                    comment += f"| 🏷️ **Category** | {category} |\n"
                
                # Suggestion for this specific issue
                if issue.get('suggestion'):
                    comment += f"| 💡 **Suggestion** | {issue.get('suggestion')} |\n"
                
                comment += "\n"

        # Include file-specific issues if available
        if include_inline and review_result.get("file_issues"):
            comment += "### 📄 File-Specific Issues\n\n"
            for file_issue in review_result.get("file_issues", []):
                if file_issue.get("file") and file_issue.get("line"):
                    comment += f"**`{file_issue['file']}`** (line {file_issue['line']}):\n"
                    comment += f"> {file_issue.get('message', '')}\n\n"
            comment += "\n"

        # Suggestions section with better formatting
        if review_result.get("suggestions"):
            comment += "### 💡 Suggestions for Improvement\n\n"
            for idx, suggestion in enumerate(review_result["suggestions"], 1):
                # Check if suggestion is a dict with more details
                if isinstance(suggestion, dict):
                    comment += f"**{idx}. {suggestion.get('title', 'Improvement')}**\n\n"
                    comment += f"{suggestion.get('description', '')}\n\n"
                else:
                    comment += f"**{idx}.** {suggestion}\n\n"
            comment += "\n"
        
        # Agentic-specific sections
        if is_agentic:
            # Tools Used (extract from reasoning chain)
            tools_used = set()
            if review_result.get("agent_reasoning"):
                for step in review_result["agent_reasoning"]:
                    tool = step.get("tool_used")
                    if tool:
                        tools_used.add(tool)
            
            if tools_used:
                comment += "### 🔧 Tools Used\n\n"
                comment += "The agent used the following specialized tools:\n\n"
                for tool in sorted(tools_used):
                    tool_display = tool.replace("_", " ").title()
                    comment += f"- 🔨 **{tool_display}** (`{tool}`)\n"
                comment += "\n"
            
            # Files Analyzed
            if review_result.get("review_summary"):
                files_analyzed = review_result.get("files_analyzed", [])
                if files_analyzed:
                    comment += "### 📁 Files Analyzed\n\n"
                    for file in files_analyzed[:10]:  # Limit to first 10
                        comment += f"- `{file}`\n"
                    if len(files_analyzed) > 10:
                        comment += f"\n*... and {len(files_analyzed) - 10} more files*\n"
                    comment += "\n"
            
            # Decisions Made (collapsible)
            if review_result.get("decisions_made"):
                comment += "<details>\n<summary><b>🧠 Agent Decisions</b> (Click to expand)</summary>\n\n"
                for decision in review_result["decisions_made"]:
                    comment += f"- {decision}\n"
                comment += "\n</details>\n\n"
            
            # Reasoning Chain (collapsible)
            if review_result.get("agent_reasoning"):
                reasoning_steps = review_result["agent_reasoning"]
                if len(reasoning_steps) > 0:
                    comment += "<details>\n<summary><b>🔗 Reasoning Chain</b> (Click to expand)</summary>\n\n"
                    comment += f"*The agent took {len(reasoning_steps)} reasoning steps:*\n\n"
                    
                    for step in reasoning_steps[:15]:  # Show first 15 steps
                        step_num = step.get("step_number", 0)
                        thought = step.get("thought", "")
                        tool_used = step.get("tool_used")
                        
                        comment += f"**Step {step_num}:** {thought}\n"
                        if tool_used:
                            comment += f"  - 🔧 Used tool: `{tool_used}`\n"
                        comment += "\n"
                    
                    if len(reasoning_steps) > 15:
                        comment += f"\n*... and {len(reasoning_steps) - 15} more steps*\n"
                    
                    comment += "</details>\n\n"
        
        # Statistics summary with visual chart
        issues_count = len(review_result.get("issues", []))
        suggestions_count = len(review_result.get("suggestions", []))
        if issues_count > 0 or suggestions_count > 0:
            comment += "### 📈 Review Statistics\n\n"
            
            # Create visual breakdown
            if issues_count > 0:
                high_count = sum(1 for i in review_result.get("issues", []) if i.get("severity", "").upper() == "HIGH")
                medium_count = sum(1 for i in review_result.get("issues", []) if i.get("severity", "").upper() == "MEDIUM")
                low_count = sum(1 for i in review_result.get("issues", []) if i.get("severity", "").upper() == "LOW")
                
                comment += "| Severity | Count |\n"
                comment += "|----------|-------|\n"
                if high_count > 0:
                    comment += f"| 🔴 High | {high_count} |\n"
                if medium_count > 0:
                    comment += f"| 🟡 Medium | {medium_count} |\n"
                if low_count > 0:
                    comment += f"| 🔵 Low | {low_count} |\n"
                comment += f"| **Total Issues** | **{issues_count}** |\n\n"
            
            if suggestions_count > 0:
                comment += f"**Total Suggestions:** {suggestions_count}\n\n"

        # Footer
        if is_agentic:
            comment += "---\n\n"
            comment += "🤖 **Agentic AI Review** | "
            comment += "Powered by autonomous AI agent with tool-based analysis\n\n"
            comment += "*This review was generated using Agentic AI that plans, reasons, and makes decisions autonomously.*"
        else:
            comment += "---\n"
            comment += "*This review was generated automatically by the PR Reviewer Bot*"

        return comment

    def post_inline_review_comments(self, pr_data: Dict, review_result: Dict) -> None:
        """
        Post inline review comments using GitHub's PR Review API
        This creates actual line-level comments on the PR code changes
        Requires 'pull-requests: write' permission in the workflow

        Args:
            pr_data: Pull request data from webhook
            review_result: Analysis results from LLM
        """
        try:
            repo_name = pr_data["base"]["repo"]["full_name"]
            pr_number = pr_data["number"]
            
            print(f"📝 Preparing to post inline review comments...")
            print(f"   Repository: {repo_name}")
            print(f"   PR Number: {pr_number}")
            
            # Step 1: Get diff data to validate line numbers
            # This is critical to avoid 422 errors from GitHub API
            valid_ranges = {}
            try:
                print("   Fetching PR diff to validate comment positions...")
                diff_data = self.get_pr_diff(pr_data)
                valid_ranges = self._parse_diff_ranges(diff_data)
                print(f"   Parsed valid line ranges for {len(valid_ranges)} files")
            except Exception as e:
                print(f"⚠️ Warning: Could not parse diff for line validation: {e}")
                # We will proceed with empty valid_ranges, which might result in all comments being skipped/moved to summary
            
            # Step 2: Create inline comments, filtering by valid ranges
            inline_comments, skipped_comments = self._create_inline_comments(review_result, valid_ranges)
            
            print(f"   Generated {len(inline_comments)} valid inline comments")
            if skipped_comments:
                print(f"   Moved {len(skipped_comments)} comments to summary (lines invalid or outside diff)")

            # Step 3: Create review body with summary + skipped comments
            review_body = self._create_review_summary(review_result, skipped_comments)
            
            # If we have absolutely no comments (inline or skipped) and no summary, warn but proceed
            if not inline_comments and not review_body:
                 print("⚠️  No content to post (no inline comments, no skipped comments, no summary).")
                 return

            owner, repo = repo_name.split("/")
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "PR-Reviewer-Action"
            }
            
            review_data = {
                "body": review_body,
                "event": "COMMENT",  # Options: APPROVE, REQUEST_CHANGES, COMMENT
                "comments": inline_comments
            }
            
            print(f"   API URL: {api_url}")
            print(f"   Review body length: {len(review_body)} characters")
            print(f"   Inline comments to post: {len(inline_comments)}")
            
            response = requests.post(
                api_url,
                json=review_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                review_id = response_data.get("id", "N/A")
                review_url = response_data.get("html_url", "N/A")
                print(f"✅ Inline review posted successfully!")
                print(f"   Review ID: {review_id}")
                print(f"   Review URL: {review_url}")
                print(f"   PR #{pr_number} in {repo_name}")
                print(f"   View PR: https://github.com/{repo_name}/pull/{pr_number}")
                
            elif response.status_code == 422:
                # Validation error - often means line numbers are invalid
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Unprocessable Entity")
                print(f"❌ GitHub API validation error (422): {error_msg}")
                print(f"   This usually means line numbers are invalid or don't exist in the diff")
                print(f"   Response: {response.text[:500]}")
                
                # Try to extract which comment failed
                errors = error_data.get("errors", [])
                for error in errors:
                    print(f"   Error detail: {error}")
                
                raise Exception(f"GitHub API validation error: {error_msg}")
                
            elif response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Forbidden")
                raise Exception(
                    f"Permission denied (403): Unable to post inline review on PR #{pr_number}.\n"
                    f"Repository: {repo_name}\n"
                    f"This usually means the workflow is missing required permissions.\n\n"
                    f"SOLUTION: Add this to your workflow file under the job:\n\n"
                    f"  permissions:\n"
                    f"    pull-requests: write\n"
                    f"    contents: read\n\n"
                    f"If the PR is from a fork, you may need to use a Personal Access Token (PAT)\n"
                    f"instead of GITHUB_TOKEN. See ACTION_README.md for details.\n\n"
                    f"GitHub API error: {error_msg}"
                )
            else:
                error_text = response.text[:500]
                print(f"❌ Failed to post inline review")
                print(f"   Status code: {response.status_code}")
                print(f"   Response: {error_text}")
                raise Exception(f"Failed to post inline review: HTTP {response.status_code} - {error_text}")
                
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error message for 403 errors
            if "403" in error_msg or "Resource not accessible by integration" in error_msg or "Permission denied" in error_msg:
                raise
            raise Exception(f"Error posting inline review comments: {error_msg}")
    
    def _create_review_summary(self, review_result: Dict, skipped_comments: List[Dict] = None) -> str:
        """
        Create a concise review summary for the PR review body
        Includes any comments that couldn't be posted inline
        """
        summary = "## 🤖 AI Code Review\n\n"
        
        # Overall summary
        if review_result.get("summary"):
            summary += f"{review_result['summary']}\n\n"
        
        # Quick stats
        issues_count = len(review_result.get("issues", []))
        file_issues_count = len(review_result.get("file_issues", []))
        suggestions_count = len(review_result.get("suggestions", []))
        
        if issues_count > 0 or file_issues_count > 0 or suggestions_count > 0:
            summary += "### 📊 Review Summary\n\n"
            if issues_count > 0:
                summary += f"- 🐛 **{issues_count}** general issues found\n"
            if file_issues_count > 0:
                summary += f"- 📍 **{file_issues_count}** line-specific comments\n"
            if suggestions_count > 0:
                summary += f"- 💡 **{suggestions_count}** suggestions for improvement\n"
            summary += "\n"
        
        # Overall score
        score = review_result.get("overall_score", 0)
        if score > 0:
            if score >= 85:
                emoji = "✅"
                status = "Great job!"
            elif score >= 70:
                emoji = "🟡"
                status = "Good work with room for improvement"
            else:
                emoji = "🔴"
                status = "Needs attention"
            
            summary += f"### {emoji} Overall Score: {score}/100\n{status}\n\n"
        
        # Append skipped comments (comments outside diff context)
        if skipped_comments:
            summary += "### ⚠️ Comments on Unchanged Lines & Context\n\n"
            summary += "The following issues were found but could not be posted inline because they are outside the PR diff context:\n\n"
            
            for comment in skipped_comments:
                path = comment.get("path", "unknown")
                line = comment.get("line", "?")
                body = comment.get("body", "").replace("\n", " ") # Collapse body mainly
                # Extract severity/message if possible from formatted body
                # Body format: 🔴 **HIGH**: message...
                
                summary += f"**`{path}`:{line}**\n"
                summary += f"> {body}\n\n"
        
        summary += "*📍 Check the inline comments below for specific feedback on individual lines.*"
        
        return summary
    
    def _create_inline_comments(self, review_result: Dict, valid_ranges: Dict[str, List[tuple]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Create inline comments for specific lines from review results.
        Filters comments based on valid_ranges (lines actually in the diff).
        
        Returns:
            Tuple of (valid_comments, skipped_comments)
        """
        valid_comments = []
        skipped_comments = []

        all_issues = []
        # Process file-specific issues with line numbers
        all_issues.extend(review_result.get("file_issues", []))
        # Also process general issues that have file/line info
        all_issues.extend([i for i in review_result.get("issues", []) if i.get("line") and i.get("file")])

        processed_locations = set()

        for issue in all_issues:
            if issue.get("line") and issue.get("file"):
                file_path = issue["file"]
                try:
                    line_num = int(issue["line"])
                except ValueError:
                    continue # Skip invalid line numbers
                    
                # Skip duplicate comments for same location
                loc_key = f"{file_path}:{line_num}"
                if loc_key in processed_locations:
                    continue
                processed_locations.add(loc_key)

                severity = issue.get("severity", "info").upper()
                emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🔵"
                
                comment_body = f"{emoji} **{severity}**: {issue.get('message', '')}"
                
                # Add suggestion if available
                if issue.get("suggestion"):
                    comment_body += f"\n\n💡 **Suggestion**: {issue['suggestion']}"
                
                # Add category if available
                if issue.get("category"):
                    comment_body += f"\n\n🏷️ **Category**: {issue['category']}"
                
                comment_data = {
                    "path": file_path,
                    "line": line_num,
                    "body": comment_body,
                }
                
                # Check validation
                is_valid = False
                if not valid_ranges:
                    # If we couldn't parse ranges, we can't strict validate. 
                    # We might choose to be optimistic (return True) or pessimistic (return False).
                    # Given the user wants to FIX 422 errors, we should probably be pessimistic 
                    # and put them in summary if we aren't sure. 
                    # BUT, if fetching diff failed completely, putting everything in summary is safer.
                    is_valid = False 
                else:
                    # Check if line is in valid ranges
                    ranges = valid_ranges.get(file_path, [])
                    for start, end in ranges:
                        if start <= line_num <= end:
                            is_valid = True
                            break
                
                if is_valid:
                    valid_comments.append(comment_data)
                else:
                    skipped_comments.append(comment_data)

        return valid_comments, skipped_comments
