"""
Memory and state management for the agentic AI system.
Tracks agent decisions, tool usage, and review history.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class AgentStep:
    """Represents a single step in the agent's reasoning process"""
    step_number: int
    thought: str
    tool_used: Optional[str]
    tool_arguments: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class AgentState:
    """Represents the current state of the agent"""
    pr_number: int
    repository: str
    current_phase: str  # planning, analyzing, reviewing, finalizing
    steps_taken: List[AgentStep]
    files_analyzed: List[str]
    issues_found: List[Dict[str, Any]]
    decisions_made: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        data["steps_taken"] = [step.to_dict() for step in self.steps_taken]
        return data


class AgentMemory:
    """Manages agent memory and state"""
    
    def __init__(self):
        self.current_state: Optional[AgentState] = None
        self.history: List[AgentState] = []
    
    def initialize_review(self, pr_number: int, repository: str) -> AgentState:
        """Initialize a new review session"""
        self.current_state = AgentState(
            pr_number=pr_number,
            repository=repository,
            current_phase="planning",
            steps_taken=[],
            files_analyzed=[],
            issues_found=[],
            decisions_made=[],
            start_time=datetime.utcnow()
        )
        return self.current_state
    
    def add_step(
        self,
        thought: str,
        tool_used: Optional[str] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a step to the current review"""
        if not self.current_state:
            raise ValueError("No active review session")
        
        step = AgentStep(
            step_number=len(self.current_state.steps_taken) + 1,
            thought=thought,
            tool_used=tool_used,
            tool_arguments=tool_arguments,
            tool_result=tool_result,
            timestamp=datetime.utcnow()
        )
        
        self.current_state.steps_taken.append(step)
    
    def add_decision(self, decision: str) -> None:
        """Record a decision made by the agent"""
        if not self.current_state:
            raise ValueError("No active review session")
        
        self.current_state.decisions_made.append(decision)
        self.add_step(f"Decision: {decision}")
    
    def mark_file_analyzed(self, filename: str) -> None:
        """Mark a file as analyzed"""
        if not self.current_state:
            raise ValueError("No active review session")
        
        if filename not in self.current_state.files_analyzed:
            self.current_state.files_analyzed.append(filename)
    
    def add_issue(self, issue: Dict[str, Any]) -> None:
        """Add an issue found during review"""
        if not self.current_state:
            raise ValueError("No active review session")
        
        self.current_state.issues_found.append(issue)
    
    def update_phase(self, phase: str) -> None:
        """Update the current phase"""
        if not self.current_state:
            raise ValueError("No active review session")
        
        self.current_state.current_phase = phase
        self.add_step(f"Phase transition: {phase}")
    
    def finalize_review(self) -> AgentState:
        """Finalize the current review"""
        if not self.current_state:
            raise ValueError("No active review session")
        
        self.current_state.end_time = datetime.utcnow()
        self.current_state.current_phase = "completed"
        
        # Save to history
        self.history.append(self.current_state)
        
        # Return copy and clear current
        finalized = self.current_state
        self.current_state = None
        
        return finalized
    
    def get_review_summary(self) -> Dict[str, Any]:
        """Get summary of current review"""
        if not self.current_state:
            return {"error": "No active review"}
        
        return {
            "pr_number": self.current_state.pr_number,
            "repository": self.current_state.repository,
            "phase": self.current_state.current_phase,
            "files_analyzed": len(self.current_state.files_analyzed),
            "issues_found": len(self.current_state.issues_found),
            "decisions_made": len(self.current_state.decisions_made),
            "steps_taken": len(self.current_state.steps_taken),
            "duration_seconds": (
                (datetime.utcnow() - self.current_state.start_time).total_seconds()
                if not self.current_state.end_time
                else (self.current_state.end_time - self.current_state.start_time).total_seconds()
            )
        }
    
    def get_reasoning_chain(self) -> List[Dict[str, Any]]:
        """Get the full reasoning chain"""
        if not self.current_state:
            return []
        
        return [step.to_dict() for step in self.current_state.steps_taken]

