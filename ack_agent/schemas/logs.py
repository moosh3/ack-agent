from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ack_agent.schemas.base import BaseInvestigatorResponse, TaskParameters


class LogEntry(BaseModel):
    """Model representing a single log entry"""
    timestamp: datetime = Field(..., description="When the log entry was generated")
    level: str = Field(..., description="Log level (INFO, ERROR, WARNING, etc.)")
    message: str = Field(..., description="Log message text")
    service: str = Field(..., description="Service that generated the log")
    component: Optional[str] = Field(None, description="Component within the service")
    trace_id: Optional[str] = Field(None, description="Distributed tracing ID if available")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional log attributes")
    
    def is_error(self) -> bool:
        """Check if this log entry indicates an error"""
        return self.level.upper() in ["ERROR", "CRITICAL", "FATAL", "SEVERE"]
    
    def is_warning(self) -> bool:
        """Check if this log entry indicates a warning"""
        return self.level.upper() in ["WARNING", "WARN"]


class ExceptionPattern(BaseModel):
    """Model representing a recurring exception pattern"""
    pattern: str = Field(..., description="The exception pattern identified")
    count: int = Field(..., description="Number of occurrences of this pattern")
    examples: List[str] = Field(default_factory=list, description="Example log messages matching this pattern")
    first_seen: Optional[datetime] = Field(None, description="When this pattern was first observed")
    last_seen: Optional[datetime] = Field(None, description="When this pattern was last observed")
    severity: Optional[str] = Field(None, description="Estimated severity of this exception")
    related_components: List[str] = Field(default_factory=list, description="Components associated with this pattern")


class LogVolumePoint(BaseModel):
    """Model representing a single point in a log volume time series"""
    timestamp: datetime = Field(..., description="Timestamp for this data point")
    count: int = Field(..., description="Number of log entries at this time")
    baseline: Optional[int] = Field(None, description="Expected baseline count for this time")
    deviation_percentage: Optional[float] = Field(None, description="Percentage deviation from baseline")
    level_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of log counts by level (ERROR, INFO, etc.)")


class LogVolumeSummary(BaseModel):
    """Summary of log volume analysis"""
    time_series: List[LogVolumePoint] = Field(..., description="Time series data points")
    anomalies: bool = Field(False, description="Whether anomalies were detected")
    anomaly_periods: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Periods where anomalies were detected")
    peak_time: Optional[datetime] = Field(None, description="Time of peak log volume")
    peak_count: Optional[int] = Field(None, description="Count at peak volume")
    average_count: Optional[float] = Field(None, description="Average log count in period")


# Response models for log investigations
class LogsInvestigatorResponse(BaseInvestigatorResponse[Dict[str, Any]]):
    """Unified response model for all log investigation tasks
    
    This model can handle the results of any log investigation task,
    with specific helper methods for extracting different types of results.
    """
    # Type-specific data will be stored in the 'result' field
    # from the BaseInvestigatorResponse class
    total_count: Optional[int] = Field(
        None,
        description="Total count of logs matching query (may be more than returned)"
    )
    
    def get_log_entries(self) -> List[LogEntry]:
        """Extract log entries from a 'search_logs' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Handle case where we might have raw dictionaries instead of model instances
        return [
            entry if isinstance(entry, LogEntry) else LogEntry.model_validate(entry)
            for entry in self.result
        ]
    
    def get_patterns(self) -> List[ExceptionPattern]:
        """Extract exception patterns from a 'extract_patterns' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Handle case where we might have raw dictionaries instead of model instances
        return [
            pattern if isinstance(pattern, ExceptionPattern) else ExceptionPattern.model_validate(pattern)
            for pattern in self.result
        ]
    
    def get_volume_analysis(self) -> Optional[LogVolumeSummary]:
        """Extract log volume analysis from a 'analyze_volume' task"""
        if not self.is_success() or not self.result:
            return None
        
        # Handle case where we might have a raw dictionary instead of a model instance
        if isinstance(self.result, LogVolumeSummary):
            return self.result
        else:
            return LogVolumeSummary.model_validate(self.result)


# For backward compatibility, keep the original response models as type aliases
LogsResponse = LogsInvestigatorResponse
PatternResponse = LogsInvestigatorResponse
VolumeAnalysisResponse = LogsInvestigatorResponse


# Task Parameter Models for log investigations
class LogSearchParameters(TaskParameters):
    """Parameters for log search task"""
    query: str = Field(..., description="Search query")
    time_range: str = Field(..., description="Time range for search")
    reference_time: Optional[str] = Field(None, description="Reference time for relative time ranges")
    max_results: Optional[int] = Field(1000, description="Maximum number of results to return")
    filter_levels: Optional[List[str]] = Field(None, description="Filter by log levels")


class PatternExtractionParameters(TaskParameters):
    """Parameters for pattern extraction task"""
    query: str = Field(..., description="Search query to find patterns within")
    time_range: str = Field(..., description="Time range for analysis")
    reference_time: Optional[str] = Field(None, description="Reference time for relative time ranges")
    min_occurrences: Optional[int] = Field(3, description="Minimum occurrences to identify a pattern")


class LogVolumeParameters(TaskParameters):
    """Parameters for log volume analysis task"""
    query: str = Field(..., description="Base query for log volume analysis")
    time_range: str = Field(..., description="Time range for analysis")
    reference_time: Optional[str] = Field(None, description="Reference time for relative time ranges")
    interval: Optional[str] = Field("5m", description="Interval for time buckets")
    detect_anomalies: Optional[bool] = Field(True, description="Whether to detect anomalies")
