import os
from typing import Dict, Any, List, Optional
from agno.tools import Tool, tool

class SplunkTools(Tool):
    """Tool for interacting with Splunk API for log analysis.
    
    This tool allows agents to query Splunk for logs and events
    to investigate incidents and identify root causes.
    """
    name = "splunk"
    description = "Tools for querying Splunk logs and events"
    
    def __init__(self, splunk_url: Optional[str] = None, splunk_token: Optional[str] = None):
        """Initialize the Splunk tools with API URL and token.
        
        Args:
            splunk_url: Optional URL for the Splunk API.
                       If not provided, reads from SPLUNK_URL env var.
            splunk_token: Optional authentication token for Splunk.
                         If not provided, reads from SPLUNK_TOKEN env var.
        """
        super().__init__()
        self.splunk_url = splunk_url or os.getenv("SPLUNK_URL")
        self.splunk_token = splunk_token or os.getenv("SPLUNK_TOKEN")
        if not self.splunk_url or not self.splunk_token:
            raise ValueError("SPLUNK_URL and SPLUNK_TOKEN environment variables are required")
    
    @tool("Search Splunk logs")
    def search(self, query: str, earliest_time: Optional[str] = "-60m", latest_time: Optional[str] = "now", 
               max_count: int = 100) -> Dict[str, Any]:
        """Search Splunk logs with a given query.
        
        Args:
            query: Splunk search query (SPL)
            earliest_time: Start time for the search (default: 60 minutes ago)
            latest_time: End time for the search (default: now)
            max_count: Maximum number of results to return (default: 100)
            
        Returns:
            Dict containing search results
        """
        # TODO: Implement actual Splunk API call using requests or a Splunk SDK
        # For now, return mock data for development
        return {
            "preview": False,
            "results": [
                {
                    "_raw": "2025-04-01T16:15:02Z ERROR [web-server-01] AppServer - Connection pool exhausted: cannot acquire new database connection",
                    "_time": "2025-04-01T16:15:02.000+00:00",
                    "host": "web-server-01",
                    "source": "/var/log/application/app.log",
                    "sourcetype": "application-logs",
                    "index": "main"
                },
                {
                    "_raw": "2025-04-01T16:15:05Z ERROR [web-server-01] DbConnector - Database connection timeout after 30s",
                    "_time": "2025-04-01T16:15:05.000+00:00",
                    "host": "web-server-01",
                    "source": "/var/log/application/app.log",
                    "sourcetype": "application-logs",
                    "index": "main"
                },
                {
                    "_raw": "2025-04-01T16:15:10Z WARN [web-server-01] HealthChecker - Service health check failing: database connectivity issues",
                    "_time": "2025-04-01T16:15:10.000+00:00",
                    "host": "web-server-01",
                    "source": "/var/log/application/app.log",
                    "sourcetype": "application-logs",
                    "index": "main"
                }
            ],
            "highlighted": {},
            "init_offset": 0,
            "messages": [],
            "fields": ["_raw", "_time", "host", "source", "sourcetype", "index"],
            "stats": {}
        }
    
    @tool("Get error log frequency")
    def error_frequency(self, service_name: str, time_range: str = "60m", group_by: str = "sourcetype") -> Dict[str, Any]:
        """Get frequency of error logs for a specific service.
        
        Args:
            service_name: Name of the service to investigate
            time_range: Time range for the search (default: 60 minutes)
            group_by: Field to group results by (default: sourcetype)
            
        Returns:
            Dict containing error frequency statistics
        """
        # TODO: Implement actual Splunk API call
        # This would typically run a query like: 
        # search host=* sourcetype=* service={service_name} (error OR exception OR critical OR fail) 
        # | stats count by {group_by}
        
        # For now, return mock data for development
        return {
            "preview": False,
            "results": [
                {
                    "count": "42",
                    group_by: "application-logs"
                },
                {
                    "count": "17",
                    group_by: "database-logs"
                },
                {
                    "count": "5",
                    group_by: "nginx-access"
                }
            ],
            "fields": ["count", group_by]
        }
    
    @tool("Find exceptions in logs")
    def find_exceptions(self, service_name: str, time_range: str = "60m", max_count: int = 20) -> Dict[str, Any]:
        """Find and extract exceptions from logs for a specific service.
        
        Args:
            service_name: Name of the service to investigate
            time_range: Time range for the search (default: 60 minutes)
            max_count: Maximum number of results to return (default: 20)
            
        Returns:
            Dict containing exception details
        """
        # TODO: Implement actual Splunk API call
        # This would typically run a query that extracts exception stack traces
        
        # For now, return mock data for development
        return {
            "preview": False,
            "results": [
                {
                    "_time": "2025-04-01T16:15:05.000+00:00",
                    "host": "web-server-01",
                    "exception_type": "DatabaseConnectionException",
                    "exception_message": "Connection pool exhausted: cannot acquire new database connection",
                    "count": "15"
                },
                {
                    "_time": "2025-04-01T16:10:12.000+00:00",
                    "host": "web-server-01",
                    "exception_type": "TimeoutException",
                    "exception_message": "Database query timed out after 30 seconds",
                    "count": "8"
                }
            ],
            "fields": ["_time", "host", "exception_type", "exception_message", "count"]
        }
    
    @tool("Get recommended Splunk queries")
    def get_recommended_queries(self, service_name: str, issue_type: Optional[str] = None) -> List[Dict[str, str]]:
        """Get recommended Splunk queries for investigating a specific service.
        
        Args:
            service_name: Name of the service to investigate
            issue_type: Optional type of issue to focus on (e.g., 'error', 'performance', 'database')
            
        Returns:
            List of dicts containing query information
        """
        # This is a helper method that provides common queries for specific services
        # In a real implementation, this could be backed by a knowledge base
        
        base_queries = [
            {
                "name": "All Errors",
                "query": f"search index=* host=* sourcetype=* service={service_name} (ERROR OR CRITICAL OR FATAL OR EXCEPTION OR FAIL)",
                "description": "Find all error-level logs for the service"
            },
            {
                "name": "HTTP 5xx Errors",
                "query": f"search index=* sourcetype=access_combined OR sourcetype=nginx_access service={service_name} status>=500",
                "description": "Find all HTTP 500-level errors for the service"
            },
            {
                "name": "Recent Deployments",
                "query": f"search index=* sourcetype=deployment OR sourcetype=cicd service={service_name} | sort -_time",
                "description": "Find recent deployment events for the service"
            }
        ]
        
        # Add issue-specific queries if an issue type is specified
        if issue_type:
            if issue_type.lower() == "error":
                base_queries.extend([
                    {
                        "name": "Exception Stack Traces",
                        "query": f"search index=* host=* sourcetype=* service={service_name} Exception OR Error | rex field=_raw \"(?s)(?i)exception:(?P<exception>.+?)(?:\\n\\w|$)\"",
                        "description": "Extract exception stack traces"
                    },
                    {
                        "name": "Error Frequency By Component",
                        "query": f"search index=* host=* sourcetype=* service={service_name} (ERROR OR CRITICAL OR FATAL) | rex field=_raw \"\\[(?P<component>[^\\]]*)\\]\" | stats count by component",
                        "description": "Count errors by component or module"
                    }
                ])
            elif issue_type.lower() == "performance":
                base_queries.extend([
                    {
                        "name": "Slow Requests",
                        "query": f"search index=* sourcetype=access_combined OR sourcetype=nginx_access service={service_name} | eval response_time=tonumber(response_time) | where response_time > 1000",
                        "description": "Find HTTP requests taking more than 1 second"
                    },
                    {
                        "name": "Response Time Percentiles",
                        "query": f"search index=* sourcetype=access_combined OR sourcetype=nginx_access service={service_name} | eventstats perc25(response_time) as p25, perc50(response_time) as p50, perc75(response_time) as p75, perc90(response_time) as p90, perc99(response_time) as p99",
                        "description": "Calculate response time percentiles"
                    }
                ])
            elif issue_type.lower() == "database":
                base_queries.extend([
                    {
                        "name": "Database Connection Issues",
                        "query": f"search index=* host=* sourcetype=* service={service_name} (\"connection pool\" OR \"database connection\" OR \"sql exception\")",
                        "description": "Find database connection issues"
                    },
                    {
                        "name": "Slow Queries",
                        "query": f"search index=* sourcetype=db_logs OR sourcetype=mysql OR sourcetype=postgresql service={service_name} slow",
                        "description": "Find slow database queries"
                    }
                ])
            elif issue_type.lower() == "memory":
                base_queries.extend([
                    {
                        "name": "Memory Issues",
                        "query": f"search index=* host=* sourcetype=* service={service_name} (\"OutOfMemoryError\" OR \"memory leak\" OR \"memory exhausted\" OR \"cannot allocate memory\")",
                        "description": "Find memory-related issues"
                    },
                    {
                        "name": "GC Activity",
                        "query": f"search index=* sourcetype=gc_logs service={service_name}",
                        "description": "Find garbage collection activity logs"
                    }
                ])
        
        return base_queries
