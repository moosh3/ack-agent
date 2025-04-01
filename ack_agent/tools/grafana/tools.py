import os
from typing import Dict, Any, List, Optional
from agno.tools import Tool, tool

class GrafanaTools(Tool):
    """Tool for interacting with Grafana API for dashboard visualization.
    
    This tool allows agents to retrieve Grafana dashboards and panels
    to visualize system state during incidents.
    """
    name = "grafana"
    description = "Tools for retrieving Grafana dashboards and visualizations"
    
    def __init__(self, grafana_url: Optional[str] = None, grafana_token: Optional[str] = None):
        """Initialize the Grafana tools with API URL and token.
        
        Args:
            grafana_url: Optional URL for the Grafana API.
                        If not provided, reads from GRAFANA_URL env var.
            grafana_token: Optional authentication token for Grafana.
                          If not provided, reads from GRAFANA_TOKEN env var.
        """
        super().__init__()
        self.grafana_url = grafana_url or os.getenv("GRAFANA_URL")
        self.grafana_token = grafana_token or os.getenv("GRAFANA_TOKEN")
        if not self.grafana_url or not self.grafana_token:
            raise ValueError("GRAFANA_URL and GRAFANA_TOKEN environment variables are required")
    
    @tool("Search Grafana dashboards")
    def search_dashboards(self, query: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for Grafana dashboards.
        
        Args:
            query: Optional search query string
            tags: Optional list of dashboard tags to filter by
            
        Returns:
            Dict containing search results
        """
        # TODO: Implement actual Grafana API call using requests
        # For now, return mock data for development
        return {
            "dashboards": [
                {
                    "id": 1,
                    "uid": "cIBgcSjkk",
                    "title": "Web Application Overview",
                    "uri": "db/web-application-overview",
                    "url": "/d/cIBgcSjkk/web-application-overview",
                    "type": "dash-db",
                    "tags": ["web", "application", "overview"],
                    "isStarred": True
                },
                {
                    "id": 2,
                    "uid": "ABCdefGhi",
                    "title": "Database Performance",
                    "uri": "db/database-performance",
                    "url": "/d/ABCdefGhi/database-performance",
                    "type": "dash-db",
                    "tags": ["database", "performance", "mysql"],
                    "isStarred": False
                },
                {
                    "id": 3,
                    "uid": "XYZ123abc",
                    "title": "Kubernetes Cluster Overview",
                    "uri": "db/kubernetes-cluster-overview",
                    "url": "/d/XYZ123abc/kubernetes-cluster-overview",
                    "type": "dash-db",
                    "tags": ["kubernetes", "cluster", "overview"],
                    "isStarred": True
                }
            ]
        }
    
    @tool("Get Grafana dashboard")
    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """Get a Grafana dashboard by its UID.
        
        Args:
            uid: UID of the dashboard to retrieve
            
        Returns:
            Dict containing the dashboard definition
        """
        # TODO: Implement actual Grafana API call
        # For now, return a simple mock response for development
        return {
            "dashboard": {
                "id": 1,
                "uid": uid,
                "title": "Web Application Overview",
                "panels": [
                    {
                        "id": 1,
                        "title": "Request Rate",
                        "type": "graph",
                        "description": "HTTP requests per second"
                    },
                    {
                        "id": 2,
                        "title": "Error Rate",
                        "type": "graph",
                        "description": "HTTP error rate (%)"
                    },
                    {
                        "id": 3,
                        "title": "Response Time",
                        "type": "graph",
                        "description": "HTTP response time (ms)"
                    }
                ],
                "schemaVersion": 26,
                "version": 1,
                "revision": 1
            },
            "meta": {
                "isStarred": True,
                "url": f"/d/{uid}/web-application-overview",
                "folderId": 0,
                "folderTitle": "General",
                "folderUrl": "",
                "provisioned": False,
                "provisionedExternalId": ""
            }
        }
    
    @tool("Get Grafana panel image")
    def get_panel_image(self, dashboard_uid: str, panel_id: int, 
                       time_from: str = "now-6h", time_to: str = "now",
                       width: int = 800, height: int = 400) -> Dict[str, Any]:
        """Get an image of a specific Grafana panel.
        
        Args:
            dashboard_uid: UID of the dashboard
            panel_id: ID of the panel within the dashboard
            time_from: Start time for the panel data (default: 6 hours ago)
            time_to: End time for the panel data (default: now)
            width: Width of the image in pixels (default: 800)
            height: Height of the image in pixels (default: 400)
            
        Returns:
            Dict containing the panel image URL or base64-encoded image data
        """
        # TODO: Implement actual Grafana API call
        # This would typically generate a render URL or retrieve a rendered image
        
        # For now, return a mock response for development
        return {
            "panel": {
                "dashboard_uid": dashboard_uid,
                "panel_id": panel_id,
                "title": "Error Rate",
                "description": "HTTP error rate (%)"
            },
            "image_url": f"{self.grafana_url}/render/d-solo/{dashboard_uid}?panelId={panel_id}&from={time_from}&to={time_to}&width={width}&height={height}&theme=light",
            # In a real implementation, this could be base64 encoded image data
            "image_data": "(Mock image data - in real implementation this would be base64 encoded)"
        }
    
    @tool("Get related dashboards for a service")
    def get_related_dashboards(self, service_name: str) -> List[Dict[str, Any]]:
        """Get dashboards related to a specific service.
        
        Args:
            service_name: Name of the service to find dashboards for
            
        Returns:
            List of dicts containing related dashboard information
        """
        # TODO: Implement actual Grafana API call to search for dashboards
        # with the service name or related tags
        
        # For now, return mock data for development
        return [
            {
                "uid": "cIBgcSjkk",
                "title": f"{service_name} Overview",
                "url": f"/d/cIBgcSjkk/{service_name.lower()}-overview",
                "tags": [service_name.lower(), "overview"],
                "description": f"Overview dashboard for {service_name}",
                "panels": ["Request Rate", "Error Rate", "Response Time"]
            },
            {
                "uid": "ABCdefGhi",
                "title": f"{service_name} Performance",
                "url": f"/d/ABCdefGhi/{service_name.lower()}-performance",
                "tags": [service_name.lower(), "performance"],
                "description": f"Performance metrics for {service_name}",
                "panels": ["CPU Usage", "Memory Usage", "Database Connections"]
            },
            {
                "uid": "XYZ123abc",
                "title": f"{service_name} Errors",
                "url": f"/d/XYZ123abc/{service_name.lower()}-errors",
                "tags": [service_name.lower(), "errors"],
                "description": f"Error tracking for {service_name}",
                "panels": ["Error Rate", "Error Types", "Stack Traces"]
            }
        ]
