import os
from typing import Dict, Any, List, Optional
from agno.tools import Tool, tool

class PrometheusTools(Tool):
    """Tool for interacting with Prometheus API.
    
    This tool allows agents to query Prometheus metrics to investigate
    system performance and identify anomalies during incidents.
    """
    name = "prometheus"
    description = "Tools for querying Prometheus metrics"
    
    def __init__(self, prometheus_url: Optional[str] = None):
        """Initialize the Prometheus tools with API URL.
        
        Args:
            prometheus_url: Optional URL for the Prometheus API.
                           If not provided, reads from PROMETHEUS_URL env var.
        """
        super().__init__()
        self.prometheus_url = prometheus_url or os.getenv("PROMETHEUS_URL")
        if not self.prometheus_url:
            raise ValueError("PROMETHEUS_URL environment variable is required")
    
    @tool("Query Prometheus instant metrics")
    def query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Query Prometheus for current metric values.
        
        Args:
            query: PromQL query string
            time: Optional time for the query (RFC3339 or Unix timestamp)
            
        Returns:
            Dict containing query results
        """
        # TODO: Implement actual Prometheus API call using requests
        # For now, return mock data for development
        return {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "__name__": "up",
                            "instance": "localhost:9090",
                            "job": "prometheus",
                        },
                        "value": [1712042800, "1"]
                    }
                ]
            }
        }
    
    @tool("Query Prometheus range metrics")
    def query_range(self, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """Query Prometheus for metric values over a time range.
        
        Args:
            query: PromQL query string
            start: Start time (RFC3339 or Unix timestamp)
            end: End time (RFC3339 or Unix timestamp)
            step: Query resolution step width (e.g., '15s', '1m', '1h')
            
        Returns:
            Dict containing query results over the time range
        """
        # TODO: Implement actual Prometheus API call
        # For now, return mock data for development
        return {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "cpu_usage_percent",
                            "instance": "web-server-01:9100",
                            "job": "node",
                        },
                        "values": [
                            [1712042700, "75.5"],
                            [1712042760, "82.3"],
                            [1712042820, "91.7"],
                            [1712042880, "95.2"],
                            [1712042940, "93.8"]
                        ]
                    }
                ]
            }
        }
    
    @tool("Get Prometheus targets health")
    def targets(self) -> Dict[str, Any]:
        """Get health and status information for all Prometheus targets.
        
        Returns:
            Dict containing information about active and dropped targets
        """
        # TODO: Implement actual Prometheus API call
        # For now, return mock data for development
        return {
            "status": "success",
            "data": {
                "activeTargets": [
                    {
                        "discoveredLabels": {
                            "__address__": "localhost:9090",
                            "__metrics_path__": "/metrics",
                            "__scheme__": "http",
                            "job": "prometheus"
                        },
                        "labels": {
                            "instance": "localhost:9090",
                            "job": "prometheus"
                        },
                        "scrapePool": "prometheus",
                        "scrapeUrl": "http://localhost:9090/metrics",
                        "health": "up",
                        "lastError": "",
                        "lastScrape": "2025-04-01T16:30:00Z",
                        "lastScrapeDuration": 0.015123125
                    },
                    {
                        "discoveredLabels": {
                            "__address__": "web-server-01:9100",
                            "__metrics_path__": "/metrics",
                            "__scheme__": "http",
                            "job": "node"
                        },
                        "labels": {
                            "instance": "web-server-01:9100",
                            "job": "node"
                        },
                        "scrapePool": "node",
                        "scrapeUrl": "http://web-server-01:9100/metrics",
                        "health": "up",
                        "lastError": "",
                        "lastScrape": "2025-04-01T16:29:45Z",
                        "lastScrapeDuration": 0.0098765
                    }
                ],
                "droppedTargets": []
            }
        }
    
    @tool("Get Prometheus alerts")
    def alerts(self) -> Dict[str, Any]:
        """Get currently firing alerts from Prometheus.
        
        Returns:
            Dict containing information about active alerts
        """
        # TODO: Implement actual Prometheus API call
        # For now, return mock data for development
        return {
            "status": "success",
            "data": {
                "alerts": [
                    {
                        "labels": {
                            "alertname": "HighCpuUsage",
                            "instance": "web-server-01:9100",
                            "job": "node",
                            "severity": "critical"
                        },
                        "annotations": {
                            "description": "CPU usage above 90% for 5 minutes",
                            "summary": "High CPU usage on web-server-01"
                        },
                        "state": "firing",
                        "activeAt": "2025-04-01T16:15:00Z",
                        "value": "95.2"
                    }
                ]
            }
        }
    
    @tool("Get recommended Prometheus queries for a service")
    def get_recommended_queries(self, service_name: str, issue_type: Optional[str] = None) -> List[Dict[str, str]]:
        """Get recommended Prometheus queries for investigating a specific service.
        
        Args:
            service_name: Name of the service to investigate
            issue_type: Optional type of issue to focus on (e.g., 'cpu', 'memory', 'disk', 'network')
            
        Returns:
            List of dicts containing query information
        """
        # This is a helper method that provides common queries for specific services
        # In a real implementation, this could be backed by a knowledge base
        
        base_queries = [
            {
                "name": "Service Availability",
                "query": f"up{{job=\'{service_name}\'}}\n",
                "description": "Checks if the service is up"
            },
            {
                "name": "Request Rate",
                "query": f"sum(rate(http_requests_total{{job=\'{service_name}\'}}[5m]))",
                "description": "Rate of HTTP requests over the last 5 minutes"
            },
            {
                "name": "Error Rate",
                "query": f"sum(rate(http_requests_total{{job=\'{service_name}\', status=~\'^5.*\'}}[5m])) / sum(rate(http_requests_total{{job=\'{service_name}\'}}[5m]))",
                "description": "Rate of 5xx errors over the last 5 minutes"
            },
            {
                "name": "Response Latency (p95)",
                "query": f"histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{job=\'{service_name}\'}}[5m])) by (le))",
                "description": "95th percentile of request duration"
            }
        ]
        
        # Add issue-specific queries if an issue type is specified
        if issue_type:
            if issue_type.lower() == "cpu":
                base_queries.extend([
                    {
                        "name": "CPU Usage",
                        "query": f"avg(rate(process_cpu_seconds_total{{job=\'{service_name}\'}}[5m]) * 100)",
                        "description": "Average CPU usage percentage"
                    },
                    {
                        "name": "CPU Throttling",
                        "query": f"rate(container_cpu_cfs_throttled_seconds_total{{name=~\'{service_name}.*\'}}[5m])",
                        "description": "CPU throttling events"
                    }
                ])
            elif issue_type.lower() == "memory":
                base_queries.extend([
                    {
                        "name": "Memory Usage",
                        "query": f"sum(container_memory_usage_bytes{{name=~\'{service_name}.*\'}}) by (container_name)",
                        "description": "Memory usage in bytes"
                    },
                    {
                        "name": "Memory Limit Percent",
                        "query": f"sum(container_memory_usage_bytes{{name=~\'{service_name}.*\'}}) / sum(container_spec_memory_limit_bytes{{name=~\'{service_name}.*\'}}) * 100",
                        "description": "Percentage of memory limit used"
                    }
                ])
            elif issue_type.lower() == "disk":
                base_queries.extend([
                    {
                        "name": "Disk Usage",
                        "query": f"node_filesystem_avail_bytes{{job=\'{service_name}\'}} / node_filesystem_size_bytes{{job=\'{service_name}\'}} * 100",
                        "description": "Available disk space percentage"
                    },
                    {
                        "name": "Disk I/O",
                        "query": f"rate(node_disk_io_time_seconds_total{{job=\'{service_name}\'}}[5m]) * 100",
                        "description": "Disk I/O utilization percentage"
                    }
                ])
            elif issue_type.lower() == "network":
                base_queries.extend([
                    {
                        "name": "Network Receive Throughput",
                        "query": f"rate(container_network_receive_bytes_total{{name=~\'{service_name}.*\'}}[5m])",
                        "description": "Network receive throughput"
                    },
                    {
                        "name": "Network Transmit Throughput",
                        "query": f"rate(container_network_transmit_bytes_total{{name=~\'{service_name}.*\'}}[5m])",
                        "description": "Network transmit throughput"
                    }
                ])
            elif issue_type.lower() == "database":
                base_queries.extend([
                    {
                        "name": "Database Connections",
                        "query": f"pg_stat_activity_count{{job=\'{service_name}\'}} or mysql_global_status_threads_connected{{job=\'{service_name}\'}}",
                        "description": "Number of active database connections"
                    },
                    {
                        "name": "Database Query Time",
                        "query": f"rate(pg_stat_activity_max_tx_duration{{job=\'{service_name}\'}}[5m]) or mysql_global_status_slow_queries{{job=\'{service_name}\'}}",
                        "description": "Database query execution time or slow query count"
                    }
                ])
        
        return base_queries
