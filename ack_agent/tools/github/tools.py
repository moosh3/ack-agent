import os
from typing import Dict, Any, List, Optional
from agno.tools import Tool, tool

class GitHubTools(Tool):
    """Tool for interacting with GitHub API to check code changes.
    
    This tool allows agents to retrieve information about GitHub repositories,
    recent commits, pull requests, and issues that might be related to incidents.
    """
    name = "github"
    description = "Tools for querying GitHub repositories and code changes"
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the GitHub tools with authentication token.
        
        Args:
            github_token: Optional GitHub authentication token.
                          If not provided, reads from GITHUB_TOKEN env var.
        """
        super().__init__()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
    
    @tool("Get recent commits")
    def get_recent_commits(self, owner: str, repo: str, branch: str = "main", max_count: int = 10) -> Dict[str, Any]:
        """Get recent commits for a GitHub repository.
        
        Args:
            owner: GitHub repository owner (username or organization)
            repo: GitHub repository name
            branch: Branch to get commits from (default: main)
            max_count: Maximum number of commits to retrieve (default: 10)
            
        Returns:
            Dict containing recent commits
        """
        # TODO: Implement actual GitHub API call using requests or PyGithub
        # For now, return mock data for development
        return {
            "commits": [
                {
                    "sha": "abc123def456ghi789",
                    "commit": {
                        "author": {
                            "name": "Jane Smith",
                            "email": "jane.smith@example.com",
                            "date": "2025-04-01T15:30:00Z"
                        },
                        "message": "Fix database connection pooling issue",
                        "url": f"https://github.com/{owner}/{repo}/commit/abc123def456ghi789"
                    },
                    "author": {
                        "login": "janesmith",
                        "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
                    },
                    "files": [
                        {
                            "filename": "src/database/connection_pool.py",
                            "status": "modified",
                            "additions": 15,
                            "deletions": 5
                        }
                    ]
                },
                {
                    "sha": "def456ghi789jkl012",
                    "commit": {
                        "author": {
                            "name": "John Doe",
                            "email": "john.doe@example.com",
                            "date": "2025-04-01T14:45:00Z"
                        },
                        "message": "Increase memory limits for web pods",
                        "url": f"https://github.com/{owner}/{repo}/commit/def456ghi789jkl012"
                    },
                    "author": {
                        "login": "johndoe",
                        "avatar_url": "https://avatars.githubusercontent.com/u/87654321"
                    },
                    "files": [
                        {
                            "filename": "kubernetes/web-deployment.yaml",
                            "status": "modified",
                            "additions": 2,
                            "deletions": 2
                        }
                    ]
                }
            ]
        }
    
    @tool("Get file content")
    def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """Get the content of a file from a GitHub repository.
        
        Args:
            owner: GitHub repository owner (username or organization)
            repo: GitHub repository name
            path: Path to the file within the repository
            ref: Optional reference (branch, tag, or commit SHA)
            
        Returns:
            Dict containing file content
        """
        # TODO: Implement actual GitHub API call
        # For now, return mock data for development
        return {
            "name": path.split("/")[-1],
            "path": path,
            "sha": "abc123def456ghi789",
            "size": 1024,
            "url": f"https://github.com/{owner}/{repo}/blob/main/{path}",
            "html_url": f"https://github.com/{owner}/{repo}/blob/main/{path}",
            "git_url": f"https://api.github.com/repos/{owner}/{repo}/git/blobs/abc123def456ghi789",
            "download_url": f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}",
            "type": "file",
            "content": "# Mock file content\n\nThis is a mock file content for development purposes.\n",
            "encoding": "utf-8"
        }
    
    @tool("Get repository information")
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get information about a GitHub repository.
        
        Args:
            owner: GitHub repository owner (username or organization)
            repo: GitHub repository name
            
        Returns:
            Dict containing repository information
        """
        # TODO: Implement actual GitHub API call
        # For now, return mock data for development
        return {
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "private": False,
            "html_url": f"https://github.com/{owner}/{repo}",
            "description": "Example repository for development",
            "fork": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2025-04-01T15:30:00Z",
            "pushed_at": "2025-04-01T15:30:00Z",
            "default_branch": "main",
            "owner": {
                "login": owner,
                "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
            }
        }
    
    @tool("Search code")
    def search_code(self, query: str, owner: Optional[str] = None, repo: Optional[str] = None, 
                   language: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
        """Search for code in GitHub repositories.
        
        Args:
            query: Search query string
            owner: Optional repository owner to limit search scope
            repo: Optional repository name to limit search scope (requires owner)
            language: Optional language to filter results
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            Dict containing search results
        """
        # TODO: Implement actual GitHub API call
        # Construct GitHub search query with appropriate filters
        search_query = query
        if owner and repo:
            search_query = f"{search_query} repo:{owner}/{repo}"
        elif owner:
            search_query = f"{search_query} user:{owner}"
        if language:
            search_query = f"{search_query} language:{language}"
        
        # For now, return mock data for development
        return {
            "total_count": 2,
            "incomplete_results": False,
            "items": [
                {
                    "name": "connection_pool.py",
                    "path": "src/database/connection_pool.py",
                    "repository": {
                        "name": repo or "example-repo",
                        "full_name": f"{owner or 'example-org'}/{repo or 'example-repo'}"
                    },
                    "html_url": f"https://github.com/{owner or 'example-org'}/{repo or 'example-repo'}/blob/main/src/database/connection_pool.py",
                    "score": 1.0
                },
                {
                    "name": "web-deployment.yaml",
                    "path": "kubernetes/web-deployment.yaml",
                    "repository": {
                        "name": repo or "example-repo",
                        "full_name": f"{owner or 'example-org'}/{repo or 'example-repo'}"
                    },
                    "html_url": f"https://github.com/{owner or 'example-org'}/{repo or 'example-repo'}/blob/main/kubernetes/web-deployment.yaml",
                    "score": 0.8
                }
            ]
        }
    
    @tool("Get recent pull requests")
    def get_recent_pull_requests(self, owner: str, repo: str, state: str = "all", max_count: int = 10) -> Dict[str, Any]:
        """Get recent pull requests for a GitHub repository.
        
        Args:
            owner: GitHub repository owner (username or organization)
            repo: GitHub repository name
            state: Pull request state (all, open, closed) (default: all)
            max_count: Maximum number of PRs to retrieve (default: 10)
            
        Returns:
            Dict containing recent pull requests
        """
        # TODO: Implement actual GitHub API call
        # For now, return mock data for development
        return {
            "pull_requests": [
                {
                    "number": 123,
                    "title": "Optimize database connection pooling",
                    "html_url": f"https://github.com/{owner}/{repo}/pull/123",
                    "state": "merged",
                    "created_at": "2025-04-01T14:30:00Z",
                    "merged_at": "2025-04-01T15:30:00Z",
                    "user": {
                        "login": "janesmith",
                        "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
                    },
                    "body": "This PR fixes database connection pooling to prevent connection exhaustion issues.",
                    "changed_files": 3,
                    "additions": 25,
                    "deletions": 10
                },
                {
                    "number": 122,
                    "title": "Update Kubernetes resource limits",
                    "html_url": f"https://github.com/{owner}/{repo}/pull/122",
                    "state": "merged",
                    "created_at": "2025-04-01T13:00:00Z",
                    "merged_at": "2025-04-01T14:45:00Z",
                    "user": {
                        "login": "johndoe",
                        "avatar_url": "https://avatars.githubusercontent.com/u/87654321"
                    },
                    "body": "This PR updates Kubernetes resource limits to improve stability.",
                    "changed_files": 1,
                    "additions": 2,
                    "deletions": 2
                }
            ]
        }
    
    @tool("Find potential incident-related changes")
    def find_incident_related_changes(self, owner: str, repo: str, service_name: str, 
                                    since: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find potential code changes that might be related to an incident.
        
        This tool analyzes recent commits, pull requests, and code changes to identify
        potential causes of an incident based on the service name and relevant keywords.
        
        Args:
            owner: GitHub repository owner (username or organization)
            repo: GitHub repository name
            service_name: Name of the service experiencing the incident
            since: ISO8601 timestamp to search from (e.g., '2025-04-01T00:00:00Z')
            keywords: Optional list of keywords related to the incident (e.g., 'database', 'memory')
            
        Returns:
            Dict containing potential incident-related changes
        """
        # TODO: Implement actual GitHub API calls to get commits, PRs, etc.
        # and analyze them to find potential incident causes
        
        # Default keywords if none provided
        if not keywords:
            keywords = ["error", "fix", "crash", "bug", "issue", "failure", "incident"]
        
        # In a real implementation, we would:
        # 1. Get recent commits since the given timestamp
        # 2. Get recent merged PRs since the given timestamp
        # 3. Filter by service name and keywords in commit messages, PR titles/descriptions, and changed files
        # 4. Score and rank potential causes based on recency, keyword matches, etc.
        
        # For now, return mock data for development
        return {
            "potential_causes": [
                {
                    "type": "pull_request",
                    "title": "Optimize database connection pooling",
                    "url": f"https://github.com/{owner}/{repo}/pull/123",
                    "merged_at": "2025-04-01T15:30:00Z",
                    "author": "janesmith",
                    "relevance_score": 0.9,
                    "match_reason": "Commits mention 'database connection' which matches incident keywords",
                    "key_changes": [
                        "src/database/connection_pool.py"
                    ]
                },
                {
                    "type": "commit",
                    "message": "Increase memory limits for web pods",
                    "url": f"https://github.com/{owner}/{repo}/commit/def456ghi789jkl012",
                    "date": "2025-04-01T14:45:00Z",
                    "author": "johndoe",
                    "relevance_score": 0.7,
                    "match_reason": "Changed Kubernetes resource limits which could affect system stability",
                    "key_changes": [
                        "kubernetes/web-deployment.yaml"
                    ]
                }
            ],
            "related_files": [
                {
                    "path": "src/database/connection_pool.py",
                    "url": f"https://github.com/{owner}/{repo}/blob/main/src/database/connection_pool.py",
                    "last_modified": "2025-04-01T15:30:00Z",
                    "relevance_score": 0.9
                },
                {
                    "path": "kubernetes/web-deployment.yaml",
                    "url": f"https://github.com/{owner}/{repo}/blob/main/kubernetes/web-deployment.yaml",
                    "last_modified": "2025-04-01T14:45:00Z",
                    "relevance_score": 0.7
                }
            ]
        }
