from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ack_agent.schemas.base import BaseInvestigatorResponse, TaskParameters


class PodStatus(BaseModel):
    """Model representing the status of a Kubernetes pod"""
    name: str = Field(..., description="Name of the pod")
    namespace: str = Field(..., description="Namespace the pod belongs to")
    status: str = Field(..., description="Current status (Running, Pending, Failed, etc.)")
    ready: bool = Field(..., description="Whether the pod is ready")
    restarts: int = Field(0, description="Number of times the pod has restarted")
    age: str = Field(..., description="Age of the pod")
    reason: Optional[str] = Field(None, description="Reason for current status, if applicable")
    message: Optional[str] = Field(None, description="Detailed message about the current status")
    node: Optional[str] = Field(None, description="Node the pod is running on")
    labels: Dict[str, str] = Field(default_factory=dict, description="Pod labels")
    containers: List[str] = Field(default_factory=list, description="Names of containers in the pod")


class K8sEvent(BaseModel):
    """Model representing a Kubernetes event"""
    type: str = Field(..., description="Event type (Normal or Warning)")
    reason: str = Field(..., description="Short reason for the event")
    message: str = Field(..., description="Detailed message")
    object: str = Field(..., description="Object the event is about")
    timestamp: datetime = Field(..., description="When the event occurred")
    count: int = Field(1, description="Number of times this event has occurred")
    source: Optional[str] = Field(None, description="Component that generated the event")


class ResourceUsage(BaseModel):
    """Model representing resource usage of a node or pod"""
    name: str = Field(..., description="Name of the node or pod")
    cpu_usage: float = Field(..., description="CPU usage percentage (0-100)")
    memory_usage: float = Field(..., description="Memory usage percentage (0-100)")
    cpu_pressure: bool = Field(False, description="Whether the node is under CPU pressure")
    memory_pressure: bool = Field(False, description="Whether the node is under memory pressure")
    disk_pressure: bool = Field(False, description="Whether the node is under disk pressure")
    pid_pressure: bool = Field(False, description="Whether the node is under PID pressure")
    node_name: str = Field(..., description="Name of the node")
    cpu_requests: Optional[str] = Field(None, description="CPU requests")
    cpu_limits: Optional[str] = Field(None, description="CPU limits")
    memory_requests: Optional[str] = Field(None, description="Memory requests")
    memory_limits: Optional[str] = Field(None, description="Memory limits")


class DeploymentInfo(BaseModel):
    """Model representing a Kubernetes deployment"""
    name: str = Field(..., description="Name of the deployment")
    namespace: str = Field(..., description="Namespace the deployment belongs to")
    ready: str = Field(..., description="Ready replicas (format: ready/total)")
    up_to_date: int = Field(..., description="Number of up-to-date replicas")
    available: int = Field(..., description="Number of available replicas")
    age: str = Field(..., description="Age of the deployment")
    image: str = Field(..., description="Container image used")
    replicas: int = Field(..., description="Total number of desired replicas")
    revision: Optional[str] = Field(None, description="Deployment revision")
    strategy: Optional[str] = Field(None, description="Deployment strategy")
    last_updated: Optional[datetime] = Field(None, description="When the deployment was last updated")


# Type-specific response models
class KubernetesInvestigatorResponse(BaseInvestigatorResponse[Dict[str, Any]]):
    """Unified response model for all Kubernetes investigation tasks
    
    This model can handle the results of any Kubernetes investigation task,
    with specific helper methods for extracting different types of results.
    """
    # Type-specific result data will be stored in the 'result' field
    # from the BaseInvestigatorResponse class
    
    def get_pod_status(self) -> Dict[str, List[PodStatus]]:
        """Extract pod status results from a 'check_pod_status' task"""
        if not self.is_success():
            return {"healthy_pods": [], "unhealthy_pods": []}
        
        # Convert dict results to PodStatus objects if they aren't already
        result = self.result or {"healthy_pods": [], "unhealthy_pods": []}
        
        # Handle case where we might have raw dictionaries instead of model instances
        healthy_pods = [
            pod if isinstance(pod, PodStatus) else PodStatus.model_validate(pod)
            for pod in result.get("healthy_pods", [])
        ]
        unhealthy_pods = [
            pod if isinstance(pod, PodStatus) else PodStatus.model_validate(pod)
            for pod in result.get("unhealthy_pods", [])
        ]
        
        return {"healthy_pods": healthy_pods, "unhealthy_pods": unhealthy_pods}
    
    def get_events(self) -> List[K8sEvent]:
        """Extract Kubernetes events from a 'get_events' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Convert dict results to K8sEvent objects if they aren't already
        return [
            event if isinstance(event, K8sEvent) else K8sEvent.model_validate(event)
            for event in self.result
        ]
    
    def get_resource_usage(self) -> List[ResourceUsage]:
        """Extract resource usage metrics from a 'check_resource_usage' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Convert dict results to ResourceUsage objects if they aren't already
        return [
            resource if isinstance(resource, ResourceUsage) else ResourceUsage.model_validate(resource)
            for resource in self.result
        ]
    
    def get_deployment_info(self) -> List[DeploymentInfo]:
        """Extract deployment information from a 'check_deployment_status' task"""
        if not self.is_success() or not self.result:
            return []
        
        # Convert dict results to DeploymentInfo objects if they aren't already
        return [
            deployment if isinstance(deployment, DeploymentInfo) else DeploymentInfo.model_validate(deployment)
            for deployment in self.result
        ]


# For backward compatibility, keep the original response models as type aliases
PodStatusResponse = KubernetesInvestigatorResponse
EventsResponse = KubernetesInvestigatorResponse
ResourceUsageResponse = KubernetesInvestigatorResponse
DeploymentStatusResponse = KubernetesInvestigatorResponse


# Task Parameter Models for Kubernetes investigations
class PodStatusParameters(TaskParameters):
    """Parameters for pod status check task"""
    service_name: str = Field(..., description="Name of the service to check pods for")
    namespace: Optional[str] = Field(None, description="Namespace to filter by")
    label_selector: Optional[str] = Field(None, description="Label selector to filter pods")


class EventsParameters(TaskParameters):
    """Parameters for Kubernetes events task"""
    service_name: str = Field(..., description="Name of the service to get events for")
    namespace: Optional[str] = Field(None, description="Namespace to filter by")
    time_range: Optional[str] = Field(None, description="Time range for events (e.g., '1h')")
    event_types: Optional[List[str]] = Field(None, description="Types of events to include")


class ResourceUsageParameters(TaskParameters):
    """Parameters for resource usage check task"""
    service_name: str = Field(..., description="Name of the service to check resource usage for")
    namespace: Optional[str] = Field(None, description="Namespace to filter by")
    include_nodes: bool = Field(True, description="Whether to include node metrics")


class DeploymentStatusParameters(TaskParameters):
    """Parameters for deployment status check task"""
    service_name: str = Field(..., description="Name of the service to check deployment status for")
    namespace: Optional[str] = Field(None, description="Namespace to filter by")
