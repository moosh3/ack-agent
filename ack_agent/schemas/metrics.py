from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ack_agent.schemas.base import BaseInvestigatorResponse, TaskParameters


class MetricDataPoint(BaseModel):
    """Model representing a single metric data point"""
    timestamp: datetime = Field(..., description="Timestamp for this data point")
    value: float = Field(..., description="Metric value at this timestamp")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")


class MetricSeries(BaseModel):
    """Model representing a time series of metric data points"""
    metric_name: str = Field(..., description="Name of the metric")
    data_points: List[MetricDataPoint] = Field(..., description="Series of data points")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    labels: Dict[str, str] = Field(default_factory=dict, description="Common labels for all points in series")
    
    def get_current_value(self) -> Optional[float]:
        """Get the most recent value in the series"""
        if not self.data_points:
            return None
        return max(self.data_points, key=lambda p: p.timestamp).value
    
    def get_average(self) -> Optional[float]:
        """Get the average value across the series"""
        if not self.data_points:
            return None
        return sum(p.value for p in self.data_points) / len(self.data_points)
    
    def get_peak(self) -> Optional[float]:
        """Get the peak value in the series"""
        if not self.data_points:
            return None
        return max(p.value for p in self.data_points)


class MetricAnomaly(BaseModel):
    """Model representing an anomaly detected in metrics"""
    metric: str = Field(..., description="Name of the metric with the anomaly")
    timestamp: datetime = Field(..., description="When the anomaly was detected")
    expected_value: Optional[float] = Field(None, description="Expected value based on baseline")
    actual_value: float = Field(..., description="Actual value observed")
    deviation_percentage: float = Field(..., description="Percentage deviation from expected")
    description: str = Field(..., description="Human-readable description of the anomaly")
    severity: str = Field(..., description="Severity of the anomaly (low, medium, high)")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels for the anomaly")


class ResourceBottleneck(BaseModel):
    """Model representing a resource bottleneck"""
    resource_type: str = Field(..., description="Type of resource (cpu, memory, disk, network)")
    component: str = Field(..., description="Component experiencing the bottleneck")
    utilization: float = Field(..., description="Current utilization percentage")
    threshold: float = Field(..., description="Threshold for bottleneck determination")
    description: str = Field(..., description="Description of the bottleneck")
    impact: Optional[str] = Field(None, description="Potential impact of this bottleneck")
    recommendation: Optional[str] = Field(None, description="Recommendation to address the bottleneck")


class QueryResult(BaseModel):
    """Model representing a result from a metric query"""
    query_name: str = Field(..., description="Name or identifier for this query")
    query: str = Field(..., description="The actual query that was executed")
    series: List[MetricSeries] = Field(default_factory=list, description="Time series results")
    execution_time_ms: Optional[int] = Field(None, description="Query execution time in milliseconds")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of the query results")


# Response models for metrics investigations
class MetricsInvestigatorResponse(BaseInvestigatorResponse[Dict[str, Any]]):
    """Unified response model for all metrics investigation tasks
    
    This model can handle the results of any metrics investigation task,
    with specific helper methods for extracting different types of results.
    """
    # Type-specific data will be stored in the 'result' field
    # from the BaseInvestigatorResponse class
    
    def get_query_results(self) -> Dict[str, QueryResult]:
        """Extract query results from a 'run_queries' task"""
        if not self.is_success() or not self.result:
            return {}
        
        # Handle case where we might have raw dictionaries instead of model instances
        return {
            query_name: 
                result if isinstance(result, QueryResult) else QueryResult.model_validate(result)
            for query_name, result in self.result.items()
        }
    
    def get_anomalies(self) -> List[MetricAnomaly]:
        """Extract metric anomalies from a 'detect_anomalies' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Handle case where we might have raw dictionaries instead of model instances
        return [
            anomaly if isinstance(anomaly, MetricAnomaly) else MetricAnomaly.model_validate(anomaly)
            for anomaly in self.result
        ]
    
    def get_bottlenecks(self) -> Dict[str, ResourceBottleneck]:
        """Extract resource bottlenecks from an 'identify_bottlenecks' task"""
        if not self.is_success() or not self.result:
            return {}
        
        # Handle case where we might have raw dictionaries instead of model instances
        return {
            resource_type: 
                bottleneck if isinstance(bottleneck, ResourceBottleneck) else ResourceBottleneck.model_validate(bottleneck)
            for resource_type, bottleneck in self.result.items()
        }


# For backward compatibility, keep the original response models as type aliases
QueryResponse = MetricsInvestigatorResponse
AnomalyResponse = MetricsInvestigatorResponse
BottleneckResponse = MetricsInvestigatorResponse


# Task Parameter Models for metrics investigations
class MetricQueryParameters(TaskParameters):
    """Parameters for metric query task"""
    query: str = Field(..., description="The query to execute")
    start: str = Field(..., description="Start time for the query range")
    end: str = Field(..., description="End time for the query range")
    step: str = Field("1m", description="Step size for the query")


class RecommendedQueriesParameters(TaskParameters):
    """Parameters for getting recommended queries"""
    service_name: str = Field(..., description="Service to get recommended queries for")
    category: Optional[List[str]] = Field(None, description="Categories of metrics to include")


class AnomalyDetectionParameters(TaskParameters):
    """Parameters for anomaly detection task"""
    service_name: str = Field(..., description="Service to detect anomalies for")
    start: str = Field(..., description="Start time for analysis")
    end: str = Field(..., description="End time for analysis")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to analyze")
    sensitivity: Optional[float] = Field(2.0, description="Sensitivity of anomaly detection (higher = more sensitive)")


class BottleneckParameters(TaskParameters):
    """Parameters for bottleneck identification task"""
    service_name: str = Field(..., description="Service to identify bottlenecks for")
    time_range: str = Field(..., description="Time range for analysis")
    include_recommendations: Optional[bool] = Field(True, description="Whether to include recommendations")
