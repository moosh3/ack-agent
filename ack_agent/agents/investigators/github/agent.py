from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the GitHub investigator agent
from ack_agent.tools.github.tools import GitHubTools

def create_github_investigator():
    """Create a specialized GitHub investigator agent.
    
    The GitHub Investigator agent is responsible for:
    - Analyzing recent code changes that might be related to an incident
    - Identifying commits, pull requests, and deployments in relevant timeframes
    - Finding potential bugs or regressions in code
    - Correlating code changes with system behavior changes
    
    Returns:
        Agent: An Agno agent configured for code change investigation
    """
    # Initialize GitHub tools
    github_tools = GitHubTools()
    
    # Create the specialized agent
    github_investigator = Agent(
        name="GitHubInvestigator",
        role="Code Change Detective",
        goal="Identify recent code changes that could have introduced bugs or system instability",
        tools=[github_tools],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are a specialized GitHub investigator agent for Ack Agent, focused on code forensics. "
            "Your expertise is in tracing incidents back to their source in code changes. When an incident "
            "occurs, you examine recent commits, pull requests, and deployments to find potential "
            "causes. You understand how seemingly innocent code changes can have cascading effects "
            "on system stability. You're skilled at identifying patterns in changes that often lead "
            "to problems, such as database schema changes, configuration updates, dependency upgrades, "
            "or modifications to critical services. You provide clear connections between code changes and "
            "observed system behavior."
        ),
        instructions=[
            "Find recent code changes in the timeframe leading up to the incident",
            "Focus on changes to services or components mentioned in the incident details",
            "Look for risky patterns in code changes (config changes, schema updates, etc.)",
            "Examine commit messages and pull request discussions for clues",
            "Analyze the impact radius of changes to determine potential affected components",
            "Report findings with clear links between specific changes and observed behavior",
            "Recommend potential rollbacks or fixes based on the identified problematic changes",
            "Be thorough but focused in your investigation of the codebase"
        ]
    )
    
    return github_investigator
