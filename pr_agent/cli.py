#!/usr/bin/env python3
"""
Command-line interface for PR Agent.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

from pr_agent.core.reviewer import PRReviewer
from pr_agent.github.client import GitHubClient
from pr_agent.models.openai_model import OpenAIModel

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pr_agent")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PR Agent - AI-powered code review assistant for GitHub Pull Requests"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review a pull request")
    review_parser.add_argument(
        "--repo", required=True, help="Repository in the format 'owner/repo'"
    )
    review_parser.add_argument(
        "--pr", required=True, type=int, help="Pull request number"
    )
    review_parser.add_argument(
        "--comment", action="store_true", help="Post review as comments on the PR"
    )
    review_parser.add_argument(
        "--output", help="Output file for review results (JSON format)"
    )
    review_parser.add_argument(
        "--model", help="Model to use for review (default: from environment)"
    )
    review_parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to review"
    )
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup PR Agent configuration")
    setup_parser.add_argument(
        "--github-token", help="GitHub API token"
    )
    setup_parser.add_argument(
        "--openai-key", help="OpenAI API key"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args(args)


async def review_pr(args: argparse.Namespace) -> int:
    """Review a pull request."""
    logger.info(f"Reviewing PR #{args.pr} in {args.repo}")
    
    # Initialize components
    github_client = GitHubClient()
    
    model = OpenAIModel(
        model_name=args.model or os.getenv("MODEL_NAME", "gpt-4-turbo")
    )
    
    reviewer = PRReviewer(
        github_client=github_client,
        model=model,
        max_files=args.max_files
    )
    
    # Perform review
    try:
        review_result = await reviewer.review_pr(
            repo_name=args.repo,
            pr_number=args.pr,
            post_comments=args.comment
        )
        
        # Print summary to console
        print("\n" + "=" * 80)
        print(f"PR Review Summary for {args.repo}#{args.pr}")
        print("=" * 80)
        print(review_result["summary"])
        print("\n" + "=" * 80)
        
        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(review_result, f, indent=2)
            logger.info(f"Review results saved to {args.output}")
        
        return 0
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


def setup_config(args: argparse.Namespace) -> int:
    """Setup PR Agent configuration."""
    logger.info("Setting up PR Agent configuration")
    
    # Create .env file if it doesn't exist
    env_file = ".env"
    env_vars = {}
    
    # Load existing .env if it exists
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    
    # Update with new values
    if args.github_token:
        env_vars["GITHUB_TOKEN"] = args.github_token
    
    if args.openai_key:
        env_vars["OPENAI_API_KEY"] = args.openai_key
    
    # Write back to .env
    with open(env_file, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("Configuration updated successfully.")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parsed_args = parse_args(args)
    
    if parsed_args.command == "review":
        return asyncio.run(review_pr(parsed_args))
    elif parsed_args.command == "setup":
        return setup_config(parsed_args)
    elif parsed_args.command == "version":
        from pr_agent import __version__
        print(f"PR Agent version {__version__}")
        return 0
    else:
        parse_args(["--help"])
        return 1


if __name__ == "__main__":
    sys.exit(main()) 