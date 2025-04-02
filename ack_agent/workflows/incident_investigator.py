from typing import Dict, Any, List, Optional, Union, AsyncGenerator, BinaryIO, cast
import json
import datetime
import os
import base64
from uuid import uuid4
from pathlib import Path

from agno.workflow import Workflow
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from agno.run.response import RunResponse, RunEvent
from agno.memory.workflow import WorkflowMemory, WorkflowRun
from agno.artifacts import ArtifactStore, Artifact  

from ack_agent.schemas.kubernetes import (
    KubernetesInvestigatorResponse, PodStatusParameters, EventsParameters,
    ResourceUsageParameters, DeploymentStatusParameters
)
from ack_agent.schemas.logs import (
    LogsInvestigatorResponse, LogSearchParameters, PatternExtractionParameters, LogVolumeParameters
)
from ack_agent.schemas.metrics import (
    MetricsInvestigatorResponse, MetricQueryParameters, RecommendedQueriesParameters, 
    AnomalyDetectionParameters, BottleneckParameters
)
from ack_agent.schemas.code import (
    CodeInvestigatorResponse, CommitParameters, DeploymentParameters, RiskyChangeParameters
)

from ack_agent.agents.investigators.kubernetes.agent import create_kubernetes_investigator
from ack_agent.agents.investigators.splunk.agent import create_splunk_investigator
from ack_agent.agents.investigators.github.agent import create_github_investigator
from ack_agent.agents.investigators.metrics.agent import create_metrics_investigator


