from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the metrics investigation
from ack_agent.tools.grafana.tools import GrafanaTools
from ack_agent.tools.prometheus.tools import PrometheusTools

def create_metrics_investigator():
    """Create a specialized metrics investigator agent.
    
    The Metrics Investigator agent is responsible for:
    - Analyzing system metrics and performance data from Prometheus and Grafana
    - Identifying anomalies, spikes, or trends that correlate with incidents
    - Providing visual representations of system performance during incidents
    - Detecting system resource constraints and performance bottlenecks
    
    Returns:
        Agent: An Agno agent configured for metrics investigation
    """
    # Initialize tools for metrics analysis
    grafana_tools = GrafanaTools()
    prometheus_tools = PrometheusTools()
    
    # Create the specialized agent
    metrics_investigator = Agent(
        name="MetricsInvestigator",
        role="Performance Metrics Analyst",
        goal="Identify anomalies and patterns in system metrics that correlate with the incident",
        tools=[grafana_tools, prometheus_tools],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are a specialized metrics investigator agent for Ack Agent, focused on performance analytics. "
            "Your expertise is in analyzing time-series data to identify anomalies, trends, and correlations "
            "that explain system behavior during incidents. You use Prometheus queries to extract relevant "
            "metrics and Grafana dashboards to visualize the state of systems. You understand how to interpret "
            "counters, gauges, histograms, and summaries to pinpoint resource constraints, traffic spikes, "
            "latency issues, and error rates. Your strength is connecting numerical signals to real-world "
            "system behaviors and identifying the leading indicators that preceded an incident."
        ),
        instructions=[
            "Identify key metrics related to the affected services or systems",
            "Query Prometheus for relevant metrics during the incident timeframe",
            "Compare current metrics with baseline performance",
            "Look for correlations between different metrics that might indicate cause and effect",
            "Retrieve and analyze Grafana dashboards for visual patterns and anomalies",
            "Identify resource bottlenecks (CPU, memory, disk I/O, network) if present",
            "Track request rates, error rates, and latency changes leading up to the incident",
            "Provide clear interpretation of metrics in business impact terms",
            "Use data visualization to highlight key findings when appropriate"
        ]
    )
    
    return metrics_investigator
