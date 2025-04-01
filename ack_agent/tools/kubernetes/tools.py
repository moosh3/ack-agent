import os
from typing import Dict, Any, List, Optional
from agno.tools import Tool, tool

class KubernetesTools(Tool):
    """Tool for interacting with Kubernetes API to monitor cluster health.
    
    This tool allows agents to retrieve information about Kubernetes resources
    such as pods, nodes, deployments, and events to diagnose infrastructure issues
    during incidents.
    """
    name = "kubernetes"
    description = "Tools for querying Kubernetes resources and events"
    
    def __init__(self, kubeconfig: Optional[str] = None):
        """Initialize the Kubernetes tools with configuration.
        
        Args:
            kubeconfig: Optional path to kubeconfig file.
                        If not provided, reads from KUBERNETES_CONFIG env var or default location.
        """
        super().__init__()
        self.kubeconfig = kubeconfig or os.getenv("KUBERNETES_CONFIG") or os.path.expanduser("~/.kube/config")
        # In a real implementation, we would create a Kubernetes client here
        # self.client = kubernetes.client.CoreV1Api()
    
    @tool("Get Kubernetes pod status")
    def get_pod(self, namespace: str, name: str) -> Dict[str, Any]:
        """Get details about a specific Kubernetes pod.
        
        Args:
            namespace: Kubernetes namespace
            name: Pod name
            
        Returns:
            Dict containing pod details
        """
        # TODO: Implement actual Kubernetes API call using kubernetes client
        # For now, return mock data for development
        return {
            "metadata": {
                "name": name,
                "namespace": namespace,
                "uid": "pod-uid-123",
                "creationTimestamp": "2025-04-01T15:00:00Z"
            },
            "spec": {
                "containers": [
                    {
                        "name": "app",
                        "image": "app-image:latest",
                        "resources": {
                            "limits": {
                                "cpu": "1",
                                "memory": "1Gi"
                            },
                            "requests": {
                                "cpu": "500m",
                                "memory": "512Mi"
                            }
                        }
                    }
                ],
                "nodeName": "node-123"
            },
            "status": {
                "phase": "Running",
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "True",
                        "lastTransitionTime": "2025-04-01T15:01:00Z"
                    }
                ],
                "containerStatuses": [
                    {
                        "name": "app",
                        "ready": True,
                        "restartCount": 0,
                        "state": {
                            "running": {
                                "startedAt": "2025-04-01T15:01:00Z"
                            }
                        }
                    }
                ],
                "hostIP": "192.168.1.10",
                "podIP": "10.0.0.15"
            }
        }
    
    @tool("List Kubernetes pods")
    def list_pods(self, namespace: str, label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List pods in a Kubernetes namespace, optionally filtered by labels.
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Optional label selector (e.g., "app=backend,env=prod")
            
        Returns:
            Dict containing list of pods
        """
        # TODO: Implement actual Kubernetes API call
        # For now, return mock data for development
        return {
            "items": [
                {
                    "metadata": {
                        "name": "app-backend-5d8b9f8f5d-abcde",
                        "namespace": namespace,
                        "labels": {
                            "app": "backend",
                            "pod-template-hash": "5d8b9f8f5d"
                        }
                    },
                    "status": {
                        "phase": "Running",
                        "podIP": "10.0.0.15",
                        "containerStatuses": [
                            {
                                "name": "backend",
                                "ready": True,
                                "restartCount": 0
                            }
                        ]
                    }
                },
                {
                    "metadata": {
                        "name": "app-backend-5d8b9f8f5d-fghij",
                        "namespace": namespace,
                        "labels": {
                            "app": "backend",
                            "pod-template-hash": "5d8b9f8f5d"
                        }
                    },
                    "status": {
                        "phase": "Pending",
                        "conditions": [
                            {
                                "type": "PodScheduled",
                                "status": "False",
                                "reason": "Unschedulable",
                                "message": "0/3 nodes are available: 3 Insufficient memory."
                            }
                        ]
                    }
                }
            ]
        }
    
    @tool("Get Kubernetes node status")
    def get_node(self, name: str) -> Dict[str, Any]:
        """Get details about a specific Kubernetes node.
        
        Args:
            name: Node name
            
        Returns:
            Dict containing node details
        """
        # TODO: Implement actual Kubernetes API call
        # For now, return mock data for development
        return {
            "metadata": {
                "name": name,
                "uid": "node-uid-123",
                "labels": {
                    "kubernetes.io/hostname": name,
                    "node-role.kubernetes.io/worker": ""
                }
            },
            "spec": {
                "podCIDR": "10.0.0.0/24",
                "taints": []
            },
            "status": {
                "capacity": {
                    "cpu": "8",
                    "memory": "32Gi",
                    "pods": "110"
                },
                "allocatable": {
                    "cpu": "7800m",
                    "memory": "30Gi",
                    "pods": "110"
                },
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "True",
                        "lastHeartbeatTime": "2025-04-01T16:25:00Z",
                        "lastTransitionTime": "2025-04-01T08:00:00Z",
                        "reason": "",
                        "message": ""
                    },
                    {
                        "type": "MemoryPressure",
                        "status": "False",
                        "lastHeartbeatTime": "2025-04-01T16:25:00Z",
                        "lastTransitionTime": "2025-04-01T08:00:00Z",
                        "reason": "",
                        "message": ""
                    },
                    {
                        "type": "DiskPressure",
                        "status": "False",
                        "lastHeartbeatTime": "2025-04-01T16:25:00Z",
                        "lastTransitionTime": "2025-04-01T08:00:00Z",
                        "reason": "",
                        "message": ""
                    },
                    {
                        "type": "PIDPressure",
                        "status": "False",
                        "lastHeartbeatTime": "2025-04-01T16:25:00Z",
                        "lastTransitionTime": "2025-04-01T08:00:00Z",
                        "reason": "",
                        "message": ""
                    }
                ],
                "addresses": [
                    {
                        "type": "InternalIP",
                        "address": "192.168.1.10"
                    },
                    {
                        "type": "Hostname",
                        "address": name
                    }
                ]
            }
        }
    
    @tool("List Kubernetes nodes")
    def list_nodes(self, label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List all Kubernetes nodes, optionally filtered by labels.
        
        Args:
            label_selector: Optional label selector (e.g., "node-role.kubernetes.io/worker=")
            
        Returns:
            Dict containing list of nodes
        """
        # TODO: Implement actual Kubernetes API call
        # For now, return mock data for development
        return {
            "items": [
                {
                    "metadata": {
                        "name": "node-1",
                        "labels": {
                            "kubernetes.io/hostname": "node-1",
                            "node-role.kubernetes.io/worker": ""
                        }
                    },
                    "status": {
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "True"
                            }
                        ]
                    }
                },
                {
                    "metadata": {
                        "name": "node-2",
                        "labels": {
                            "kubernetes.io/hostname": "node-2",
                            "node-role.kubernetes.io/worker": ""
                        }
                    },
                    "status": {
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "True"
                            }
                        ]
                    }
                },
                {
                    "metadata": {
                        "name": "node-3",
                        "labels": {
                            "kubernetes.io/hostname": "node-3",
                            "node-role.kubernetes.io/worker": ""
                        }
                    },
                    "status": {
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "False",
                                "reason": "KubeletNotReady",
                                "message": "PLEG is not healthy"
                            }
                        ]
                    }
                }
            ]
        }
    
    @tool("Get Kubernetes events")
    def get_events(self, namespace: Optional[str] = None, field_selector: Optional[str] = None) -> Dict[str, Any]:
        """Get Kubernetes events, optionally filtered by namespace or fields.
        
        Args:
            namespace: Optional Kubernetes namespace
            field_selector: Optional field selector (e.g., "involvedObject.name=pod-name")
            
        Returns:
            Dict containing list of events
        """
        # TODO: Implement actual Kubernetes API call
        # For now, return mock data for development
        return {
            "items": [
                {
                    "metadata": {
                        "name": "app-backend-5d8b9f8f5d-fghij.1712042700",
                        "namespace": namespace or "default"
                    },
                    "involvedObject": {
                        "kind": "Pod",
                        "namespace": namespace or "default",
                        "name": "app-backend-5d8b9f8f5d-fghij"
                    },
                    "reason": "FailedScheduling",
                    "message": "0/3 nodes are available: 3 Insufficient memory.",
                    "source": {
                        "component": "default-scheduler"
                    },
                    "firstTimestamp": "2025-04-01T16:05:00Z",
                    "lastTimestamp": "2025-04-01T16:15:00Z",
                    "count": 5,
                    "type": "Warning"
                },
                {
                    "metadata": {
                        "name": "node-3.1712042400",
                        "namespace": "default"
                    },
                    "involvedObject": {
                        "kind": "Node",
                        "name": "node-3"
                    },
                    "reason": "NodeNotReady",
                    "message": "Node node-3 status is now: NodeNotReady",
                    "source": {
                        "component": "node-controller"
                    },
                    "firstTimestamp": "2025-04-01T16:00:00Z",
                    "lastTimestamp": "2025-04-01T16:00:00Z",
                    "count": 1,
                    "type": "Warning"
                }
            ]
        }
    
    @tool("Get Kubernetes deployment status")
    def get_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        """Get details about a specific Kubernetes deployment.
        
        Args:
            namespace: Kubernetes namespace
            name: Deployment name
            
        Returns:
            Dict containing deployment details
        """
        # TODO: Implement actual Kubernetes API call
        # For now, return mock data for development
        return {
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {
                    "app": name
                }
            },
            "spec": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": name
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": name,
                                "image": f"{name}:latest"
                            }
                        ]
                    }
                }
            },
            "status": {
                "replicas": 3,
                "updatedReplicas": 3,
                "readyReplicas": 2,
                "availableReplicas": 2,
                "unavailableReplicas": 1,
                "conditions": [
                    {
                        "type": "Available",
                        "status": "True",
                        "reason": "MinimumReplicasAvailable",
                        "message": "Deployment has minimum availability.",
                        "lastTransitionTime": "2025-04-01T15:30:00Z"
                    },
                    {
                        "type": "Progressing",
                        "status": "True",
                        "reason": "ReplicaSetUpdated",
                        "message": "ReplicaSet has been successfully updated.",
                        "lastTransitionTime": "2025-04-01T15:30:00Z"
                    }
                ]
            }
        }
    
    @tool("Get Kubernetes logs")
    def get_logs(self, namespace: str, pod_name: str, container_name: Optional[str] = None, 
                previous: bool = False, tail_lines: int = 100) -> Dict[str, Any]:
        """Get logs from a Kubernetes pod.
        
        Args:
            namespace: Kubernetes namespace
            pod_name: Pod name
            container_name: Optional container name (required for multi-container pods)
            previous: Whether to retrieve logs from previous container instance
            tail_lines: Number of lines to retrieve from the end of the logs
            
        Returns:
            Dict containing log content
        """
        # TODO: Implement actual Kubernetes API call
        # For now, return mock data for development
        
        # Create some sample log lines relevant to our scenario
        log_lines = [
            "2025-04-01T16:14:50Z INFO  Starting application server",
            "2025-04-01T16:14:52Z INFO  Connected to database successfully",
            "2025-04-01T16:14:55Z INFO  Initialized 8 connection pool threads",
            "2025-04-01T16:15:00Z INFO  Processing request GET /api/users",
            "2025-04-01T16:15:01Z WARN  High database query time: 1.5s for getUserList",
            "2025-04-01T16:15:10Z INFO  Processing request GET /api/products",
            "2025-04-01T16:15:12Z ERROR Failed to execute database query: Connection timed out",
            "2025-04-01T16:15:13Z ERROR Database connection lost: Connection reset by peer",
            "2025-04-01T16:15:14Z WARN  Retrying database connection (attempt 1/5)",
            "2025-04-01T16:15:15Z ERROR Failed to reconnect to database: Too many connections",
            "2025-04-01T16:15:16Z WARN  Retrying database connection (attempt 2/5)",
            "2025-04-01T16:15:17Z ERROR Failed to reconnect to database: Too many connections",
            "2025-04-01T16:15:18Z WARN  Retrying database connection (attempt 3/5)",
            "2025-04-01T16:15:19Z ERROR Failed to reconnect to database: Too many connections",
            "2025-04-01T16:15:20Z WARN  Retrying database connection (attempt 4/5)",
            "2025-04-01T16:15:21Z ERROR Failed to reconnect to database: Too many connections",
            "2025-04-01T16:15:22Z WARN  Retrying database connection (attempt 5/5)",
            "2025-04-01T16:15:23Z ERROR Failed to reconnect to database: Too many connections",
            "2025-04-01T16:15:24Z ERROR Maximum connection retries exceeded, giving up",
            "2025-04-01T16:15:25Z FATAL Application shutting down due to persistent database connectivity issues"
        ]
        
        # Limit to requested number of lines
        if tail_lines < len(log_lines):
            log_lines = log_lines[-tail_lines:]
        
        return {
            "pod_name": pod_name,
            "container_name": container_name or "app",
            "namespace": namespace,
            "previous": previous,
            "logs": "\n".join(log_lines)
        }
    
    @tool("Analyze Kubernetes cluster health")
    def analyze_cluster_health(self) -> Dict[str, Any]:
        """Analyze overall Kubernetes cluster health across nodes and components.
        
        This is a higher-level function that aggregates information about the cluster
        to provide a comprehensive health assessment.
        
        Returns:
            Dict containing cluster health analysis
        """
        # TODO: Implement actual Kubernetes API calls to collect and analyze data
        # For now, return mock analysis for development
        return {
            "overall_status": "Warning",
            "node_status": {
                "total": 3,
                "ready": 2,
                "not_ready": 1,
                "issues": [
                    {
                        "node": "node-3",
                        "status": "NotReady",
                        "reason": "KubeletNotReady",
                        "message": "PLEG is not healthy"
                    }
                ]
            },
            "pod_status": {
                "total": 50,
                "running": 45,
                "pending": 3,
                "failed": 2,
                "issues": [
                    {
                        "namespace": "default",
                        "name": "app-backend-5d8b9f8f5d-fghij",
                        "status": "Pending",
                        "reason": "Unschedulable",
                        "message": "0/3 nodes are available: 3 Insufficient memory."
                    },
                    {
                        "namespace": "default",
                        "name": "database-0",
                        "status": "CrashLoopBackOff",
                        "reason": "Error",
                        "message": "Back-off restarting failed container"
                    }
                ]
            },
            "component_status": {
                "scheduler": "Healthy",
                "controller-manager": "Healthy",
                "etcd-0": "Healthy"
            },
            "recent_events": [
                {
                    "reason": "NodeNotReady",
                    "object": "Node/node-3",
                    "message": "Node node-3 status is now: NodeNotReady",
                    "count": 1,
                    "type": "Warning",
                    "timestamp": "2025-04-01T16:00:00Z"
                },
                {
                    "reason": "FailedScheduling",
                    "object": "Pod/app-backend-5d8b9f8f5d-fghij",
                    "message": "0/3 nodes are available: 3 Insufficient memory.",
                    "count": 5,
                    "type": "Warning",
                    "timestamp": "2025-04-01T16:15:00Z"
                }
            ]
        }
