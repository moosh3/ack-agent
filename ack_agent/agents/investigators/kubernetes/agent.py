from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Import tools for the Kubernetes investigator agent
from ack_agent.tools.kubernetes.tools import KubernetesTools

def create_kubernetes_investigator():
    """Create a specialized Kubernetes investigator agent.
    
    The Kubernetes Investigator agent is responsible for:
    - Monitoring cluster health during an incident
    - Identifying failed or degraded services in the cluster
    - Checking pod status, resource utilization, and node health
    - Examining Kubernetes events for errors and warnings
    
    Returns:
        Agent: An Agno agent configured for Kubernetes infrastructure investigation
    """
    # Initialize Kubernetes tools
    kubernetes_tools = KubernetesTools()
    
    # Create the specialized agent
    kubernetes_investigator = Agent(
        name="KubernetesInvestigator",
        role="Infrastructure Health Specialist",
        goal="Diagnose Kubernetes cluster issues and identify components causing or affected by an incident",
        tools=[kubernetes_tools],
        model=OpenAIChat(id="o1"),  # Using o1 as specified in the PRD
        backstory=(
            "You are a specialized Kubernetes investigator agent for Ack Agent, focused on infrastructure health. "
            "Your expertise is in diagnosing Kubernetes cluster problems, identifying service degradation, "
            "and pinpointing resource constraints or conflicts. When an incident occurs, you check pod status, "
            "examine node health metrics, review recent deployments, and analyze events across the cluster. "
            "You understand how different components of the cluster interact and can quickly identify "
            "whether infrastructure issues are the cause or a symptom of the broader incident."
        ),
        instructions=[
            "Analyze overall cluster health including nodes, pods, and control plane components",
            "Check for resource constraints (CPU, memory, disk) on affected services",
            "Review recent deployments or configuration changes that might have caused issues",
            "Examine pod logs for errors in affected services",
            "Look for correlation between node issues and service degradation",
            "Report clear technical assessments about the state of the Kubernetes environment",
            "Be thorough but efficient in your infrastructure investigation",
            "Provide specific recommendations for stabilizing the infrastructure"
        ]
    )
    
    return investigator
