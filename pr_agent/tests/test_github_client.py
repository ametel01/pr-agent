"""
Tests for the GitHub client.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from github import Github, GithubException

from pr_agent.github.client import GitHubClient


class TestGitHubClient(unittest.TestCase):
    """Test cases for the GitHub client."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"})
        self.env_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
    
    @patch("pr_agent.github.client.Github")
    def test_init_with_token(self, mock_github):
        """Test initialization with token."""
        client = GitHubClient(token="test-token")
        self.assertEqual(client.token, "test-token")
        mock_github.assert_called_once_with("test-token")
    
    @patch("pr_agent.github.client.Github")
    def test_init_with_env_token(self, mock_github):
        """Test initialization with token from environment."""
        client = GitHubClient()
        self.assertEqual(client.token, "fake-token")
        mock_github.assert_called_once_with("fake-token")
    
    @patch("pr_agent.github.client.Github")
    def test_init_no_token(self, mock_github):
        """Test initialization with no token."""
        self.env_patcher.stop()
        with self.assertRaises(ValueError):
            GitHubClient()
        mock_github.assert_not_called()
        self.env_patcher.start()
    
    @patch("pr_agent.github.client.Github")
    def test_get_repository(self, mock_github):
        """Test getting a repository."""
        # Setup
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Execute
        client = GitHubClient()
        repo = client.get_repository("owner/repo")
        
        # Verify
        self.assertEqual(repo, mock_repo)
        mock_github.return_value.get_repo.assert_called_once_with("owner/repo")
    
    @patch("pr_agent.github.client.Github")
    def test_get_repository_error(self, mock_github):
        """Test getting a repository with error."""
        # Setup
        mock_github.return_value.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}
        )
        
        # Execute and verify
        client = GitHubClient()
        with self.assertRaises(ValueError):
            client.get_repository("owner/repo")
    
    @patch("pr_agent.github.client.Github")
    def test_get_pull_request(self, mock_github):
        """Test getting a pull request."""
        # Setup
        mock_pr = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Execute
        client = GitHubClient()
        pr = client.get_pull_request("owner/repo", 123)
        
        # Verify
        self.assertEqual(pr, mock_pr)
        mock_github.return_value.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_pull.assert_called_once_with(123)
    
    @patch("pr_agent.github.client.Github")
    def test_get_pr_files(self, mock_github):
        """Test getting files from a pull request."""
        # Setup
        mock_file = MagicMock()
        mock_file.filename = "test.py"
        mock_file.status = "modified"
        mock_file.patch = "@@ -1,3 +1,4 @@\n line1\n+line2\n line3\n line4"
        mock_file.additions = 1
        mock_file.deletions = 0
        mock_file.changes = 1
        mock_file.blob_url = "https://github.com/owner/repo/blob/abc123/test.py"
        mock_file.raw_url = "https://github.com/owner/repo/raw/abc123/test.py"
        mock_file.contents_url = "https://api.github.com/repos/owner/repo/contents/test.py?ref=abc123"
        
        mock_pr = MagicMock()
        mock_pr.get_files.return_value = [mock_file]
        
        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Execute
        client = GitHubClient()
        files = client.get_pr_files("owner/repo", 123)
        
        # Verify
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["filename"], "test.py")
        self.assertEqual(files[0]["status"], "modified")
        self.assertEqual(files[0]["patch"], "@@ -1,3 +1,4 @@\n line1\n+line2\n line3\n line4")
        self.assertEqual(files[0]["additions"], 1)
        self.assertEqual(files[0]["deletions"], 0)
        self.assertEqual(files[0]["changes"], 1)
        self.assertEqual(files[0]["blob_url"], "https://github.com/owner/repo/blob/abc123/test.py")
        self.assertEqual(files[0]["raw_url"], "https://github.com/owner/repo/raw/abc123/test.py")
        self.assertEqual(files[0]["contents_url"], "https://api.github.com/repos/owner/repo/contents/test.py?ref=abc123")


if __name__ == "__main__":
    unittest.main() 