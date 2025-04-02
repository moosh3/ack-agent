from typing import Generic, TypeVar, Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

# Define a generic type variable for the result
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Standardized status values for investigator responses"""
    SUCCESS = "success"  # Investigation completed successfully
    ERROR = "error"      # Investigation failed to complete
    PARTIAL = "partial"  # Investigation completed with partial results


class BaseInvestigatorResponse(BaseModel, Generic[T]):
    """Base model for all investigator responses
    
    This provides a standardized structure for all investigator agents to return
    results, with consistent error handling, timing information, and metadata.
    
    Generic type T represents the specific result type for each investigator.
    """
    status: ResponseStatus = Field(
        default=ResponseStatus.SUCCESS,
        description="Status of the investigation task"
    )
    task_id: str = Field(
        ...,  # Required field
        description="Unique identifier for the specific task instance"
    )
    task_name: str = Field(
        ...,  # Required field
        description="The name of the task that was executed"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated (UTC)"
    )
    execution_time_ms: Optional[int] = Field(
        default=None,
        description="How long the task took to execute in milliseconds"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if the status is ERROR or PARTIAL"
    )
    result: Optional[T] = Field(
        default=None,
        description="The main result payload from the investigation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional contextual information about the response"
    )
    
    @field_validator('error_message')
    def validate_error_message(cls, v, info):
        """Ensure error message is present when status is ERROR"""
        if info.data.get('status') == ResponseStatus.ERROR and not v:
            raise ValueError("Error message is required when status is ERROR")
        return v
    
    def is_success(self) -> bool:
        """Convenience method to check if the response was successful"""
        return self.status == ResponseStatus.SUCCESS
    
    def is_error(self) -> bool:
        """Convenience method to check if the response has an error"""
        return self.status == ResponseStatus.ERROR
    
    def is_partial(self) -> bool:
        """Convenience method to check if the response is partial"""
        return self.status == ResponseStatus.PARTIAL


class TaskParameters(BaseModel):
    """Base model for task parameters
    
    This serves as a base for type checking parameters sent to investigator agents.
    Each task should define its own subclass with specific required parameters.
    """
    pass
