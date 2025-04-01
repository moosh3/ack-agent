from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the manager agent
from ack_agent.tools.slack.tools import SlackTools
from ack_agent.tools.pagerduty.tools import PagerDutyTools

def create_manager_agent():
    """Create a manager agent that coordinates incident response and communication.
    
    The Manager agent is responsible for:
    - Creating Slack channels for incident discussion
    - Inviting appropriate team members to the channel
    - Assigning the incident to the appropriate on-call engineer
    - Presenting clear summaries and possible next steps
    - Answering questions from users about the incident
    
    Returns:
        Agent: An Agno agent configured for incident management
    """
    # Initialize tools
    slack_tools = SlackTools()
    pagerduty_tools = PagerDutyTools()
    
    # Create the agent
    manager = Agent(
        name="Manager",
        role="Incident coordinator and communication manager",
        goal="Create communication channels, assign incidents, and provide clear information to stakeholders",
        tools=[slack_tools, pagerduty_tools],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are the Manager agent for Ack Agent, responsible for coordinating the incident "
            "response process. You create Slack channels, bring in the right team members, "
            "assign incidents to the appropriate on-call engineers, and ensure clear "
            "communication throughout the incident lifecycle."
        ),
        instructions=[
            "Create Slack channels for incident discussion with a clear naming convention",
            "Invite appropriate team members based on the incident context and service ownership",
            "Assign the PagerDuty incident to the identified service owner",
            "Present incident summaries in a clear, concise format with markdown formatting",
            "Include links to relevant information sources in your communications",
            "Answer user questions using the context gathered during investigation",
            "Be concise and to the point in all communications",
            "Do not use emojis in any communications"
        ]
    )
    
    return manager
