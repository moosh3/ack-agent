from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat

# Import specialized investigator agents
from ack_agent.agents.investigators.kubernetes.agent import create_kubernetes_investigator
from ack_agent.agents.investigators.splunk.agent import create_splunk_investigator
from ack_agent.agents.investigators.github.agent import create_github_investigator
from ack_agent.agents.investigators.metrics.agent import create_metrics_investigator


def create_investigation_team():
    """Create a team of specialized investigator agents.
    
    This function creates and configures a team of investigators, each specializing
    in different data sources:
    - Kubernetes Investigator: Monitors cluster health and infrastructure issues
    - Splunk Investigator: Analyzes logs and identifies error patterns
    - GitHub Investigator: Examines code changes that might relate to the incident
    - Metrics Investigator: Analyzes system metrics from Grafana and Prometheus
    
    Returns:
        Team: An Agno team instance configured for comprehensive investigation
    """
    # Create specialized investigator agents
    kubernetes_investigator = create_kubernetes_investigator()
    splunk_investigator = create_splunk_investigator()
    github_investigator = create_github_investigator()
    metrics_investigator = create_metrics_investigator()
    
    # Create and configure the investigation team
    investigation_team = Team(
        mode="coordinate",
        enable_agentic_context=True,
        share_member_interactions=True,
        show_tool_calls=True,
        markdown=True,
        members=[
            kubernetes_investigator,
            splunk_investigator,
            github_investigator,
            metrics_investigator
        ],
        model=OpenAIChat(id="gpt-4o"),
        success_criteria=(
            "Successfully gathered comprehensive data from all required sources, "
            "identified relevant patterns and anomalies, and provided actionable "
            "insights that contribute to incident resolution."
        ),
        instructions=[
            "Coordinate investigations across specialized agents based on incident details",
            "First determine which systems are most likely involved in the incident",
            "Direct each agent to investigate their specialized domain in parallel",
            "Consolidate findings and prioritize the most relevant information",
            "Focus on identifying the root cause through multi-system correlation",
            "Maintain clear communication about findings and investigation progress",
            "Be thorough but efficient in data collection and analysis"
        ]
    )
    
    return investigation_team


def create_investigation_coordinator():
    """Create a coordinator agent that manages the specialized investigators.
    
    This function creates an agent that serves as a high-level coordinator for
    the investigation process, delegating work to the specialized team.
    
    Returns:
        Agent: An Agno agent configured to coordinate investigations
    """
    # Create the team of specialized investigators
    investigation_team = create_investigation_team()
    
    # Create the coordinator agent
    coordinator = Agent(
        name="InvestigationCoordinator",
        role="Investigation Team Lead",
        goal="Orchestrate comprehensive data gathering from all relevant systems to support incident analysis",
        tools=[],  # Coordinator doesn't use tools directly, delegates to team members
        team=investigation_team,  # Assign the team to the coordinator
        model=OpenAIChat(id="o1"),
        backstory=(
            "You are the Investigation Coordinator for Ack Agent, responsible for orchestrating "
            "a team of specialized investigators during incidents. Your expertise lies in understanding "
            "which data sources are most relevant for different types of incidents and efficiently "
            "delegating investigation tasks. You excel at synthesizing information from various sources "
            "into a coherent picture of what happened, when, and why. Your team includes specialists in "
            "Kubernetes infrastructure, log analysis, code changes, and system metrics."
        ),
        instructions=[
            "Assess incident details and determine which systems should be investigated",
            "Delegate specific investigation tasks to your team of specialists",
            "Synthesize findings from different sources to build a coherent incident timeline",
            "Identify correlations between findings from different investigation domains",
            "Provide clear summaries of discovered evidence and potential causes",
            "Be methodical and thorough in your investigation approach",
            "Prioritize speed and efficiency in your investigation process"
        ]
    )
    
    return coordinator
