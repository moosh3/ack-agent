from agno.team import Team
from agno.models.openai import OpenAIChat

# Import individual agents
from ack_agent.agents.responder.agent import create_responder_agent
from ack_agent.agents.investigator.agent import create_investigator_agent
from ack_agent.agents.analyst.agent import create_analyst_agent
from ack_agent.agents.manager.agent import create_manager_agent


def create_incident_team():
    """Create an incident response team with specialized agents.
    
    The team follows a coordinate mode, where each agent has a specific role:
    - Responder: Acknowledges incidents and manages initial response
    - Investigator: Retrieves data from external services
    - Analyst: Analyzes data and summarizes potential causes
    - Manager: Creates Slack channels, assigns incidents, and coordinates communication
    
    Returns:
        Team: An Agno team instance configured for incident response
    """
    # Create individual agents
    responder = create_responder_agent()
    investigator = create_investigator_agent()
    analyst = create_analyst_agent()
    manager = create_manager_agent()
    
    # Create and configure the team
    incident_team = Team(
        mode="coordinate",  # Use coordinate mode to organize the team workflow
        members=[
            responder,
            investigator,
            analyst,
            manager
        ],
        model=OpenAIChat(id="gpt-4o"),  # Team coordinator model as specified in PRD
        success_criteria=(
            "Successfully acknowledged and responded to the PagerDuty incident, "
            "gathered relevant information, created a Slack channel if necessary, "
            "and provided a clear summary with potential next steps."
        ),
        instructions=[
            "Coordinate the incident response across all team members",
            "Ensure each agent completes their specific tasks in the appropriate sequence",
            "Prioritize incident resolution within the 2-minute SLA requirement",
            "Be concise and to the point in all communications",
            "Do not use emojis in any communications"
        ]
    )
    
    return incident_team
