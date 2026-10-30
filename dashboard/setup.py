"""Load keys (from .streamlit/secrets.toml or env vars) BEFORE the backend reads its settings.

Ground rule: no secrets in code. Keys live in .streamlit/secrets.toml (gitignored) locally,
or in GitHub Codespaces secrets, which show up as environment variables.
"""
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
KEYS = ["PLAID_CLIENT_ID", "PLAID_SECRET", "PLAID_ENV", "FINNHUB_API_KEY", "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL", "TOKEN_ENCRYPTION_KEY", "DATABASE_URL"]


def load_secrets() -> None:
    import streamlit as st

    try:
        for k in KEYS:
            if k in st.secrets and st.secrets[k] and not os.environ.get(k):
                os.environ[k] = str(st.secrets[k])
    except Exception:  # no secrets file is fine: the app runs on sample data
        log.debug("No .streamlit/secrets.toml found; using environment variables only")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'finance.db'}")
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
