from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the investigator agent
from ack_agent.tools.prometheus.tools import PrometheusTools
from ack_agent.tools.splunk.tools import SplunkTools
from ack_agent.tools.grafana.tools import GrafanaTools
from ack_agent.tools.kubernetes.tools import KubernetesTools
from ack_agent.tools.github.tools import GitHubTools

def create_investigator_agent():
    """Create an investigator agent that retrieves data from various services.
    
    The Investigator agent is responsible for:
    - Retrieving relevant data from PagerDuty, Prometheus, Splunk, GitHub, Kubernetes
    - Identifying metrics, logs, and events related to the incident
    - Providing context to the Analyst agent for incident analysis
    
    Returns:
        Agent: An Agno agent configured for data investigation
    """
    # Initialize tools
    prometheus_tools = PrometheusTools()
    splunk_tools = SplunkTools()
    grafana_tools = GrafanaTools()
    kubernetes_tools = KubernetesTools()
    github_tools = GitHubTools()
    
    # Create the agent
    investigator = Agent(
        name="Investigator",
        role="Data retriever from multiple monitoring and operational systems",
        goal="Gather relevant information from all available sources to support incident analysis",
        tools=[
            prometheus_tools,
            splunk_tools,
            grafana_tools,
            kubernetes_tools,
            github_tools
        ],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are the Investigator agent for Ack Agent, responsible for gathering data "
            "from various systems to provide context and supporting evidence for incident analysis. "
            "You excel at knowing which systems to query based on the incident details."
        ),
        instructions=[
            "Identify which systems are most relevant to investigate based on the incident details",
            "Query Prometheus for metrics related to the incident",
            "Search Splunk for relevant logs",
            "Retrieve Grafana dashboards to visualize system state",
            "Check Kubernetes events for relevant pods, nodes, and cluster health",
            "Review recent GitHub commits that might be related to the incident",
            "Be thorough but efficient in your data collection",
            "Be concise and to the point in all communications",
            "Do not use emojis in any communications"
        ]
    )
    
    return investigator
