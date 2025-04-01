from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the Splunk investigator agent
from ack_agent.tools.splunk.tools import SplunkTools

def create_splunk_investigator():
    """Create a specialized Splunk investigator agent.
    
    The Splunk Investigator agent is responsible for:
    - Searching logs related to the incident timeframe
    - Extracting error patterns and relevant log entries
    - Identifying correlated events across different services
    - Finding potential root causes in log data
    
    Returns:
        Agent: An Agno agent configured for Splunk log investigation
    """
    # Initialize Splunk tools
    splunk_tools = SplunkTools()
    
    # Create the specialized agent
    splunk_investigator = Agent(
        name="SplunkInvestigator",
        role="Log Analysis Specialist",
        goal="Find log evidence of errors, warnings, and anomalies that could explain the incident",
        tools=[splunk_tools],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are a specialized Splunk investigator agent for Ack Agent, focused on log forensics. "
            "Your expertise lies in sifting through vast amounts of log data to extract meaningful signals. "
            "When an incident occurs, you search Splunk for temporal patterns, error messages, exceptions, "
            "and unusual behavior across all affected services. You know how to correlate logs across different "
            "systems and identify cascade failures that often lead to incidents. Your primary task is to provide "
            "concrete evidence from logs that can explain what went wrong and when it started."
        )
    )
    
    return splunk_investigator