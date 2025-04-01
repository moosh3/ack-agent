# AI Agent Product Requirements Document

## 1. Product Overview
### 1.1 Vision Statement
Ack Agent will be a first responder to company incidents. Using tools, it will respond to PagerDuty incidents, retrieve relevant information, and take action to resolve the issue. If it cannot resolve the issue, it will create a Slack channel and invite team members to help resolve the issue.

### 1.2 Problem Statement
Currently, team members who are on call are often left to fend for themselves when an incident occurs. They may not have the necessary information to resolve the issue, and they may not have the necessary tools to do so. When an incident occurs, they must spend precious time searching for logs, graphs, and other relevant information to investigate the issue. They also need to coordinate with other team members to resolve the issue.

### 1.3 Target Users
Support engineers who respond to PagerDuty incidents when on call

### 1.4 Success Metrics
- Incident resolution time
- Incident resolution rate
- Incident resolution quality

## 2. Use Cases

### 2.1 Key Use Cases
1. **Use Case 1**: Respond to PagerDuty incident
   - Trigger: PagerDuty incident
   - Flow: 
        - The Responder agent acknowledges the PagerDuty incident, and provides relevant information to the Investigator about what service is impacted, the criticality, and the severity of the incident
        - The Investigator agent uses tools to retrieve relevant information from PagerDuty, Prometheus, Splunk, GitHub, and Kubernetes. For example, it may notice that a Kubernetes node of which the PagerDuty alert was trigger from is reporting down, and invites the on call member from the Container Infrastructure team. They may also see that the application's Prometheus metrics show a spike in database connections, and therefore invites the on call member of the team that owns the application, along with the on call engineer on the Database team.
        - The Analyst will attempt to summarize the possible cause of the issue. It will join the Slack channel the Manager creates, and present relevant information to the user in a clear and concise manner, along with possible next steps. It can also answer user queries and provide additional information to the user.
        - The Manager will create a Slack channel and invite team members to help resolve the issue. Finally, the original PagerDuty incident is assigned to the on call engineer that the agent identified as the owner of the application.

## 3. Functional Requirements

### 3.1 Core Capabilities
- Use Agent Teams so multiple agents can work on the same incident
    - Responder to acknowledge the incident, create a Slack channel, and invite team members to help resolve the issue
    - Investigator to identify useful information from external sources 
    - Analyst to reason on the cause of the issue based on metrics from Prometheus, trends shown in Grafana dashboards, logs from Splunk, Kubernetes events on pods, nodes, and the cluster health, recent GitHub commits, and other relevant information provided by the Investigator
    - Manager to triage the incident, present the summary of the issue to the user in a clear and concise manner, along with possible next steps identified by reasoning over the retrieved information, and assign the incident to a team member once the Slack channel is created. The Manager will also answer questions from the user about the issue using the context it has gathered via external sources to the best of its ability, with links to the information it used to answer the question
- Retrieve relevant information from PagerDuty, Prometheus, Splunk, Grafana, Kubernetes events, GitHub and other sources
- Attempt to summarize the possible cause of the issue using the information pulled from external sources
- Reason on the cause of the issue based on metrics from Prometheus, trends shown in Grafana dashboards, logs from Splunk, Kubernetes events on pods, nodes, and the cluster health, recent GitHub commits, and other relevant information
- Gather and present a summary of the issue to the user in a clear and concise manner, along with possible next steps identified by reasoning over the retrieved information
- Create Slack channels and invite team members to help resolve the issue
- Answer questions from the user about the issue using the context it has gathered via external sources to the best of its ability, with links to the information it used to answer the question

### 3.2 Input Processing
- The agent will receive PagerDuty incidents via a webhook in JSON format
- Using tools, the agent will retrieve relevant information from PagerDuty, Prometheus, Splunk, GitHub, and Kubernetes using tools supported by the Agno agent framework. If a tool does not exist for the external service, the agent will use an MCP tool instead.

### 3.3 Output Generation
- Markdown formatted response with embedded images of Grafana dashboard, Prometheus queries, Splunk log messages, Kubernetes events, GitHub commits, and other relevant information

### 3.4 Context Handling
- [Specify how the agent should maintain context in conversations]
- [Define memory requirements and limitations]

### 3.5 Error Handling
- [Define how the agent should respond to errors, invalid inputs, etc.]

## 4. Technical Requirements

### 4.1 Agent Framework and Components
- Agno [https://docs.agno.com/]
- Agno Agent Teams for breaking up the investigation into smaller tasks
- PgVector for vector database
- PostgreSQL for database and storage

### 4.2 Integration Points
- PagerDuty
- Prometheus
- Splunk
- Grafana
- Kubernetes
- GitHub
- Slack

### 4.3 Model Specifications
- Base model reasoning model: OpenAI o1 or o3-mini
- Tool calling model: OpenAI gpt-4o

### 4.4 Development Environment
- Python 3.12 with virtual environment
- Docker compose for local development

### 4.5 Performance Requirements
- Response time: 2 minutes or less before creating the Slack channel
- Availability: 99.9%

### 4.6 Security Requirements
- All data is encrypted in transit and at rest
- All data is stored in a secure database
- All data is protected by authentication and authorization

## 5. User Experience

### 5.1 Interaction Design
- All interactions will be via Slack messages. The agent will use the Slack API to send and receive messages.
- Users can start a Slack thread on the original message the agent sends to the newly created Slack channel to query the agent about the issue.

### 5.2 Tone and Personality
- The agent will be concise and to the point
- It will not use emojis

## 6. Future Roadmap

### 6.1 Planned Enhancements
- Be able to take action on the issue. For example, restarting a Kubernetes pod or a deployment, or reverting a GitHub pull request that is causing the issue. 

### 6.2 Extensibility Considerations
- It should be extensible to add new tools and services for additional context when triaging an issue and reasoning on the cause of the issue

## 7. Appendices

### 7.1 Glossary
- [Define key terms and technical concepts]

### 7.2 References
- Agno Agent Team https://docs.agno.com/teams/coordinat
- Agno PgVector https://docs.agno.com/vectordb/pgvector
- PagerDuty MCP Server https://github.com/wpfleger96/pagerduty-mcp-server
- Prometheus MCP Server https://github.com/pab1it0/prometheus-mcp-server
- Grafana MCP Server https://github.com/grafana/mcp-grafana
- Kubernetes MCP Server https://github.com/Flux159/mcp-server-kubernetes
- GitHub MCP Server https://github.com/modelcontextprotocol/servers/tree/main/src/github