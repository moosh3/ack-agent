import os
from fastapi import FastAPI, Request, Response, status
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Import agent team
from ack_agent.teams.incident_team import create_incident_team

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Ack Agent", description="First responder to company incidents")


class PagerDutyWebhook(BaseModel):
    """Model for PagerDuty webhook payload"""
    messages: list[Dict[str, Any]]
    

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "ack_agent"}


@app.post("/webhook/pagerduty")
async def pagerduty_webhook(payload: PagerDutyWebhook):
    """Endpoint for PagerDuty webhook
    
    This endpoint receives PagerDuty incidents via webhooks and triggers
    the incident response process with the agent team.
    """
    try:
        # For each message in the webhook payload
        for message in payload.messages:
            # Create the incident team
            incident_team = create_incident_team()
            
            # Process the incident
            result = incident_team.run({
                "incident_data": message,
                "goal": "Respond to the PagerDuty incident, gather relevant information, and take appropriate action."
            })
            
            # TODO: Log the result in database
        
        return {"status": "success", "message": "Incident processing initiated"}
    
    except Exception as e:
        # Log the error
        print(f"Error processing webhook: {str(e)}")
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": f"Error processing webhook: {str(e)}"},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ack_agent.main:app", host="0.0.0.0", port=8000, reload=True)
