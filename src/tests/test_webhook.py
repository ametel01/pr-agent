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

from src.github.webhook import app, verify_signature


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
        
        # Ensure the environment variables are applied
        os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
        
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
    
    @patch("src.github.webhook.process_pull_request")
    def test_webhook_ping(self, mock_process_pr):
        """Test webhook ping event."""
        # Create payload
        payload = {"zen": "Test ping"}
        
        # Convert payload to JSON string and then to bytes
        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode()
        
        # Create signature
        secret = "test-secret"
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Send request with raw content
        response = self.client.post(
            "/webhook",
            content=payload_bytes,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Pong!"})
        mock_process_pr.assert_not_called()
    
    @patch("src.github.webhook.process_pull_request")
    def test_webhook_pull_request(self, mock_process_pr):
        """Test webhook pull request event."""
        # Create payload
        payload = {
            "action": "opened",
            "repository": {"full_name": "owner/repo"},
            "pull_request": {"number": 123}
        }
        
        # Convert payload to JSON string and then to bytes
        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode()
        
        # Create signature
        secret = "test-secret"
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Send request with raw content
        response = self.client.post(
            "/webhook",
            content=payload_bytes,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
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
        
        # Convert payload to JSON string and then to bytes
        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode()
        
        # Send request with invalid signature
        response = self.client.post(
            "/webhook",
            content=payload_bytes,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json"
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid signature"})
    
    def test_webhook_missing_event_type(self):
        """Test webhook with missing event type."""
        # Create payload
        payload = {"test": "data"}
        
        # Convert payload to JSON string and then to bytes
        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode()
        
        # Create signature
        secret = "test-secret"
        hmac_obj = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        )
        signature = f"sha256={hmac_obj.hexdigest()}"
        
        # Send request without event type
        response = self.client.post(
            "/webhook",
            content=payload_bytes,
            headers={
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        
        # Verify
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Missing event type"})


if __name__ == "__main__":
    unittest.main() 