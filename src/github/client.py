"""
GitHub client for PR Agent.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Union

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.
        
        Args:
            token: GitHub API token. If not provided, will use GITHUB_TOKEN from environment.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN not set in environment")
        
        self.client = Github(self.token)
        logger.debug("GitHub client initialized")
    
    def get_repository(self, repo_name: str) -> Repository:
        """Get a repository by name.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            
        Returns:
            Repository object
            
        Raises:
            ValueError: If repository not found
        """
        try:
            return self.client.get_repo(repo_name)
        except GithubException as e:
            logger.error(f"Failed to get repository {repo_name}: {e}")
            raise ValueError(f"Repository {repo_name} not found or access denied") from e
    
    def get_pull_request(self, repo_name: str, pr_number: int) -> PullRequest:
        """Get a pull request by number.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            PullRequest object
            
        Raises:
            ValueError: If pull request not found
        """
        repo = self.get_repository(repo_name)
        try:
            return repo.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Failed to get PR #{pr_number} in {repo_name}: {e}")
            raise ValueError(f"Pull request #{pr_number} not found in {repo_name}") from e
    
    def get_pr_files(self, repo_name: str, pr_number: int) -> List[Dict[str, str]]:
        """Get files changed in a pull request.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            List of file objects with filename, status, and patch
        """
        pr = self.get_pull_request(repo_name, pr_number)
        files = []
        
        for file in pr.get_files():
            files.append({
                "filename": file.filename,
                "status": file.status,
                "patch": file.patch,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "blob_url": file.blob_url,
                "raw_url": file.raw_url,
                "contents_url": file.contents_url,
            })
        
        return files
    
    def add_pr_comment(self, repo_name: str, pr_number: int, comment: str) -> bool:
        """Add a comment to a pull request.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            pr_number: Pull request number
            comment: Comment text
            
        Returns:
            True if comment was added successfully
        """
        pr = self.get_pull_request(repo_name, pr_number)
        try:
            pr.create_issue_comment(comment)
            return True
        except GithubException as e:
            logger.error(f"Failed to add comment to PR #{pr_number} in {repo_name}: {e}")
            return False
    
    def add_pr_review(
        self, 
        repo_name: str, 
        pr_number: int, 
        comments: List[Dict[str, Union[str, int]]], 
        body: Optional[str] = None
    ) -> bool:
        """Add a review to a pull request with inline comments.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            pr_number: Pull request number
            comments: List of comment objects with path, position, and body
            body: Overall review body text
            
        Returns:
            True if review was added successfully
        """
        pr = self.get_pull_request(repo_name, pr_number)
        try:
            pr.create_review(body=body or "", comments=comments)
            return True
        except GithubException as e:
            logger.error(f"Failed to add review to PR #{pr_number} in {repo_name}: {e}")
            return False 