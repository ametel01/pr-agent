#!/usr/bin/env python3
"""
Simple script to check if imports work correctly.
"""

try:
    print("Trying to import GitHubClient...")
    from src.github.client import GitHubClient
    print("Successfully imported GitHubClient")
except ImportError as e:
    print(f"Failed to import GitHubClient: {e}")

try:
    print("Trying to import webhook app...")
    from src.github.webhook import app, verify_signature
    print("Successfully imported webhook app")
except ImportError as e:
    print(f"Failed to import webhook app: {e}")

print("Import check completed.") 