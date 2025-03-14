"""
GitHub webhook handler for PR Agent.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from pr_agent.core.reviewer import PRReviewer
from pr_agent.github.client import GitHubClient

logger = logging.getLogger(__name__)

app = FastAPI(title="PR Agent Webhook Handler")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook signature.
    
    Args:
        payload: Request payload
        signature: GitHub signature header
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False
    
    signature = signature.replace("sha256=", "")
    
    # Create hmac signature
    hmac_obj = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    )
    digest = hmac_obj.hexdigest()
    
    return hmac.compare_digest(digest, signature)


async def process_pull_request(
    repo_name: str,
    pr_number: int,
    action: str,
    post_comments: bool = True
) -> None:
    """Process a pull request event.
    
    Args:
        repo_name: Repository name in the format "owner/repo"
        pr_number: Pull request number
        action: Pull request action (opened, synchronize, etc.)
        post_comments: Whether to post comments to the PR
    """
    logger.info(f"Processing PR #{pr_number} in {repo_name} (action: {action})")
    
    # Only process certain actions
    if action not in ["opened", "synchronize", "reopened"]:
        logger.info(f"Ignoring PR action: {action}")
        return
    
    # Initialize components
    github_client = GitHubClient()
    reviewer = PRReviewer(github_client=github_client)
    
    try:
        # Review the PR
        await reviewer.review_pr(
            repo_name=repo_name,
            pr_number=pr_number,
            post_comments=post_comments
        )
        logger.info(f"Successfully reviewed PR #{pr_number} in {repo_name}")
    except Exception as e:
        logger.error(f"Error reviewing PR #{pr_number} in {repo_name}: {e}", exc_info=True)


@app.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle GitHub webhook events.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        
    Returns:
        Response message
    """
    # Get webhook secret
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    # Get request body
    payload = await request.body()
    
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(payload, signature, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event
    event_type = request.headers.get("X-GitHub-Event")
    if not event_type:
        raise HTTPException(status_code=400, detail="Missing event type")
    
    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Process event
    if event_type == "ping":
        return {"message": "Pong!"}
    elif event_type == "pull_request":
        # Extract PR details
        repo_name = data.get("repository", {}).get("full_name")
        pr_number = data.get("pull_request", {}).get("number")
        action = data.get("action")
        
        if not repo_name or not pr_number or not action:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Process PR in background
        background_tasks.add_task(
            process_pull_request,
            repo_name=repo_name,
            pr_number=pr_number,
            action=action
        )
        
        return {
            "message": f"Processing PR #{pr_number} in {repo_name}",
            "status": "accepted"
        }
    else:
        logger.info(f"Ignoring event type: {event_type}")
        return {"message": f"Event type {event_type} not supported"}


def start_webhook_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "info"
) -> None:
    """Start the webhook server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        log_level: Logging level
    """
    import uvicorn
    
    uvicorn.run(
        "pr_agent.github.webhook:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    ) 