#!/usr/bin/env python3
"""
Simple script to test GitHub connection.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.github.client import GitHubClient

def test_connection():
    """Test connection to GitHub API."""
    print("Testing GitHub connection...")
    
    # Check if token is set
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token or github_token == "your_github_token_here":
        print("Error: GITHUB_TOKEN not set in .env file")
        return False
    
    try:
        # Initialize client
        client = GitHubClient()
        
        # Test a simple API call - get a public repository
        repo_name = "octocat/Hello-World"  # A public GitHub repository
        repo = client.get_repository(repo_name)
        
        print(f"Successfully connected to GitHub!")
        print(f"Repository: {repo.full_name}")
        print(f"Description: {repo.description}")
        print(f"Stars: {repo.stargazers_count}")
        return True
    except Exception as e:
        print(f"Error connecting to GitHub: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 