class IncidentInvestigationWorkflow(Workflow):
    """Workflow for investigating incidents using specialized agents.
    
    This workflow orchestrates the investigation of incidents by leveraging
    specialized agents for different domains: Kubernetes infrastructure,
    logs analysis, code changes, and metrics. It follows a structured approach
    to ensure thorough investigation while efficiently prioritizing the most
    relevant domains based on incident details.
    """
    
    def __init__(self, incident_data: Dict[str, Any], db_path: str = None, run_id: str = None, session_id: str = None):
        """Initialize the incident investigation workflow.
        
        Args:
            incident_data: Dictionary containing incident details, including at minimum:
                - service_name: The affected service
                - incident_type: The type of incident (e.g., 'outage', 'performance', 'error')
                - severity: Severity level (e.g., 'critical', 'warning')
                - description: Text description of the incident
                - timestamp: When the incident occurred
            db_path: Path to SQLite database file. If None, uses a default path.
            run_id: Optional ID for this investigation run. If None, a new UUID will be generated.
            session_id: Optional ID for the investigation session. If None, a new UUID will be generated.
        """
        super().__init__(
            name="Incident Investigation",
            description="Systematic investigation of incidents across multiple domains"
        )
        
        self.incident_data = incident_data
        self.investigation_results = {}
        
        # Initialize run tracking
        self.run_id = run_id or str(uuid4())
        self.session_id = session_id or str(uuid4())
        self.run_response = RunResponse(
            run_id=self.run_id,
            session_id=self.session_id,
            workflow_id=self.workflow_id
        )
        
        # Create a unique incident ID if none provided
        self.incident_id = incident_data.get('incident_id', self._generate_incident_id())
        
        # Initialize workflow memory
        self.memory = WorkflowMemory()
        # Metadata for incident context that we'll store in memory
        self.memory_metadata = {
            'service': incident_data.get('service_name', 'unknown'),
            'incident_type': incident_data.get('incident_type', 'unknown'),
            'severity': incident_data.get('severity', 'unknown'),
            'incident_id': self.incident_id
        }
        
        # Initialize artifact store for evidence storage
        artifact_dir = os.path.join(os.path.dirname(db_path) if db_path else os.getcwd(), 'artifacts')
        os.makedirs(artifact_dir, exist_ok=True)
        self.artifact_store = ArtifactStore(artifact_dir)
        
        # Initialize SQLite storage
        if db_path is None:
            # Use a default path in the project directory
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'incidents.db')
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        self.storage = SqliteStorage(db_path)
        self._init_db_schema()
        
        # Store the incident details in the database
        self._store_incident()
        
        # Initialize investigation agents
        self.kubernetes_investigator = create_kubernetes_investigator()
        self.splunk_investigator = create_splunk_investigator()
        self.github_investigator = create_github_investigator()
        self.metrics_investigator = create_metrics_investigator()
        
        # Set up the workflow configuration
        self._setup_workflow()
    
    def _generate_incident_id(self) -> str:
        """Generate a unique incident ID based on timestamp and service.
        
        Returns:
            A unique string identifier for the incident
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        service = self.incident_data.get('service_name', 'unknown').replace('-', '_')
        return f"incident_{service}_{timestamp}"
    
    def _init_db_schema(self):
        """Initialize the database schema for storing incident data and findings."""
        # Create incidents table
        self.storage.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                service_name TEXT,
                incident_type TEXT,
                severity TEXT,
                description TEXT,
                timestamp TEXT,
                created_at TEXT
            )
        """)
        
        # Create findings table for storing potential causes from agents
        self.storage.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                incident_id TEXT,
                source TEXT,  -- which agent/domain (kubernetes, logs, code, metrics)
                description TEXT,
                evidence TEXT, -- JSON serialized evidence data
                confidence REAL,
                timestamp TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            )
        """)
    
    def _store_incident(self):
        """Store the incident details in the database."""
        try:
            # Check if incident already exists
            result = self.storage.execute(
                "SELECT 1 FROM incidents WHERE incident_id = ?",
                (self.incident_id,)
            )
            
            if not result.fetchone():
                # Insert the incident data
                self.storage.execute(
                    """
                    INSERT INTO incidents (
                        incident_id, service_name, incident_type, severity, 
                        description, timestamp, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.incident_id,
                        self.incident_data.get('service_name', 'unknown'),
                        self.incident_data.get('incident_type', 'unknown'),
                        self.incident_data.get('severity', 'unknown'),
                        self.incident_data.get('description', ''),
                        self.incident_data.get('timestamp', datetime.datetime.now().isoformat()),
                        datetime.datetime.now().isoformat()
                    )
                )
        except Exception as e:
            print(f"Error storing incident in database: {e}")
    
    def _store_finding(self, source: str, description: str, evidence: Any, confidence: float):
        """Store a potential cause finding in the database.
        
        Args:
            source: Source of the finding (e.g., 'kubernetes', 'logs', 'code', 'metrics')
            description: Description of the finding
            evidence: Evidence supporting the finding (will be JSON serialized)
            confidence: Confidence score (0.0 to 1.0)
        
        Returns:
            The generated finding ID
        """
        try:
            # Generate a unique finding ID
            finding_id = f"{self.incident_id}_{source}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Serialize evidence to JSON if necessary
            if not isinstance(evidence, str):
                evidence = json.dumps(evidence)
                
            # Insert the finding
            self.storage.execute(
                """
                INSERT INTO findings (
                    finding_id, incident_id, source, description, 
                    evidence, confidence, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    finding_id,
                    self.incident_id,
                    source,
                    description,
                    evidence,
                    confidence,
                    datetime.datetime.now().isoformat()
                )
            )
            
            return finding_id
        except Exception as e:
            print(f"Error storing finding in database: {e}")
            return None
    
    def _setup_workflow(self):
        """Set up the workflow configuration.
        
        In Agno, workflows are defined by implementing methods that handle
        different stages of the investigation process. This method sets up
        any initial configuration needed before the workflow runs.
        """
        # Initialize the session state to track investigation progress
        self.session_state = {
            'assessed': False,
            'investigations': {
                'kubernetes': False,
                'logs': False,
                'code_changes': False,
                'metrics': False
            },
            'findings': [],
            'artifacts': [],
            'synthesized': False
        }
        
        # Register the investigation methods that can be called during workflow execution
        self._investigation_methods = {
            'kubernetes': self.investigate_kubernetes,
            'logs': self.investigate_logs,
            'code_changes': self.investigate_code_changes,
            'metrics': self.investigate_metrics
        }
        
        # Map investigation types to their respective agents
        self._investigation_agents = {
            'kubernetes': self.kubernetes_investigator,
            'logs': self.splunk_investigator,
            'code_changes': self.github_investigator,
            'metrics': self.metrics_investigator
        }
    
    async def assess_incident(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """Assess incident details to determine which domains to investigate.
        
        Args:
            context: The workflow context including incident data
            
        Returns:
            Dictionary with keys for each investigation domain and boolean values
            indicating whether that domain should be investigated
        """
        incident = self.incident_data
        service_name = incident.get('service_name', '')
        incident_type = incident.get('incident_type', '')
        description = incident.get('description', '')
        
        # Default to investigating all domains
        investigate = {
            'investigate_kubernetes': True,
            'investigate_logs': True,
            'investigate_code_changes': True,
            'investigate_metrics': True
        }
        
        # Logic to determine which domains to prioritize based on incident details
        # In a real system, this would be more sophisticated
        if 'deployment' in description.lower() or 'pod' in description.lower():
            # Prioritize Kubernetes and code changes for deployment issues
            investigate['investigate_metrics'] = False
        
        if 'performance' in incident_type.lower() or 'slow' in description.lower():
            # Prioritize metrics for performance issues
            investigate['investigate_code_changes'] = False
        
        if 'error' in description.lower() or 'exception' in description.lower():
            # Prioritize logs and code changes for error issues
            pass  # Investigate all domains
        
        return investigate
    
    async def investigate_kubernetes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate Kubernetes infrastructure for issues.
        
        Args:
            context: The workflow context including incident data and previous results
            
        Returns:
            Dictionary with Kubernetes investigation findings
        """
        service_name = self.incident_data.get('service_name', '')
        
        # Use the Kubernetes investigator to check cluster health
        # In a real implementation, this would make actual API calls to Kubernetes
        findings = {}
        
        # Check pod status
        pod_status_params = PodStatusParameters(
            service_name=service_name
        )
        pod_status_task = {
            "task": "check_pod_status",
            "parameters": pod_status_params.model_dump()
        }
        pod_status_response = await self.kubernetes_investigator.run(pod_status_task)
        
        # Use the helper method to get typed pod status results
        findings['pod_status'] = pod_status_response.get_pod_status()
        
        # Get recent events
        events_params = EventsParameters(
            service_name=service_name
        )
        events_task = {
            "task": "get_recent_events",
            "parameters": events_params.model_dump()
        }
        events_response = await self.kubernetes_investigator.run(events_task)
        
        # Use the helper method to get typed events
        findings['recent_events'] = events_response.get_events()
        
        # Check resource usage
        resource_params = ResourceUsageParameters(
            service_name=service_name
        )
        resource_task = {
            "task": "check_resource_usage",
            "parameters": resource_params.model_dump()
        }
        resource_response = await self.kubernetes_investigator.run(resource_task)
        
        # Use the helper method to get typed resource usage data
        findings['resource_usage'] = resource_response.get_resource_usage()
        
        # Check deployment status
        deployment_params = DeploymentStatusParameters(
            service_name=service_name
        )
        deployment_task = {
            "task": "check_deployment_status",
            "parameters": deployment_params.model_dump()
        }
        deployment_response = await self.kubernetes_investigator.run(deployment_task)
        
        # Use the helper method to get typed deployment information
        findings['deployment_status'] = deployment_response.get_deployment_info()
        
        # Store the complete Kubernetes investigation as an artifact
        self.store_artifact(
            content=findings,
            artifact_type='kubernetes',
            description=f"Complete Kubernetes investigation for {service_name}",
            file_extension='json'
        )
        
        # Store findings in the database
        pod_status = findings.get('pod_status', {})
        unhealthy_pods = pod_status.get('unhealthy_pods', [])
        if unhealthy_pods:
            self._store_finding(
                source='kubernetes',
                description='Unhealthy pods detected that may be related to the incident',
                evidence=unhealthy_pods,
                confidence=0.8
            )
            
            # Store unhealthy pods as a separate artifact for easier access
            self.store_artifact(
                content={'unhealthy_pods': unhealthy_pods},
                artifact_type='kubernetes_pods',
                description=f"Unhealthy pods for {service_name}",
                file_extension='json'
            )
        
        resource_usage = findings.get('resource_usage', {})
        if resource_usage.get('cpu_pressure', False) or resource_usage.get('memory_pressure', False):
            self._store_finding(
                source='kubernetes',
                description='Resource pressure detected on nodes running the service',
                evidence=resource_usage,
                confidence=0.75
            )
            
            # Store resource usage as an artifact
            self.store_artifact(
                content=resource_usage,
                artifact_type='kubernetes_resources',
                description=f"Resource pressure metrics for {service_name}",
                file_extension='json'
            )
            
        recent_events = findings.get('recent_events', [])
        error_events = [e for e in recent_events if e.get('type') == 'Warning' or e.get('type') == 'Error']
        if error_events:
            self._store_finding(
                source='kubernetes',
                description='Kubernetes events with warnings or errors detected',
                evidence=error_events,
                confidence=0.7
            )
            
            # Store error events as an artifact
            self.store_artifact(
                content={'error_events': error_events},
                artifact_type='kubernetes_events',
                description=f"Kubernetes warning and error events for {service_name}",
                file_extension='json'
            )
        
        self.investigation_results['kubernetes'] = findings
        return findings
    
    async def investigate_logs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze logs for error patterns and anomalies.
        
        Args:
            context: The workflow context including incident data and previous results
            
        Returns:
            Dictionary with log analysis findings
        """
        service_name = self.incident_data.get('service_name', '')
        incident_time = self.incident_data.get('timestamp', '')
        
        # Search for errors in logs around the incident time
        # In a real implementation, this would make actual API calls to Splunk
        findings = {}
        
        # Search for error logs using Pydantic models for parameters
        error_logs_params = LogSearchParameters(
            query=f'service={service_name} error',
            time_range=f'-30m,+30m',
            reference_time=incident_time
        )
        
        error_logs_task = {
            "task": "search_logs",
            "parameters": error_logs_params.model_dump()
        }
        
        findings['error_logs'] = await self.splunk_investigator.run(error_logs_task)
        
        # Extract exception patterns
        patterns_params = PatternExtractionParameters(
            query=f'service={service_name} exception',
            time_range=f'-30m,+30m',
            reference_time=incident_time
        )
        
        patterns_task = {
            "task": "extract_patterns",
            "parameters": patterns_params.model_dump()
        }
        
        findings['exception_patterns'] = await self.splunk_investigator.run(patterns_task)
        
        # Analyze log volume
        volume_params = LogVolumeParameters(
            query=f'service={service_name}',
            time_range=f'-3h,+1h',
            reference_time=incident_time
        )
        
        volume_task = {
            "task": "analyze_log_volume",
            "parameters": volume_params.model_dump()
        }
        
        findings['log_volume_analysis'] = await self.splunk_investigator.run(volume_task)
        
        # Store the complete logs investigation as an artifact
        self.store_artifact(
            content=findings,
            artifact_type='logs',
            description=f"Complete log analysis for {service_name} around {incident_time}",
            file_extension='json'
        )
        
        # Store findings in the database
        error_logs = findings.get('error_logs', [])
        if error_logs:
            self._store_finding(
                source='logs',
                description='Error logs detected during the incident timeframe',
                evidence=error_logs[:5],  # Store first 5 errors as evidence
                confidence=0.75
            )
            
            # Store full error logs as an artifact for reference
            self.store_artifact(
                content={'error_logs': error_logs},
                artifact_type='logs_errors',
                description=f"Error logs for {service_name} around incident time",
                file_extension='json'
            )
            
        exception_patterns = findings.get('exception_patterns', [])
        if exception_patterns:
            self._store_finding(
                source='logs',
                description='Recurring exception patterns identified in logs',
                evidence=exception_patterns,
                confidence=0.85
            )
            
            # Store exception patterns as an artifact
            self.store_artifact(
                content={'exception_patterns': exception_patterns},
                artifact_type='logs_exceptions',
                description=f"Exception patterns in {service_name} logs",
                file_extension='json'
            )
            
        log_volume = findings.get('log_volume_analysis', {})
        if log_volume.get('anomalies', False):
            self._store_finding(
                source='logs',
                description='Anomalous log volume detected around incident time',
                evidence=log_volume,
                confidence=0.7
            )
            
            # Store log volume analysis as an artifact
            self.store_artifact(
                content=log_volume,
                artifact_type='logs_volume',
                description=f"Log volume analysis for {service_name}",
                file_extension='json'
            )
        
        self.investigation_results['logs'] = findings
        return findings
    
    async def investigate_code_changes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze recent code changes that might relate to the incident.
        
        Args:
            context: The workflow context including incident data and previous results
            
        Returns:
            Dictionary with code change analysis findings
        """
        service_name = self.incident_data.get('service_name', '')
        incident_time = self.incident_data.get('timestamp', '')
        
        # In a real implementation, this would make actual API calls to GitHub
        findings = {}
        
        # Get recent commits using Pydantic models for parameters
        
        commits_params = CommitParameters(
            repo=service_name,
            since="24h",
            reference_time=incident_time
        )
        
        commits_task = {
            "task": "get_recent_commits",
            "parameters": commits_params.model_dump()
        }
        
        raw_commits_response = await self.github_investigator.run(commits_task)
        
        # Convert the raw JSON response to our unified Code response model
        commits_response = CodeInvestigatorResponse.model_validate(raw_commits_response)
        
        # Use the helper method to get typed commits
        findings['recent_commits'] = commits_response.get_commits()
        
        # Get recent deployments
        
        deployments_params = DeploymentParameters(
            service=service_name,
            since="24h",
            reference_time=incident_time
        )
        
        deployments_task = {
            "task": "get_recent_deployments",
            "parameters": deployments_params.model_dump()
        }
        
        raw_deployments_response = await self.github_investigator.run(deployments_task)
        
        # Convert to our unified Code response model
        deployments_response = CodeInvestigatorResponse.model_validate(raw_deployments_response)
        
        # Use the helper method to get typed deployments
        findings['recent_deployments'] = deployments_response.get_deployments()
        
        # Identify risky changes
        
        risky_params = RiskyChangeParameters(
            repo=service_name,
            since="24h",
            reference_time=incident_time
        )
        
        risky_task = {
            "task": "identify_risky_changes",
            "parameters": risky_params.model_dump()
        }
        
        raw_risky_response = await self.github_investigator.run(risky_task)
        
        # Convert to our unified Code response model
        risky_response = CodeInvestigatorResponse.model_validate(raw_risky_response)
        
        # Use the helper method to get typed risky changes
        findings['risky_changes'] = risky_response.get_risky_changes()
        
        # Store findings in the database
        recent_deployments = findings.get('recent_deployments', [])
        if recent_deployments:
            # Find deployments that occurred close to the incident time
            for deployment in recent_deployments:
                deploy_time = deployment.get('deployed_at', '')
                if deploy_time and self._is_within_timeframe(deploy_time, incident_time, hours_before=6):
                    self._store_finding(
                        source='code',
                        description='Recent deployment shortly before the incident',
                        evidence=deployment,
                        confidence=0.85
                    )
                    break
        
        risky_changes = findings.get('risky_changes', [])
        if risky_changes:
            self._store_finding(
                source='code',
                description='Potentially risky code changes identified',
                evidence=risky_changes,
                confidence=0.7
            )
            
        recent_commits = findings.get('recent_commits', [])
        suspicious_commits = [c for c in recent_commits 
                            if any(kw in c.get('message', '').lower() 
                                  for kw in ['fix', 'bug', 'error', 'issue', 'crash', 'performance'])]
        if suspicious_commits:
            self._store_finding(
                source='code',
                description='Recent commits with concerning keywords',
                evidence=suspicious_commits,
                confidence=0.6
            )
        
        self.investigation_results['code_changes'] = findings
        return findings
    
    def _is_within_timeframe(self, time_str: str, reference_time: str, hours_before: int) -> bool:
        """Check if a timestamp is within specified hours before a reference time.
        
        Args:
            time_str: The timestamp to check
            reference_time: The reference timestamp
            hours_before: Number of hours before reference time to check
            
        Returns:
            True if time_str is within the specified hours before reference_time
        """
        try:
            # Parse the timestamps
            time = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            ref_time = datetime.datetime.fromisoformat(reference_time.replace('Z', '+00:00'))
            
            # Check if time is within the specified hours before ref_time
            time_diff = ref_time - time
            return time <= ref_time and time_diff.total_seconds() <= hours_before * 3600
        except Exception as e:
            print(f"Error comparing timestamps: {e}")
            return False
    
    async def investigate_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system metrics for anomalies and patterns.
        
        Args:
            context: The workflow context including incident data and previous results
            
        Returns:
            Dictionary with metrics analysis findings
        """
        service_name = self.incident_data.get('service_name', '')
        incident_time = self.incident_data.get('timestamp', '')
        
        # Create task for metrics investigator to get recommended queries using Pydantic models
        
        query_params = RecommendedQueriesParameters(
            service_name=service_name
        )
        
        query_task = {
            "task": "get_recommended_queries",
            "parameters": query_params.model_dump()
        }
        
        # Run the metrics investigator agent to get query recommendations
        raw_recommended_queries_response = await self.metrics_investigator.run(query_task)
        
        # Since this isn't a standard response type but returns a list of query objects,
        # we'll handle it differently - as a QueryResponse containing a dictionary of QueryResults
        recommended_queries_response = MetricsInvestigatorResponse.model_validate(raw_recommended_queries_response)
        # Get query results using the helper method
        recommended_queries = recommended_queries_response.get_query_results().values() if recommended_queries_response.is_success() else []
        
        metrics_results = {}
        
        # Execute each recommended query and collect results
        
        for query_info in recommended_queries:
            query_name = query_info.query_name if hasattr(query_info, 'query_name') else None
            query = query_info.query if hasattr(query_info, 'query') else None
            
            if query and query_name:
                # Create task to run this specific query
                run_query_params = MetricQueryParameters(
                    query=query,
                    start=f'{incident_time}-30m',
                    end=f'{incident_time}+30m',
                    step="1m"
                )
                
                run_query_task = {
                    "task": "run_query",
                    "parameters": run_query_params.model_dump()
                }
                
                # Run the metrics investigator agent with this task
                raw_query_result = await self.metrics_investigator.run(run_query_task)
                
                # Convert to our unified Metrics response model
                query_result = MetricsInvestigatorResponse.model_validate(raw_query_result)
                
                # Get query results using the helper method
                metrics_results[query_name] = query_result.get_query_results().get(query_name, {}) if query_result.is_success() else {}
        
        # Create task to detect anomalies in metrics
        
        anomaly_params = AnomalyDetectionParameters(
            service_name=service_name,
            start=f'{incident_time}-3h',
            end=f'{incident_time}+1h'
        )
        
        anomaly_task = {
            "task": "detect_anomalies",
            "parameters": anomaly_params.model_dump()
        }
        
        # Run the metrics investigator to detect anomalies
        raw_anomaly_response = await self.metrics_investigator.run(anomaly_task)
        
        # Convert to our unified Metrics response model
        anomaly_response = MetricsInvestigatorResponse.model_validate(raw_anomaly_response)
        
        # Get anomalies using the helper method
        anomalies = anomaly_response.get_anomalies() if anomaly_response.is_success() else []
        
        # Create task to identify resource bottlenecks
        
        bottleneck_params = BottleneckParameters(
            service_name=service_name,
            time_range=f'{incident_time}-1h,{incident_time}+30m'
        )
        
        bottleneck_task = {
            "task": "identify_bottlenecks",
            "parameters": bottleneck_params.model_dump()
        }
        
        # Run the metrics investigator to identify bottlenecks
        raw_bottleneck_response = await self.metrics_investigator.run(bottleneck_task)
        
        # Convert to our unified Metrics response model
        bottleneck_response = MetricsInvestigatorResponse.model_validate(raw_bottleneck_response)
        
        # Get bottlenecks using the helper method
        resource_bottlenecks = bottleneck_response.get_bottlenecks() if bottleneck_response.is_success() else {}
        
        findings = {
            'metrics_data': metrics_results,
            'anomalies': anomalies,
            'resource_bottlenecks': resource_bottlenecks
        }
        
        # Store findings in the database
        if anomalies:
            # Store each type of anomaly as a separate finding
            for anomaly_type, anomaly_data in anomalies.items():
                if anomaly_data.get('detected', False):
                    self._store_finding(
                        source='metrics',
                        description=f'Metric anomaly detected: {anomaly_type}',
                        evidence=anomaly_data,
                        confidence=0.8
                    )
        
        if resource_bottlenecks:
            # Check for CPU bottlenecks
            if resource_bottlenecks.get('cpu_bottleneck', False):
                self._store_finding(
                    source='metrics',
                    description='CPU bottleneck detected',
                    evidence=resource_bottlenecks.get('cpu_details', {}),
                    confidence=0.85
                )
                
            # Check for memory bottlenecks
            if resource_bottlenecks.get('memory_bottleneck', False):
                self._store_finding(
                    source='metrics',
                    description='Memory bottleneck detected',
                    evidence=resource_bottlenecks.get('memory_details', {}),
                    confidence=0.85
                )
                
            # Check for disk bottlenecks
            if resource_bottlenecks.get('disk_bottleneck', False):
                self._store_finding(
                    source='metrics',
                    description='Disk I/O bottleneck detected',
                    evidence=resource_bottlenecks.get('disk_details', {}),
                    confidence=0.8
                )
                
            # Check for network bottlenecks
            if resource_bottlenecks.get('network_bottleneck', False):
                self._store_finding(
                    source='metrics',
                    description='Network bottleneck detected',
                    evidence=resource_bottlenecks.get('network_details', {}),
                    confidence=0.75
                )
        
        # Check for specific metrics that exceed thresholds
        for query_name, result in metrics_results.items():
            if result.get('exceeds_threshold', False):
                self._store_finding(
                    source='metrics',
                    description=f'Metric threshold exceeded: {query_name}',
                    evidence=result,
                    confidence=0.7
                )
        
        self.investigation_results['metrics'] = findings
        return findings
    
    async def synthesize_findings(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Combine and analyze findings from all investigations.
        
        Args:
            context: The workflow context including all investigation results
            
        Returns:
            Dictionary with synthesized findings and recommendations
        """
        # Get results from each investigation domain
        k8s_results = context.get('kubernetes_investigation', {})
        logs_results = context.get('logs_investigation', {})
        code_results = context.get('code_investigation', {})
        metrics_results = context.get('metrics_investigation', {})
        
        # Combine all findings into a comprehensive analysis
        # In a real implementation, this would use more sophisticated correlation logic
        
        # Example correlation: Check if there's a deployment that corresponds with error spikes
        correlated_findings = []
        
        # Look for deployments that happened close to the incident time
        recent_deployments = code_results.get('recent_deployments', [])
        error_logs = logs_results.get('error_logs', [])
        
        if recent_deployments and error_logs:
            # Simple correlation - did errors appear after a deployment?
            # In a real system, this would involve timestamp comparison
            correlation = "Potential correlation between recent deployment and error logs"
            correlated_findings.append(correlation)
            
            # Store this correlation in the database
            self._store_finding(
                source='correlation',
                description=correlation,
                evidence={
                    'deployments': recent_deployments,
                    'error_logs': error_logs[:5]  # First 5 errors for brevity
                },
                confidence=0.75
            )
        
        # Check if resource bottlenecks match with performance anomalies
        bottlenecks = metrics_results.get('resource_bottlenecks', {})
        anomalies = metrics_results.get('anomalies', [])
        
        if bottlenecks and anomalies:
            correlation = "Resource bottlenecks detected that correspond with performance anomalies"
            correlated_findings.append(correlation)
            
            # Store this correlation in the database
            self._store_finding(
                source='correlation',
                description=correlation,
                evidence={
                    'bottlenecks': bottlenecks,
                    'anomalies': anomalies
                },
                confidence=0.85
            )
        
        # Check if we have historical insights in the results
        historical_insights = None
        if 'historical_insights' in results:
            historical_insights = results['historical_insights']
        
        # Summarize findings across all domains
        # Get root causes with historical context considered
        potential_root_causes = self._determine_root_causes(
            k8s_results, logs_results, code_results, metrics_results, historical_insights
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            k8s_results, logs_results, code_results, metrics_results
        )
        
        # Compile the complete summary
        summary = {
            'incident_overview': self.incident_data,
            'correlated_findings': correlated_findings,
            'kubernetes_findings': k8s_results,
            'logs_findings': logs_results,
            'code_change_findings': code_results,
            'metrics_findings': metrics_results,
            'historical_insights': historical_insights,
            'potential_root_causes': potential_root_causes,
            'recommendations': recommendations
        }
        
        # Generate a markdown report artifact for human consumption
        markdown_report = self._generate_markdown_report(
            summary, 
            potential_root_causes, 
            recommendations, 
            historical_insights
        )
        
        # Store the comprehensive investigation report as an artifact
        # First as a structured JSON
        self.store_artifact(
            content=summary,
            artifact_type='investigation_summary',
            description=f"Complete investigation summary for incident {self.incident_id}",
            file_extension='json'
        )
        
        # Then as a human-readable markdown report
        self.store_artifact(
            content=markdown_report,
            artifact_type='investigation_report',
            description=f"Human-readable investigation report for incident {self.incident_id}",
            file_extension='md'
        )
        
        return summary
    
    def _determine_root_causes(self, k8s_results, logs_results, code_results, metrics_results, past_insights: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Analyze all findings to determine potential root causes.
        
        This method analyzes findings from multiple investigation domains to identify
        potential root causes. It can also incorporate historical patterns from
        previous similar incidents to improve diagnosis.
        
        Args:
            k8s_results: Results from Kubernetes investigation
            logs_results: Results from logs investigation
            code_results: Results from code changes investigation
            metrics_results: Results from metrics investigation
            past_insights: Optional historical insights from past incidents
            
        Returns:
            List of potential root causes with confidence scores
        """
        # In a real implementation, this would use more sophisticated analysis
        potential_causes = []
        
        # Check if we have historical insights to consider
        historical_causes = {}
        if past_insights and past_insights.get('past_incidents_count', 0) > 0:
            # Extract historical causes and their frequencies
            for cause in past_insights.get('common_root_causes', []):
                if cause.get('cause') and cause.get('count', 0) > 0:
                    historical_causes[cause['cause'].lower()] = cause['count']
        
        # Check for Kubernetes issues
        pod_status = k8s_results.get('pod_status', {})
        if pod_status.get('unhealthy_pods', []):
            base_confidence = 0.8
            # Adjust confidence if this has been a recurring cause
            if 'unhealthy pods detected' in historical_causes:
                # Increase confidence based on how often this has been seen historically
                frequency_boost = min(0.15, 0.05 * historical_causes['unhealthy pods detected'])
                adjusted_confidence = min(0.95, base_confidence + frequency_boost)
                historical_evidence = f"This has been a root cause in {historical_causes['unhealthy pods detected']} previous incidents"
            else:
                adjusted_confidence = base_confidence
                historical_evidence = None
                
            cause = {
                'description': 'Unhealthy pods detected',
                'confidence': adjusted_confidence,
                'evidence': pod_status.get('unhealthy_pods'),
                'domain': 'kubernetes',
                'historical_context': historical_evidence
            }
            potential_causes.append(cause)
            
            # Store the root cause in the database with a high confidence
            self._store_finding(
                source='root_cause',
                description=cause['description'],
                evidence=cause['evidence'],
                confidence=cause['confidence']
            )
        
        # Check for code-related issues
        risky_changes = code_results.get('risky_changes', [])
        if risky_changes:
            base_confidence = 0.7
            # Adjust confidence if this has been a recurring cause
            if 'recent risky code changes detected' in historical_causes:
                # Increase confidence based on how often this has been seen historically
                frequency_boost = min(0.15, 0.05 * historical_causes['recent risky code changes detected'])
                adjusted_confidence = min(0.95, base_confidence + frequency_boost)
                historical_evidence = f"This has been a root cause in {historical_causes['recent risky code changes detected']} previous incidents"
            else:
                adjusted_confidence = base_confidence
                historical_evidence = None
                
            cause = {
                'description': 'Recent risky code changes detected',
                'confidence': adjusted_confidence,
                'evidence': risky_changes,
                'domain': 'code_changes',
                'historical_context': historical_evidence
            }
            potential_causes.append(cause)
            
            # Store the root cause in the database
            self._store_finding(
                source='root_cause',
                description=cause['description'],
                evidence=cause['evidence'],
                confidence=cause['confidence']
            )
        
        # Check for resource bottlenecks
        bottlenecks = metrics_results.get('resource_bottlenecks', {})
        if bottlenecks:
            base_confidence = 0.75
            # Adjust confidence if this has been a recurring cause
            if 'resource bottlenecks detected' in historical_causes:
                # Increase confidence based on how often this has been seen historically
                frequency_boost = min(0.15, 0.05 * historical_causes['resource bottlenecks detected'])
                adjusted_confidence = min(0.95, base_confidence + frequency_boost)
                historical_evidence = f"This has been a root cause in {historical_causes['resource bottlenecks detected']} previous incidents"
            else:
                adjusted_confidence = base_confidence
                historical_evidence = None
                
            cause = {
                'description': 'Resource bottlenecks detected',
                'confidence': adjusted_confidence,
                'evidence': bottlenecks,
                'domain': 'metrics',
                'historical_context': historical_evidence
            }
            potential_causes.append(cause)
            
            # Store the root cause in the database
            self._store_finding(
                source='root_cause',
                description=cause['description'],
                evidence=cause['evidence'],
                confidence=cause['confidence']
            )
        
        # Check for error patterns in logs
        error_patterns = logs_results.get('exception_patterns', [])
        if error_patterns:
            base_confidence = 0.85
            # Adjust confidence if this has been a recurring cause
            if 'recurring error patterns in logs' in historical_causes:
                # Increase confidence based on how often this has been seen historically
                frequency_boost = min(0.1, 0.05 * historical_causes['recurring error patterns in logs'])
                adjusted_confidence = min(0.95, base_confidence + frequency_boost)
                historical_evidence = f"This has been a root cause in {historical_causes['recurring error patterns in logs']} previous incidents"
            else:
                adjusted_confidence = base_confidence
                historical_evidence = None
                
            cause = {
                'description': 'Recurring error patterns in logs',
                'confidence': adjusted_confidence,
                'evidence': error_patterns,
                'domain': 'logs',
                'historical_context': historical_evidence
            }
            potential_causes.append(cause)
            
            # Store the root cause in the database with high confidence
            self._store_finding(
                source='root_cause',
                description=cause['description'],
                evidence=cause['evidence'],
                confidence=cause['confidence']
            )
        
        # Check if there are historical causes that weren't detected in current analysis
        if historical_causes:
            for cause_desc, frequency in historical_causes.items():
                # Check if this historical cause is already in our current potential causes
                if not any(cause_desc.lower() in c['description'].lower() for c in potential_causes):
                    # Only add historical causes that have occurred multiple times
                    if frequency >= 2:
                        # Add historical cause with appropriate confidence
                        historical_confidence = min(0.65, 0.4 + (0.05 * frequency))  # Base confidence plus frequency bonus
                        
                        cause = {
                            'description': cause_desc.capitalize(),  # Ensure proper casing
                            'confidence': historical_confidence,
                            'evidence': f"Detected in {frequency} past similar incidents",
                            'domain': 'historical',
                            'historical_context': "Added based solely on historical patterns"
                        }
                        potential_causes.append(cause)
                        
                        # Store this historical insight
                        self._store_finding(
                            source='historical_insight',
                            description=cause['description'],
                            evidence=cause['evidence'],
                            confidence=cause['confidence']
                        )
                        
        # Sort causes by confidence (highest first)
        potential_causes.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return potential_causes
    
    def _generate_recommendations(self, k8s_results, logs_results, code_results, metrics_results) -> List[str]:
        """Generate recommendations based on investigation findings.
        
        Args:
            k8s_results: Results from Kubernetes investigation
            logs_results: Results from logs investigation
            code_results: Results from code changes investigation
            metrics_results: Results from metrics investigation
            
        Returns:
            List of recommendations for addressing the incident
        """
        recommendations = []
        
        # Kubernetes recommendations
        pod_status = k8s_results.get('pod_status', {})
        if pod_status.get('unhealthy_pods', []):
            recommendations.append(
                "Restart unhealthy pods and check their resource allocations"
            )
        
        # Code change recommendations
        risky_changes = code_results.get('risky_changes', [])
        recent_deployments = code_results.get('recent_deployments', [])
        if risky_changes and recent_deployments:
            recommendations.append(
                "Consider rolling back the most recent deployment and reviewing the identified risky changes"
            )
        
        # Metrics-based recommendations
        bottlenecks = metrics_results.get('resource_bottlenecks', {})
        if bottlenecks.get('cpu', False):
            recommendations.append(
                "Increase CPU allocation for the affected service or optimize CPU usage"
            )
        if bottlenecks.get('memory', False):
            recommendations.append(
                "Increase memory allocation for the affected service or fix memory leaks"
            )
        
        # Log-based recommendations
        error_logs = logs_results.get('error_logs', [])
        if error_logs:
            recommendations.append(
                "Address the recurring error patterns identified in the logs"
            )
        
        # Always include generic recommendations
        recommendations.append(
            "Monitor the service closely for the next 24 hours to ensure stability"
        )
        
        return recommendations


    async def run(self, **kwargs: Any) -> AsyncGenerator[RunResponse, None]:
        """Run the incident investigation workflow.
        
        This implementation uses the standard Agno RunResponse pattern for streaming
        progress updates during the investigation.
        
        Args:
            **kwargs: Additional arguments for the run
            
        Yields:
            RunResponse objects with progressive updates during the investigation
        """
        # Initialize the investigation
        service_name = self.incident_data.get('service_name', 'unknown')
        severity = self.incident_data.get('severity', 'unknown')
        incident_type = self.incident_data.get('incident_type', 'unknown')
        
        # Update run_response with initial information
        self.run_response.content = f"Starting investigation of {severity} {incident_type} incident in {service_name}"
        yield self.run_response.clone()
        
        # Check for historical context from similar incidents
        yield self._stream_event(f"Checking for similar past incidents...")
        past_insights = self.get_past_insights(service_name)
        
        if past_insights['past_incidents_count'] > 0:
            # Format historical insights for display
            patterns = past_insights.get('patterns', [])
            patterns_str = '\n  - '.join([''] + patterns) if patterns else ' None identified.'
            
            common_causes = past_insights.get('common_root_causes', [])
            causes_str = '\n  - '.join([''] + [f"{c['cause']} (seen {c['count']} times)" for c in common_causes]) if common_causes else ' None identified.'
            
            recurring_symptoms = past_insights.get('recurring_symptoms', [])
            symptoms_str = '\n  - '.join([''] + [f"{s['symptom']} (seen {s['count']} times)" for s in recurring_symptoms]) if recurring_symptoms else ' None identified.'
            
            # Share historical context
            history_message = f"\n### Historical Context\n"
            history_message += f"Found {past_insights['past_incidents_count']} similar past incidents for this service.\n\n"
            history_message += f"**Common patterns:** {patterns_str}\n\n"
            history_message += f"**Recurring root causes:** {causes_str}\n\n"
            history_message += f"**Common symptoms:** {symptoms_str}\n\n"
            history_message += "Using this historical context to guide the current investigation.\n"
            
            yield self._stream_event(history_message)
        
        # Assess the incident to determine which domains to investigate
        yield self._stream_event(f"Assessing incident details to prioritize investigation domains...")
        investigation_plan = await self.assess_incident({})
        
        # Incorporate historical insights into investigation plan
        if past_insights['past_incidents_count'] > 0:
            symptoms = [s['symptom'] for s in past_insights.get('recurring_symptoms', [])]
            
            # Add relevant domains based on historical patterns
            if 'recurring_log_errors' in symptoms and not investigation_plan.get('logs', False):
                investigation_plan['logs'] = True
                yield self._stream_event("Adding logs investigation based on historical patterns")
                
            if 'unhealthy_pods' in symptoms and not investigation_plan.get('kubernetes', False):
                investigation_plan['kubernetes'] = True
                yield self._stream_event("Adding Kubernetes investigation based on historical patterns")
                
            if 'metric_anomalies' in symptoms and not investigation_plan.get('metrics', False):
                investigation_plan['metrics'] = True
                yield self._stream_event("Adding metrics investigation based on historical patterns")
                
            if 'risky_code_changes' in symptoms and not investigation_plan.get('code_changes', False):
                investigation_plan['code_changes'] = True
                yield self._stream_event("Adding code changes investigation based on historical patterns")
        
        # Stream back the assessment results
        assessment_message = f"\nInvestigation plan based on incident assessment:\n"
        for domain, should_investigate in investigation_plan.items():
            status = "✅ Will investigate" if should_investigate else "❌ Skipping"
            assessment_message += f"  - {domain}: {status}\n"
        yield self._stream_event(assessment_message)
        
        # Update the session state with assessment results
        self.session_state['assessed'] = True
        self.session_state['investigation_plan'] = investigation_plan
        
        # Save historical context to session state
        if past_insights['past_incidents_count'] > 0:
            self.session_state['historical_insights'] = past_insights
        
        # Execute investigations based on the assessment
        results = {}
        
        # Process each domain in the investigation plan
        for domain, should_investigate in investigation_plan.items():
            if not should_investigate:
                continue
                
            # If the domain is one of our investigation domains, execute it
            if domain in self._investigation_methods:
                yield self._stream_event(f"Starting {domain} investigation...")
                
                # Set up context for this investigation with relevant historical data
                investigation_context = {}
                if past_insights['past_incidents_count'] > 0:
                    # Add domain-specific historical context if available
                    domain_symptoms = {
                        'kubernetes': 'unhealthy_pods',
                        'logs': 'recurring_log_errors',
                        'code_changes': 'risky_code_changes',
                        'metrics': 'metric_anomalies'
                    }
                    
                    if domain in domain_symptoms:
                        symptom = domain_symptoms[domain]
                        related_insights = [s for s in past_insights.get('recurring_symptoms', []) 
                                          if s['symptom'] == symptom]
                        
                        if related_insights:
                            investigation_context['historical_context'] = {
                                f'recurring_{domain}_issues': True,
                                'frequency': related_insights[0]['count']
                            }
                
                # Execute the investigation method with appropriate agent
                method = self._investigation_methods[domain]
                results[f'{domain}_investigation'] = await method(investigation_context)
                
                # Record completion in session state
                self.session_state['investigations'][domain] = True
                
                # Generate appropriate completion message based on domain
                completion_messages = {
                    'kubernetes': lambda r: f"Kubernetes investigation complete. Found {len(r.get('pod_status', {}).get('unhealthy_pods', []))} unhealthy pods.",
                    'logs': lambda r: f"Logs investigation complete. Found {len(r.get('error_patterns', []))} error patterns.",
                    'code_changes': lambda r: f"Code investigation complete. Found {len(r.get('risky_changes', []))} potentially risky changes.",
                    'metrics': lambda r: f"Metrics investigation complete. Found {len(r.get('anomalies', []))} anomalies."
                }
                
                if domain in completion_messages:
                    yield self._stream_event(completion_messages[domain](results[f'{domain}_investigation']))
                else:
                    yield self._stream_event(f"{domain} investigation complete.")
        
        # Synthesize findings across all domains
        yield self._stream_event("Synthesizing findings across all investigation domains...")
        self.session_state['synthesized'] = True
        
        # Call the synthesis method with all collected results
        synthesis = await self.synthesize_findings(results)
        
        # Store synthesis results in session state
        self.session_state['synthesis_results'] = synthesis
        
        # Format final response with root causes and recommendations
        root_causes = synthesis.get('potential_root_causes', [])
        recommendations = synthesis.get('recommendations', [])
        
        final_response = f"\n## Investigation Results for {service_name} {incident_type} incident\n\n"
        
        # Include root causes in final response
        if root_causes:
            final_response += "### Potential Root Causes\n\n"
            for i, cause in enumerate(root_causes, 1):
                confidence = cause.get('confidence', 0) * 100
                final_response += f"**{i}. {cause.get('description')}** (Confidence: {confidence:.0f}%)\n\n"
        else:
            final_response += "### No clear root causes identified\n\n"
        
        # Include recommendations in final response
        if recommendations:
            final_response += "### Recommended Actions\n\n"
            for i, recommendation in enumerate(recommendations, 1):
                final_response += f"**{i}.** {recommendation}\n\n"
        else:
            final_response += "### No specific recommendations available\n\n"
        
        # Include investigation summary
        final_response += "### Investigation Summary\n\n"
        for domain, should_investigate in investigation_plan.items():
            if should_investigate:
                domain_findings = []
                
                if domain == 'kubernetes' and 'kubernetes_investigation' in results:
                    unhealthy_pods = results['kubernetes_investigation'].get('pod_status', {}).get('unhealthy_pods', [])
                    if unhealthy_pods:
                        domain_findings.append(f"{len(unhealthy_pods)} unhealthy pods")
                        
                elif domain == 'logs' and 'logs_investigation' in results:
                    error_count = len(results['logs_investigation'].get('error_logs', []))
                    pattern_count = len(results['logs_investigation'].get('exception_patterns', []))
                    if error_count or pattern_count:
                        domain_findings.append(f"{error_count} errors, {pattern_count} patterns")
                        
                elif domain == 'code_changes' and 'code_investigation' in results:
                    deployment_count = len(results['code_investigation'].get('recent_deployments', []))
                    risky_count = len(results['code_investigation'].get('risky_changes', []))
                    if deployment_count or risky_count:
                        domain_findings.append(f"{deployment_count} deployments, {risky_count} risky changes")
                        
                elif domain == 'metrics' and 'metrics_investigation' in results:
                    anomaly_count = sum(1 for anomaly in results['metrics_investigation'].get('anomalies', {}).values() if anomaly.get('detected', False))
                    bottleneck_count = sum(1 for k, v in results['metrics_investigation'].get('resource_bottlenecks', {}).items() if k.endswith('_bottleneck') and v)
                    if anomaly_count or bottleneck_count:
                        domain_findings.append(f"{anomaly_count} anomalies, {bottleneck_count} bottlenecks")
                
                findings_text = ", ".join(domain_findings) if domain_findings else "No significant findings"
                final_response += f"- **{domain.title()}**: {findings_text}\n"
        
        # Update and yield the final response
        self.run_response.content = final_response
        yield self.run_response.clone()
        
        # Save the full results to workflow memory for future incidents
        self.add_to_memory({
            'investigation_plan': investigation_plan,
            'results': results,
            'synthesis': synthesis,
            'root_causes': root_causes,
            'recommendations': recommendations
        })
        
        yield self._stream_event("Investigation complete. Results saved to workflow memory for future reference.")
        
        return self.run_response.content
    
    
    def _stream_event(self, message: str) -> RunResponse:
        """Helper method to create a streaming event.
        
        Args:
            message: The message to include in the event
            
        Returns:
            A RunResponse with the event
        """
        self.run_response.content = message
        event = RunEvent(event_type="progress_update", data={"message": message})
        self.run_response.events.append(event)
        return self.run_response.clone()
        
    def add_to_memory(self, findings: Dict[str, Any], context: Dict[str, Any] = None) -> None:
        """Add investigation findings to workflow memory.
        
        Args:
            findings: Dictionary containing investigation results
            context: Additional context to associate with these findings
        """
        # Merge with the incident metadata
        memory_context = dict(self.memory_metadata)
        if context:
            memory_context.update(context)
            
        # Create a memory entry with findings and metadata
        memory_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'incident_id': self.incident_id,
            'findings': findings,
            'metadata': memory_context
        }
        
        # Add the run to memory
        run = WorkflowRun(
            input={'incident_data': self.incident_data},
            response=self.run_response.clone()
        )
        self.memory.add_run(run)
        
        # Store findings in memory metadata so they're available for future runs
        self.memory.set_metadata('incidents', {
            self.incident_id: memory_entry
        }, merge=True)
        
    def query_similar_incidents(self, service_name: str = None, incident_type: str = None, 
                                look_back_days: int = 30) -> List[Dict[str, Any]]:
        """Query memory for similar past incidents.
        
        Args:
            service_name: Filter incidents by service name
            incident_type: Filter incidents by incident type
            look_back_days: How far back to look for similar incidents
            
        Returns:
            List of similar incidents with their findings
        """
        similar_incidents = []
        
        # Get all past incidents from memory
        all_incidents = self.memory.get_metadata('incidents', {})
        
        # Calculate cutoff date for lookback period
        now = datetime.datetime.now()
        cutoff_date = (now - datetime.timedelta(days=look_back_days)).isoformat()
        
        # Filter incidents by criteria
        for incident_id, incident_data in all_incidents.items():
            if incident_id == self.incident_id:
                # Skip current incident
                continue
                
            # Check timestamp is within lookback period
            if incident_data.get('timestamp', '') < cutoff_date:
                continue
                
            # Match criteria if provided
            meta = incident_data.get('metadata', {})
            if service_name and meta.get('service') != service_name:
                continue
                
            if incident_type and meta.get('incident_type') != incident_type:
                continue
                
            similar_incidents.append(incident_data)
            
        return similar_incidents
        
    def store_artifact(self, content: Union[str, bytes, Dict[str, Any]], artifact_type: str, description: str, file_extension: str = None) -> str:
        """Store investigation artifacts like logs, metrics visualizations, or reports.
        
        Args:
            content: The content to store - can be text, binary, or JSON data
            artifact_type: Type of artifact (e.g., 'logs', 'metrics', 'kubernetes', 'report')
            description: Human-readable description of the artifact
            file_extension: Optional file extension (e.g., 'json', 'txt', 'png')
            
        Returns:
            Artifact ID that can be used to retrieve the artifact later
        """
        # Convert dict content to JSON string
        if isinstance(content, dict):
            content = json.dumps(content, indent=2)
            if not file_extension:
                file_extension = 'json'
                
        # Default extension for text content
        if isinstance(content, str) and not file_extension:
            file_extension = 'txt'
            
        # Generate a unique name based on type and timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{self.incident_id}_{artifact_type}_{timestamp}"
        if file_extension:
            file_name = f"{file_name}.{file_extension}"
        
        # Store the artifact with metadata
        metadata = {
            'incident_id': self.incident_id,
            'service': self.incident_data.get('service_name', 'unknown'),
            'timestamp': datetime.datetime.now().isoformat(),
            'type': artifact_type,
            'description': description
        }
        
        # Create and store the artifact
        artifact = Artifact(content=content, metadata=metadata)
        artifact_id = self.artifact_store.store(artifact, file_name)
        
        # Log the artifact creation
        self._store_finding(
            source='artifact',
            description=f"Stored {artifact_type} artifact: {description}",
            evidence={
                'artifact_id': artifact_id,
                'file_name': file_name
            },
            confidence=1.0
        )
        
        return artifact_id
        
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve a stored artifact by ID.
        
        Args:
            artifact_id: The ID of the artifact to retrieve
            
        Returns:
            The artifact if found, None otherwise
        """
        try:
            return self.artifact_store.get(artifact_id)
        except Exception as e:
            # Log the error and return None
            self._store_finding(
                source='error',
                description=f"Failed to retrieve artifact {artifact_id}",
                evidence={
                    'error': str(e)
                },
                confidence=1.0
            )
            return None
            
    def list_artifacts(self, artifact_type: str = None, include_content: bool = False) -> List[Dict[str, Any]]:
        """List artifacts related to the current incident.
        
        Args:
            artifact_type: Optional filter by artifact type
            include_content: Whether to include the actual content in the results
            
        Returns:
            List of artifacts with their metadata
        """
        artifacts = self.artifact_store.list_all()
        
        # Filter by incident_id and optionally by type
        incident_artifacts = []
        for artifact_id, artifact in artifacts.items():
            metadata = artifact.metadata
            
            # Skip if not related to this incident
            if metadata.get('incident_id') != self.incident_id:
                continue
                
            # Filter by type if specified
            if artifact_type and metadata.get('type') != artifact_type:
                continue
                
            # Create the artifact info
            artifact_info = {
                'id': artifact_id,
                'metadata': metadata,
            }
            
            # Include content if requested
            if include_content:
                if isinstance(artifact.content, bytes):
                    # Base64 encode binary content
                    artifact_info['content'] = base64.b64encode(artifact.content).decode('utf-8')
                    artifact_info['encoding'] = 'base64'
                else:
                    artifact_info['content'] = artifact.content
                    artifact_info['encoding'] = 'utf8'
            
            incident_artifacts.append(artifact_info)
            
        return incident_artifacts
    
    def _generate_markdown_report(self, summary: Dict[str, Any], root_causes: List[Dict[str, Any]], recommendations: List[str], historical_insights: Optional[Dict[str, Any]] = None) -> str:
        """Generate a human-readable markdown report of the investigation findings.
        
        Args:
            summary: The complete investigation summary
            root_causes: List of potential root causes with confidence scores
            recommendations: List of recommendations for addressing the incident
            historical_insights: Optional historical insights from past incidents
            
        Returns:
            A formatted markdown string containing the incident report
        """
        # Get incident details
        incident_data = summary.get('incident_overview', {})
        service_name = incident_data.get('service_name', 'Unknown service')
        incident_time = incident_data.get('timestamp', 'Unknown time')
        severity = incident_data.get('severity', 'Unknown')
        incident_type = incident_data.get('incident_type', 'Unknown')
        
        # Start building the report
        report = []
        
        # Title and incident overview
        report.append(f"# Incident Investigation Report: {service_name}")
        report.append(f"\n**Incident ID:** {self.incident_id}")
        report.append(f"**Time:** {incident_time}")
        report.append(f"**Service:** {service_name}")
        report.append(f"**Type:** {incident_type}")
        report.append(f"**Severity:** {severity}")
        if incident_data.get('description'):
            report.append(f"\n**Description:** {incident_data.get('description')}")
        
        # Executive summary - Root Causes section
        report.append("\n## Executive Summary\n")
        
        # Root causes summary
        report.append("### Root Causes\n")
        if root_causes:
            for i, cause in enumerate(root_causes, 1):
                confidence = cause.get('confidence', 0) * 100  # Convert to percentage
                report.append(f"**{i}. {cause.get('description', 'Unknown cause')}** _(Confidence: {confidence:.1f}%)_")
                
                # Include historical context if available
                if cause.get('historical_context'):
                    report.append(f"   - *{cause.get('historical_context')}*")
        else:
            report.append("No clear root causes were identified.")
        
        # Recommendations summary
        report.append("\n### Recommendations\n")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report.append(f"**{i}.** {rec}")
        else:
            report.append("No specific recommendations could be generated.")
            
        # Historical Context section if available
        if historical_insights and historical_insights.get('past_incidents_count', 0) > 0:
            report.append("\n## Historical Context\n")
            report.append(f"This service has experienced **{historical_insights.get('past_incidents_count', 0)}** similar incidents in the past {historical_insights.get('lookback_days', 90)} days.")
            
            # Show recurring symptoms
            if historical_insights.get('recurring_symptoms', []):
                report.append("\n### Recurring Symptoms\n")
                for symptom in historical_insights.get('recurring_symptoms', []):
                    count = symptom.get('count', 0)
                    symptom_name = symptom.get('symptom', 'Unknown')
                    report.append(f"- **{symptom_name}** _(seen in {count} incidents)_")
        
        # Detailed findings sections
        report.append("\n## Detailed Investigation Findings\n")
        
        # Kubernetes findings
        k8s_findings = summary.get('kubernetes_findings', {})
        if k8s_findings:
            report.append("### Kubernetes Investigation\n")
            
            # Pod status
            pod_status = k8s_findings.get('pod_status', {})
            if pod_status.get('unhealthy_pods', []):
                report.append(f"**Unhealthy Pods:** {len(pod_status.get('unhealthy_pods', []))} found")
                for pod in pod_status.get('unhealthy_pods', [])[:3]:  # Show first 3
                    report.append(f"- {pod.get('name', 'Unknown')}: {pod.get('status', 'Unknown')} ({pod.get('reason', 'Unknown reason')})")
                if len(pod_status.get('unhealthy_pods', [])) > 3:
                    report.append(f"- _(and {len(pod_status.get('unhealthy_pods', [])) - 3} more...)_")
            
            # Recent deployments
            if k8s_findings.get('recent_deployments', []):
                deployments = k8s_findings.get('recent_deployments', [])
                report.append(f"\n**Recent Deployments:** {len(deployments)} found")
                for deploy in deployments[:3]:  # Show first 3
                    report.append(f"- {deploy.get('name', 'Unknown')}: deployed at {deploy.get('time', 'Unknown time')}")
                if len(deployments) > 3:
                    report.append(f"- _(and {len(deployments) - 3} more...)_")
        
        # Logs findings
        logs_findings = summary.get('logs_findings', {})
        if logs_findings:
            report.append("\n### Log Analysis\n")
            
            # Error logs
            error_logs = logs_findings.get('error_logs', [])
            if error_logs:
                report.append(f"**Error Logs:** {len(error_logs)} errors found")
                for error in error_logs[:3]:  # Show first 3
                    message = error.get('message', 'Unknown error')
                    if len(message) > 100:
                        message = message[:97] + '...'
                    report.append(f"- `{message}`")
                if len(error_logs) > 3:
                    report.append(f"- _(and {len(error_logs) - 3} more...)_")
            
            # Exception patterns
            exception_patterns = logs_findings.get('exception_patterns', [])
            if exception_patterns:
                report.append(f"\n**Exception Patterns:** {len(exception_patterns)} patterns identified")
                for pattern in exception_patterns[:3]:  # Show first 3
                    report.append(f"- {pattern.get('pattern', 'Unknown')}: {pattern.get('count', 0)} occurrences")
                if len(exception_patterns) > 3:
                    report.append(f"- _(and {len(exception_patterns) - 3} more...)_")
        
        # Code changes findings
        code_findings = summary.get('code_change_findings', {})
        if code_findings:
            report.append("\n### Code Analysis\n")
            
            # Risky changes
            risky_changes = code_findings.get('risky_changes', [])
            if risky_changes:
                report.append(f"**Risky Code Changes:** {len(risky_changes)} identified")
                for change in risky_changes[:3]:  # Show first 3
                    report.append(f"- {change.get('file', 'Unknown file')}: {change.get('description', 'No description')}")
                if len(risky_changes) > 3:
                    report.append(f"- _(and {len(risky_changes) - 3} more...)_")
        
        # Metrics findings
        metrics_findings = summary.get('metrics_findings', {})
        if metrics_findings:
            report.append("\n### Metrics Analysis\n")
            
            # Anomalies
            anomalies = metrics_findings.get('anomalies', [])
            if anomalies:
                report.append(f"**Metric Anomalies:** {len(anomalies)} detected")
                for anomaly in anomalies[:3]:  # Show first 3
                    report.append(f"- {anomaly.get('metric', 'Unknown metric')}: {anomaly.get('description', 'No description')}")
                if len(anomalies) > 3:
                    report.append(f"- _(and {len(anomalies) - 3} more...)_")
            
            # Resource bottlenecks
            bottlenecks = metrics_findings.get('resource_bottlenecks', {})
            if bottlenecks:
                report.append(f"\n**Resource Bottlenecks:**")
                for resource, details in bottlenecks.items():
                    report.append(f"- {resource}: {details.get('description', 'No details')}")
        
        # Correlated findings
        if summary.get('correlated_findings', []):
            report.append("\n### Correlated Findings\n")
            for finding in summary.get('correlated_findings', []):
                report.append(f"- {finding}")
        
        # Evidence and artifacts section
        artifacts = self.list_artifacts()
        if artifacts:
            report.append("\n## Evidence\n")
            report.append(f"**{len(artifacts)}** evidence artifacts were collected during this investigation.\n")
            
            # Group artifacts by type
            artifact_types = {}
            for artifact in artifacts:
                artifact_type = artifact.get('metadata', {}).get('type', 'unknown')
                if artifact_type not in artifact_types:
                    artifact_types[artifact_type] = []
                artifact_types[artifact_type].append(artifact)
            
            for artifact_type, items in artifact_types.items():
                report.append(f"### {artifact_type.capitalize()} Evidence\n")
                for item in items:
                    metadata = item.get('metadata', {})
                    report.append(f"- **{metadata.get('description', 'Unknown')}** _(ID: {item.get('id', 'Unknown')})_")
        
        # Footer with timestamp
        report.append(f"\n---\n\n*Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(report)
    
    def get_past_insights(self, service_name: str = None) -> Dict[str, Any]:
        """Analyze past incidents to find patterns and insights.
        
        This method analyzes past incidents to provide context and insights for the
        current investigation.
        
        Args:
            service_name: Optionally filter insights to specific service
            
        Returns:
            Dictionary of insights derived from past incidents
        """
        # Get similar incidents from memory
        service = service_name or self.incident_data.get('service_name')
        similar_incidents = self.query_similar_incidents(service_name=service)
        
        if not similar_incidents:
            return {
                'past_incidents_count': 0,
                'patterns': [],
                'common_root_causes': [],
                'recurring_symptoms': []
            }
            
        # Count occurrences of root causes
        root_causes = {}
        symptoms = {}
        services_affected = set()
        
        for incident in similar_incidents:
            # Extract metadata
            meta = incident.get('metadata', {})
            services_affected.add(meta.get('service', 'unknown'))
            
            # Extract findings
            findings = incident.get('findings', {})
            
            # Process root causes
            for cause in findings.get('potential_root_causes', []):
                desc = cause.get('description', '')
                if desc:
                    root_causes[desc] = root_causes.get(desc, 0) + 1
                    
            # Process symptoms from different domains
            for domain in ['kubernetes', 'logs', 'metrics', 'code_changes']:
                domain_data = findings.get(f'{domain}_investigation', {})
                
                if domain == 'kubernetes':
                    # Track unhealthy pods
                    pod_status = domain_data.get('pod_status', {})
                    unhealthy_pods = len(pod_status.get('unhealthy_pods', []))
                    if unhealthy_pods > 0:
                        symptom = 'unhealthy_pods'
                        symptoms[symptom] = symptoms.get(symptom, 0) + 1
                        
                elif domain == 'logs':
                    # Track error patterns
                    error_patterns = domain_data.get('exception_patterns', [])
                    if error_patterns:
                        symptom = 'recurring_log_errors'
                        symptoms[symptom] = symptoms.get(symptom, 0) + 1
                        
                elif domain == 'metrics':
                    # Track anomalies
                    anomalies = domain_data.get('anomalies', {})
                    if any(a.get('detected', False) for a in anomalies.values()):
                        symptom = 'metric_anomalies'
                        symptoms[symptom] = symptoms.get(symptom, 0) + 1
                        
                elif domain == 'code_changes':
                    # Track risky changes
                    if domain_data.get('risky_changes', []):
                        symptom = 'risky_code_changes'
                        symptoms[symptom] = symptoms.get(symptom, 0) + 1
        
        # Sort by frequency
        sorted_causes = sorted(
            [{'cause': k, 'count': v} for k, v in root_causes.items()],
            key=lambda x: x['count'],
            reverse=True
        )
        
        sorted_symptoms = sorted(
            [{'symptom': k, 'count': v} for k, v in symptoms.items()],
            key=lambda x: x['count'],
            reverse=True
        )
        
        # Identify patterns across incidents
        patterns = []
        if len(similar_incidents) >= 3:
            # If we see the same root cause multiple times
            if sorted_causes and sorted_causes[0]['count'] >= 2:
                patterns.append(f"Recurring root cause: {sorted_causes[0]['cause']}")
                
            # If we see the same symptom multiple times
            if sorted_symptoms and sorted_symptoms[0]['count'] >= 2:
                patterns.append(f"Recurring symptom: {sorted_symptoms[0]['symptom']}")
        
        return {
            'past_incidents_count': len(similar_incidents),
            'patterns': patterns,
            'common_root_causes': sorted_causes[:3],  # Top 3 causes
            'recurring_symptoms': sorted_symptoms[:3],  # Top 3 symptoms
            'services_affected': list(services_affected)
        }


def create_incident_investigation_workflow(incident_data: Dict[str, Any]) -> IncidentInvestigationWorkflow:
    """Factory function to create an incident investigation workflow.
    
    Args:
        incident_data: Dictionary containing incident details
        
    Returns:
        Configured IncidentInvestigationWorkflow instance
    """
    return IncidentInvestigationWorkflow(incident_data)