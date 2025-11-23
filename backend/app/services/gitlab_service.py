"""
Service for handling GitLab operations
"""
import os
from typing import Dict, Any

import gitlab


class GitLabService:
    """Handle GitLab API operations"""

    def __init__(self):
        self.token = os.getenv("GITLAB_TOKEN")
        self.client = (
            gitlab.Gitlab("https://gitlab.com", private_token=self.token)
            if self.token
            else None
        )

    def get_mr_diff(self, mr_data: Dict) -> Dict[str, Any]:
        """
        Get the diff for a merge request

        Args:
            mr_data: Merge request data from webhook

        Returns:
            Dictionary containing MR diff information
        """
        try:
            project_id = mr_data["project_id"]
            mr_iid = mr_data["iid"]

            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            # Get changes
            changes = mr.changes()

            diff_data = {
                "mr_number": mr_iid,
                "title": mr.title,
                "description": mr.description,
                "author": mr.author["username"],
                "repository": project.path_with_namespace,
                "files": [],
            }

            for change in changes["changes"]:
                diff_data["files"].append(
                    {
                        "filename": change["new_path"],
                        "status": "modified"
                        if change["new_file"] is False
                        else "added",
                        "diff": change["diff"],
                        "language": self._detect_language(change["new_path"]),
                    }
                )

            return diff_data

        except Exception as e:
            raise Exception(f"Error getting MR diff: {str(e)}")

    def post_review_comments(self, mr_data: Dict, review_result: Dict) -> None:
        """
        Post review comments to a merge request

        Args:
            mr_data: Merge request data from webhook
            review_result: Analysis results from LLM
        """
        try:
            project_id = mr_data["project_id"]
            mr_iid = mr_data["iid"]

            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            # Create comment body
            comment_body = self._format_review_comment(review_result)

            # Post note
            mr.notes.create({"body": comment_body})

        except Exception as e:
            raise Exception(f"Error posting review comments: {str(e)}")

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

    def _format_review_comment(self, review_result: Dict) -> str:
        """Format the review result into a markdown comment"""
        comment = "## 🤖 Automated Code Review\n\n"

        if review_result.get("summary"):
            comment += f"### Summary\n{review_result['summary']}\n\n"

        if review_result.get("issues"):
            comment += "### Issues Found\n\n"
            for issue in review_result["issues"]:
                severity = issue.get("severity", "info").upper()
                emoji = (
                    "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🔵"
                )
                comment += f"{emoji} **{severity}**: {issue.get('message')}\n"
            comment += "\n"

        if review_result.get("suggestions"):
            comment += "### Suggestions\n\n"
            for suggestion in review_result["suggestions"]:
                comment += f"- {suggestion}\n"
            comment += "\n"

        comment += (
            "\n---\n*This review was generated automatically by the PR Reviewer Bot*"
        )

        return comment
