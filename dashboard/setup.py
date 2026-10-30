"""Load keys BEFORE the backend reads its settings.

Ground rule: no secrets in code. Keys can come from any of these (first one wins):
  1. environment variables (GitHub Codespaces secrets show up this way)
  2. .streamlit/secrets.toml
  3. .env in the project folder (the FinTech Club Event 2 kit's format)
Both files are gitignored.
"""
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
KEYS = ["PLAID_CLIENT_ID", "PLAID_SECRET", "PLAID_ENV", "FINNHUB_API_KEY", "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL", "TOKEN_ENCRYPTION_KEY", "DATABASE_URL"]


def _load_streamlit_secrets() -> None:
    import streamlit as st

    try:
        for k in KEYS:
            if k in st.secrets and st.secrets[k] and not os.environ.get(k):
                os.environ[k] = str(st.secrets[k])
    except Exception:  # no secrets file is fine: the app runs on sample data
        log.debug("No .streamlit/secrets.toml found")


def _load_dotenv() -> None:
    try:
        from dotenv import dotenv_values
    except ImportError:
        return
    # Fill in anything still missing OR EMPTY. Streamlit copies every root-level secrets.toml entry into the
    # environment, including the template's blank `PLAID_SECRET = ""` lines, and a plain load_dotenv() would
    # treat those blanks as "already set" and silently ignore the real keys in .env.
    for key, value in dotenv_values(ROOT / ".env", encoding="utf-8-sig").items():  # -sig: tolerate a Notepad BOM
        if value and not os.environ.get(key):
            os.environ[key] = value


def load_secrets() -> None:
    _load_streamlit_secrets()
    _load_dotenv()
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'finance.db'}")
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
