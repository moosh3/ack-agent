import os
from typing import Dict, Any, List, Optional
from agno.tools import Tool, tool

class SlackTools(Tool):
    """Tool for interacting with Slack API.
    
    This tool allows agents to interact with Slack for communication,
    including creating channels, inviting users, and sending messages.
    """
    name = "slack"
    description = "Tools for interacting with Slack for communication"
    
    def __init__(self):
        """Initialize the Slack tools with API tokens from environment variables."""
        super().__init__()
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        if not self.bot_token or not self.app_token:
            raise ValueError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN environment variables are required")
    
    @tool("Create a Slack channel")
    def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new Slack channel.
        
        Args:
            name: The name of the channel to create (without '#')
            is_private: Whether the channel should be private (default: False)
            
        Returns:
            Dict containing channel details
        """
        # TODO: Implement actual Slack API call using slack_sdk
        # For now, return a mock response for development
        channel_id = f"C{name.upper()}123"
        return {
            "ok": True,
            "channel": {
                "id": channel_id,
                "name": name,
                "is_private": is_private,
                "created": 1712043000  # Unix timestamp
            }
        }
    
    @tool("Invite users to a Slack channel")
    def invite_to_channel(self, channel_id: str, user_ids: List[str]) -> Dict[str, Any]:
        """Invite users to a Slack channel.
        
        Args:
            channel_id: The ID of the channel to invite users to
            user_ids: List of user IDs to invite
            
        Returns:
            Dict containing the result of the invitation
        """
        # TODO: Implement actual Slack API call
        return {
            "ok": True,
            "channel": channel_id,
            "invited_users": user_ids
        }
    
    @tool("Send a message to a Slack channel")
    def send_message(self, channel_id: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send a message to a Slack channel.
        
        Args:
            channel_id: The ID of the channel to send the message to
            text: The text of the message
            blocks: Optional blocks for rich formatting (Slack Block Kit)
            
        Returns:
            Dict containing the result of sending the message
        """
        # TODO: Implement actual Slack API call
        message_id = "M123456789"
        return {
            "ok": True,
            "channel": channel_id,
            "ts": "1712043000.123456",  # Timestamp used as message ID in Slack
            "message": {
                "text": text,
                "user": "BOT_USER_ID",
                "bot_id": "B123",
                "blocks": blocks or []
            }
        }
    
    @tool("Get users in a Slack team")
    def get_users(self) -> List[Dict[str, Any]]:
        """Get a list of users in the Slack workspace.
        
        Returns:
            List of dicts containing user details
        """
        # TODO: Implement actual Slack API call
        # For now, return mock data for development
        return [
            {
                "id": "U123",
                "name": "jane.smith",
                "real_name": "Jane Smith",
                "email": "jane.smith@example.com",
                "team_id": "T123"
            },
            {
                "id": "U456",
                "name": "john.doe",
                "real_name": "John Doe",
                "email": "john.doe@example.com",
                "team_id": "T123"
            }
        ]
    
    @tool("Create a formatted incident summary message")
    def format_incident_summary(self, 
                               incident_id: str, 
                               title: str, 
                               severity: str,
                               service: str,
                               description: str,
                               possible_causes: List[str],
                               next_steps: List[str],
                               links: Dict[str, str]) -> Dict[str, Any]:
        """Create a formatted incident summary message using Slack Block Kit.
        
        Args:
            incident_id: The ID of the incident
            title: The title of the incident
            severity: The severity of the incident
            service: The affected service
            description: Description of the incident
            possible_causes: List of possible causes
            next_steps: List of recommended next steps
            links: Dict of link titles to URLs
            
        Returns:
            Dict containing formatted blocks for Slack message
        """
        # Create a formatted Block Kit message for incident summary
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Incident Summary: {title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*ID:* {incident_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {severity}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Service:* {service}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{description}"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add possible causes
        causes_text = "*Possible Causes:*\n"
        for i, cause in enumerate(possible_causes, 1):
            causes_text += f"{i}. {cause}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": causes_text
            }
        })
        
        # Add next steps
        steps_text = "*Recommended Next Steps:*\n"
        for i, step in enumerate(next_steps, 1):
            steps_text += f"{i}. {step}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": steps_text
            }
        })
        
        # Add links
        if links:
            links_text = "*Relevant Links:*\n"
            for title, url in links.items():
                links_text += f"• <{url}|{title}>\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": links_text
                }
            })
        
        return {"blocks": blocks}
