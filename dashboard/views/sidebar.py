"""Sidebar: bank connection, time range, and which integrations are live."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import streamlit as st

from app.config import Settings
from app.db import session_scope
from app.services.plaid_link import link_sandbox_bank, linked_institutions, plaid_ready, unlink_all
from dashboard.state import refresh_data

log = logging.getLogger(__name__)
TIME_RANGES = [7, 30, 90]


@dataclass(frozen=True)
class SidebarChoice:
    days: int
    linked_banks: list[str]


def _status(ok: bool, label: str, value: str) -> str:
    dot = "🟢" if ok else "⚪"
    return f"{dot} {label}: {value}"


def render(user_id: str, settings: Settings) -> SidebarChoice:
    with st.sidebar:
        st.subheader("Bank connection")
        plaid_ok, plaid_reason = plaid_ready()
        with session_scope() as db:
            linked = linked_institutions(db, user_id) if plaid_ok else []

        if linked:
            st.success("Connected to " + ", ".join(linked))
            if st.button("Disconnect bank", width="stretch"):
                with session_scope() as db:
                    unlink_all(db, user_id)
                refresh_data()
                st.rerun()
        elif plaid_ok:
            st.caption("Plaid Sandbox is ready. Connect a test bank to replace the sample data.")
            if st.button("Connect sandbox bank", type="primary", width="stretch"):
                with st.spinner("Connecting to First Platypus Bank (Sandbox)…"):
                    try:
                        with session_scope() as db:
                            link_sandbox_bank(db, user_id)
                    except Exception as e:
                        log.exception("Sandbox link failed")
                        st.error(f"Couldn't connect the sandbox bank: {e}")
                    else:
                        refresh_data()
                        st.toast("Bank connected")
                        st.rerun()
        else:
            st.caption(f"Showing sample data. {plaid_reason}")

        st.divider()
        days = st.selectbox("Time range", TIME_RANGES, index=1, format_func=lambda d: f"Last {d} days")
        if st.button("Refresh data", width="stretch"):
            refresh_data()
            st.rerun()

        st.divider()
        ai = settings.ai_provider
        st.caption("\n\n".join([
            _status(bool(linked), "Bank data", "Plaid Sandbox" if linked else "sample"),
            _status(bool(settings.finnhub_api_key), "Stock prices", "live" if settings.finnhub_api_key else "sample"),
            _status(bool(ai), "Assistant", ai.title() if ai else "add an API key"),
        ]))
    return SidebarChoice(days=days, linked_banks=linked)
