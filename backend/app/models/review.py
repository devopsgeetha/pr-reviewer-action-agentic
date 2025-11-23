"""
Database models
"""
from typing import Dict, List, Optional
from datetime import datetime


class Review:
    """Review model"""

    def __init__(
        self,
        pr_number: int,
        repository: str,
        summary: str,
        issues: List[Dict],
        suggestions: List[str],
        overall_score: int,
        timestamp: Optional[datetime] = None,
    ):
        self.pr_number = pr_number
        self.repository = repository
        self.summary = summary
        self.issues = issues
        self.suggestions = suggestions
        self.overall_score = overall_score
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "pr_number": self.pr_number,
            "repository": self.repository,
            "summary": self.summary,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "overall_score": self.overall_score,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Review":
        """Create from dictionary"""
        return Review(
            pr_number=data["pr_number"],
            repository=data["repository"],
            summary=data["summary"],
            issues=data["issues"],
            suggestions=data["suggestions"],
            overall_score=data["overall_score"],
            timestamp=data.get("timestamp"),
        )
