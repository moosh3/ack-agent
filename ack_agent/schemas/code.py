from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ack_agent.schemas.base import BaseInvestigatorResponse, TaskParameters


class Commit(BaseModel):
    """Model representing a code commit"""
    commit_id: str = Field(..., description="Commit hash/ID")
    author: str = Field(..., description="Author of the commit")
    timestamp: datetime = Field(..., description="When the commit was made")
    message: str = Field(..., description="Commit message")
    files_changed: int = Field(0, description="Number of files changed")
    insertions: int = Field(0, description="Number of lines inserted")
    deletions: int = Field(0, description="Number of lines deleted")
    branch: Optional[str] = Field(None, description="Branch the commit was made on")
    is_merge: bool = Field(False, description="Whether this is a merge commit")
    pull_request: Optional[str] = Field(None, description="Related pull request ID")
    
    def is_large_change(self) -> bool:
        """Determine if this commit represents a large change"""
        return (self.files_changed > 10) or (self.insertions + self.deletions > 100)


class Deployment(BaseModel):
    """Model representing a deployment"""
    id: str = Field(..., description="Deployment ID")
    environment: str = Field(..., description="Deployment environment")
    deployed_at: datetime = Field(..., description="When the deployment occurred")
    status: str = Field(..., description="Deployment status")
    commit_id: Optional[str] = Field(None, description="Associated commit ID")
    deployed_by: str = Field(..., description="User who triggered the deployment")
    build_number: Optional[str] = Field(None, description="CI/CD build number")
    duration: Optional[int] = Field(None, description="Deployment duration in seconds")
    rollback_of: Optional[str] = Field(None, description="ID of deployment this rolled back (if applicable)")


class CodeChange(BaseModel):
    """Model representing a single code change"""
    file: str = Field(..., description="File that was changed")
    commit_id: str = Field(..., description="Commit that introduced the change")
    author: str = Field(..., description="Author of the change")
    timestamp: datetime = Field(..., description="When the change was made")
    lines_added: int = Field(0, description="Number of lines added")
    lines_removed: int = Field(0, description="Number of lines removed")
    change_type: str = Field(..., description="Type of change (add, modify, delete)")
    description: Optional[str] = Field(None, description="Description of the change")


class RiskyChange(BaseModel):
    """Model representing a potentially risky code change"""
    file: str = Field(..., description="File with the risky change")
    commit_id: str = Field(..., description="Commit that introduced the change")
    author: str = Field(..., description="Author of the change")
    timestamp: datetime = Field(..., description="When the change was introduced")
    description: str = Field(..., description="Description of why this change is risky")
    risk_level: str = Field(..., description="Risk level assessment (low, medium, high)")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    recommendation: Optional[str] = Field(None, description="Recommendation for this risk")


# Response models for code/GitHub investigations
class CodeInvestigatorResponse(BaseInvestigatorResponse[Dict[str, Any]]):
    """Unified response model for all code investigation tasks
    
    This model can handle the results of any code investigation task,
    with specific helper methods for extracting different types of results.
    """
    # Type-specific data will be stored in the 'result' field
    # from the BaseInvestigatorResponse class
    
    def get_commits(self) -> List[Commit]:
        """Extract commits from a 'get_recent_commits' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Handle case where we might have raw dictionaries instead of model instances
        return [
            commit if isinstance(commit, Commit) else Commit.model_validate(commit)
            for commit in self.result
        ]
    
    def get_deployments(self) -> List[Deployment]:
        """Extract deployments from a 'get_recent_deployments' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Handle case where we might have raw dictionaries instead of model instances
        return [
            deployment if isinstance(deployment, Deployment) else Deployment.model_validate(deployment)
            for deployment in self.result
        ]
    
    def get_risky_changes(self) -> List[RiskyChange]:
        """Extract risky changes from an 'identify_risky_changes' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Handle case where we might have raw dictionaries instead of model instances
        return [
            change if isinstance(change, RiskyChange) else RiskyChange.model_validate(change)
            for change in self.result
        ]


# For backward compatibility, keep the original response models as type aliases
CommitResponse = CodeInvestigatorResponse
DeploymentResponse = CodeInvestigatorResponse
RiskyChangeResponse = CodeInvestigatorResponse


# Task Parameter Models for code/GitHub investigations
class CommitParameters(TaskParameters):
    """Parameters for recent commits task"""
    repo: str = Field(..., description="Repository to query")
    since: str = Field(..., description="Time period to look back (e.g., '24h', '7d')")
    reference_time: Optional[str] = Field(None, description="Reference time for relative times")
    branch: Optional[str] = Field(None, description="Branch to filter by")
    author: Optional[str] = Field(None, description="Author to filter by")


class DeploymentParameters(TaskParameters):
    """Parameters for recent deployments task"""
    service: str = Field(..., description="Service to query deployments for")
    since: str = Field(..., description="Time period to look back")
    reference_time: Optional[str] = Field(None, description="Reference time for relative times")
    environment: Optional[str] = Field(None, description="Environment to filter by")
    status: Optional[str] = Field(None, description="Status to filter by")


class RiskyChangeParameters(TaskParameters):
    """Parameters for identifying risky changes"""
    repo: str = Field(..., description="Repository to analyze")
    since: str = Field(..., description="Time period to look back")
    reference_time: Optional[str] = Field(None, description="Reference time for relative times")
    sensitivity: Optional[float] = Field(0.7, description="Sensitivity threshold (0-1)")
