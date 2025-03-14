"""
Tests for the webhook handler.
"""

import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from pr_agent.github.webhook import app, verify_signature


class TestWebhook(unittest.TestCase):
    """Test cases for the webhook handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            "GITHUB_WEBHOOK_SECRET": "test-secret",
            "GITHUB_TOKEN": "fake-token",
            "OPENAI_API_KEY": "fake-key"
        })
        self.env_patcher.start()
        
        # Create test client
        self.client = TestClient(app)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
    
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        payload = b'{"test": "data"}'
        secret = "test-secret"
        
        # Create signature
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Verify
        self.assertTrue(verify_signature(payload, signature, secret))
    
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        payload = b'{"test": "data"}'
        secret = "test-secret"
        signature = "sha256=invalid"
        
        # Verify
        self.assertFalse(verify_signature(payload, signature, secret))
    
    def test_verify_signature_missing_prefix(self):
        """Test signature verification with missing prefix."""
        payload = b'{"test": "data"}'
        secret = "test-secret"
        signature = "invalid"
        
        # Verify
        self.assertFalse(verify_signature(payload, signature, secret))
    
    @patch("pr_agent.github.webhook.process_pull_request")
    def test_webhook_ping(self, mock_process_pr):
        """Test webhook ping event."""
        # Create payload
        payload = {"zen": "Test ping"}
        
        # Create signature
        secret = "test-secret"
        payload_bytes = json.dumps(payload).encode()
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Send request
        response = self.client.post(
            "/webhook",
            json=payload,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": signature
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Pong!"})
        mock_process_pr.assert_not_called()
    
    @patch("pr_agent.github.webhook.process_pull_request")
    def test_webhook_pull_request(self, mock_process_pr):
        """Test webhook pull request event."""
        # Create payload
        payload = {
            "action": "opened",
            "repository": {"full_name": "owner/repo"},
            "pull_request": {"number": 123}
        }
        
        # Create signature
        secret = "test-secret"
        payload_bytes = json.dumps(payload).encode()
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Send request
        response = self.client.post(
            "/webhook",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message": "Processing PR #123 in owner/repo",
            "status": "accepted"
        })
        mock_process_pr.assert_called_once()
    
    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature."""
        # Create payload
        payload = {"test": "data"}
        
        # Send request with invalid signature
        response = self.client.post(
            "/webhook",
            json=payload,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": "sha256=invalid"
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid signature"})
    
    def test_webhook_missing_event_type(self):
        """Test webhook with missing event type."""
        # Create payload
        payload = {"test": "data"}
        
        # Create signature
        secret = "test-secret"
        payload_bytes = json.dumps(payload).encode()
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Send request without event type
        response = self.client.post(
            "/webhook",
            json=payload,
            headers={
                "X-Hub-Signature-256": signature
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Missing event type"})


if __name__ == "__main__":
    unittest.main() 