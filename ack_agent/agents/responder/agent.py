from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the responder agent
from ack_agent.tools.pagerduty.tools import PagerDutyTools

def create_responder_agent():
    """Create a responder agent that acknowledges PagerDuty incidents.
    
    The Responder agent is responsible for:
    - Acknowledging the PagerDuty incident
    - Extracting key information about the incident (service, criticality, severity)
    - Providing initial context to the Investigator agent
    
    Returns:
        Agent: An Agno agent configured for incident response
    """
    # Initialize tools
    pagerduty_tools = PagerDutyTools()
    
    # Create the agent
    responder = Agent(
        name="Responder",
        role="First responder to acknowledge PagerDuty incidents and extract key information",
        goal="Acknowledge PagerDuty incidents and provide context to the investigation team",
        tools=[pagerduty_tools],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are the Responder agent for Ack Agent, responsible for being the first "
            "point of contact for PagerDuty incidents. You acknowledge incidents in PagerDuty "
            "and extract essential information to help guide the investigation process."
        ),
        instructions=[
            "Acknowledge PagerDuty incidents promptly",
            "Extract key information: service name, criticality, severity, alert message",
            "Be concise and to the point in all communications",
            "Do not use emojis in any communications"
        ]
    )
    
    return responder
