"""Fetch everything once, cache it, and expose it through the same provider interface the AI tools use."""
from datetime import date, timedelta

import streamlit as st

from app.db import SessionLocal
from app.providers import get_provider
from app.providers.base import FinanceProvider
from app.schemas import Account, CreditCard, Holding, Transaction

HISTORY_DAYS = 90


class Snapshot(FinanceProvider):
    """Cached data dressed up as a provider, so the chatbot reads the same numbers the screen shows."""

    def __init__(self, data: dict):
        self.is_demo = data["is_demo"]
        self._d = data

    def get_accounts(self) -> list[Account]:
        return self._d["accounts"]

    def get_credit_cards(self) -> list[CreditCard]:
        return self._d["cards"]

    def get_holdings(self) -> list[Holding]:
        return self._d["holdings"]

    def get_transactions(self, days: int = 30) -> list[Transaction]:
        cutoff = date.today() - timedelta(days=days)
        return [t for t in self._d["txns"] if t.date >= cutoff]


@st.cache_data(ttl=300, show_spinner="Loading your accounts…")
def load(user_id: str, version: int) -> dict:  # `version` busts the cache after connect/refresh
    db = SessionLocal()
    try:
        p = get_provider(db, user_id)
    finally:
        db.close()
    out = {"is_demo": p.is_demo, "errors": []}
    for key, fn in [("accounts", p.get_accounts), ("cards", p.get_credit_cards),
                    ("holdings", p.get_holdings), ("txns", lambda: p.get_transactions(HISTORY_DAYS))]:
        try:
            out[key] = fn()
        except Exception as e:  # noqa: BLE001 — show what failed instead of crashing the whole page
            out[key] = []
            out["errors"].append(f"{key}: {type(e).__name__}: {str(e)[:200]}")
    return out
