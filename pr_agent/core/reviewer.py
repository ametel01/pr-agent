"""
Core reviewer module for PR Agent.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple, Union

from pr_agent.github.client import GitHubClient
from pr_agent.models.base import BaseModel
from pr_agent.models.openai_model import OpenAIModel

logger = logging.getLogger(__name__)


class PRReviewer:
    """Pull Request reviewer that orchestrates the review process."""
    
    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        model: Optional[BaseModel] = None,
        max_files: int = None,
        comment_prefix: str = None
    ):
        """Initialize the PR reviewer.
        
        Args:
            github_client: GitHub client instance
            model: AI model instance
            max_files: Maximum number of files to review
            comment_prefix: Prefix for review comments
        """
        self.github_client = github_client or GitHubClient()
        self.model = model or OpenAIModel()
        self.max_files = max_files or int(os.getenv("MAX_PR_FILES", "10"))
        self.comment_prefix = comment_prefix or os.getenv("REVIEW_COMMENT_PREFIX", "[PR-Agent]")
        
        logger.debug("PR reviewer initialized")
    
    async def review_pr(
        self, 
        repo_name: str, 
        pr_number: int, 
        post_comments: bool = False
    ) -> Dict:
        """Review a pull request.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            pr_number: Pull request number
            post_comments: Whether to post review comments to GitHub
            
        Returns:
            Dictionary containing review results
        """
        logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
        
        # Get PR details
        pr = self.github_client.get_pull_request(repo_name, pr_number)
        pr_files = self.github_client.get_pr_files(repo_name, pr_number)
        
        # Limit the number of files to review
        if len(pr_files) > self.max_files:
            logger.warning(
                f"PR has {len(pr_files)} files, limiting review to {self.max_files} files"
            )
            pr_files = pr_files[:self.max_files]
        
        # Review each file
        file_reviews = []
        review_comments = []
        
        for file in pr_files:
            logger.info(f"Reviewing file: {file['filename']}")
            
            # Skip binary files, deleted files, etc.
            if file["status"] == "removed" or not file.get("patch"):
                logger.info(f"Skipping file {file['filename']} (status: {file['status']})")
                continue
            
            # Analyze the diff
            review_result = await self.model.analyze_diff(
                diff=file["patch"],
                filename=file["filename"],
                context={"pr": pr.title, "file": file}
            )
            
            file_reviews.append({
                "filename": file["filename"],
                "review": review_result
            })
            
            # Prepare comments for GitHub
            if post_comments and review_result.get("issues"):
                for issue in review_result["issues"]:
                    if "line" in issue and issue["line"]:
                        comment = {
                            "path": file["filename"],
                            "position": self._get_position_from_line(file["patch"], issue["line"]),
                            "body": f"{self.comment_prefix} **{issue['type'].upper()} ({issue['severity']})**\n\n{issue['description']}\n\n**Suggestion:** {issue['suggestion']}"
                        }
                        review_comments.append(comment)
        
        # Generate summary
        summary = await self.model.summarize_review(
            file_reviews=file_reviews,
            pr_description=pr.body
        )
        
        # Post review to GitHub if requested
        if post_comments:
            self._post_review_to_github(repo_name, pr_number, review_comments, summary)
        
        return {
            "pr": {
                "number": pr_number,
                "title": pr.title,
                "url": pr.html_url
            },
            "file_reviews": file_reviews,
            "summary": summary
        }
    
    def _get_position_from_line(self, patch: str, line_ref: Union[str, int]) -> int:
        """Convert a line reference to a position in the diff.
        
        Args:
            patch: The file patch
            line_ref: Line reference (can be a number or range like "10-15")
            
        Returns:
            Position in the diff
        """
        # This is a simplified implementation
        # In a real implementation, you would need to parse the patch and map line numbers
        # to positions in the diff
        try:
            if isinstance(line_ref, str) and "-" in line_ref:
                line_num = int(line_ref.split("-")[0])
            else:
                line_num = int(line_ref)
                
            # Count lines in the patch until we find the right position
            lines = patch.split("\n")
            current_line = 0
            for i, line in enumerate(lines):
                if line.startswith("+") and not line.startswith("+++"):
                    current_line += 1
                    if current_line >= line_num:
                        return i + 1
            
            # If we can't find the exact position, return the end of the patch
            return len(lines)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse line reference: {line_ref}")
            return 1  # Default to first line
    
    def _post_review_to_github(
        self, 
        repo_name: str, 
        pr_number: int, 
        comments: List[Dict], 
        summary: str
    ) -> bool:
        """Post a review to GitHub.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            pr_number: Pull request number
            comments: List of comment objects
            summary: Review summary
            
        Returns:
            True if review was posted successfully
        """
        if comments:
            logger.info(f"Posting review with {len(comments)} comments to PR #{pr_number}")
            return self.github_client.add_pr_review(
                repo_name=repo_name,
                pr_number=pr_number,
                comments=comments,
                body=f"{self.comment_prefix} Review Summary\n\n{summary}"
            )
        else:
            logger.info(f"Posting review summary to PR #{pr_number}")
            return self.github_client.add_pr_comment(
                repo_name=repo_name,
                pr_number=pr_number,
                comment=f"{self.comment_prefix} Review Summary\n\n{summary}"
            ) 