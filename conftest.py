"""Test setup shared by every test file. Runs before any app module is imported, so settings see these values.

Tests always use a throwaway SQLite file and never real API keys, even if your shell or secrets file has them.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
for key in ("PLAID_CLIENT_ID", "PLAID_SECRET", "FINNHUB_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
    os.environ[key] = ""
