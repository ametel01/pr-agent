#!/usr/bin/env python3
"""
Script to run the PR Agent webhook server.
"""

import os
import logging
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    """Run the webhook server."""
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting webhook server on port {port}...")
    print(f"Webhook URL: http://localhost:{port}/webhook")
    print("Press Ctrl+C to stop the server")
    
    # Run the server
    uvicorn.run(
        "src.github.webhook:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=False
    )

if __name__ == "__main__":
    main() 