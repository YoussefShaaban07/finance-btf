"""Bank feed tab: the FinTech Club Event 2 kit's Plaid Sandbox flow, inside SpendWise.

Uses event2/bank.py as the kit's team-repo step asks (`accounts, tx, source = bank.load_bank()`), with both
Silver Quest charts turned on. Falls back to the kit's CSV files when there are no Plaid keys.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import theme
from dashboard.context import DashboardContext
from event2 import bank


@st.cache_data(ttl=600, show_spinner="Calling the bank…")
def _load(version: int) -> tuple[pd.DataFrame, pd.DataFrame, str]:  # `version` lets Reload bust the cache
    return bank.load_bank()


def render(_ctx: DashboardContext) -> None:
    ss = st.session_state
    ss.setdefault("bank_feed_version", 0)
    st.caption("Event 2: three Plaid calls in a row. Get a public token, swap it for an access token, then pull "
               "accounts and transactions. The access token stays on the server and never reaches this page.")

    c1, c2 = st.columns([1, 4])
    if c1.button("Reload" if ss.get("bank_feed_on") else "Load bank feed", type="primary", width="stretch"):
        if ss.get("bank_feed_on"):
            ss.bank_feed_version += 1
        else:
            ss.bank_feed_on = True
            st.rerun()  # redraw so the button reads "Reload"
    if not ss.get("bank_feed_on"):
        c2.caption("A new sandbox bank takes up to 30 seconds to fill with transactions.")
        return

    accounts, tx, source = _load(ss.bank_feed_version)
    (st.success if source == "Plaid Sandbox" else st.info)(f"Data source: {source}. All data is fake.")

    st.subheader("Accounts")
    st.dataframe(accounts, hide_index=True, width="stretch",
                 column_config={"name": "Name", "type": "Type",
                                "balance": st.column_config.NumberColumn("Balance", format="dollar")})

    spent = tx[tx["amount"] > 0]
    if not spent.empty:
        left, right = st.columns(2, gap="large")
        with left:  # Silver Quest 1
            st.subheader("Spending by category")
            st.bar_chart(spent.groupby("category")["amount"].sum().sort_values(ascending=False),
                         color=theme.NOTE, horizontal=True, y_label="", x_label="")
        with right:  # Silver Quest 2
            st.subheader("Spending per month")
            st.bar_chart(spent.groupby(spent["date"].astype(str).str[:7])["amount"].sum(),
                         color=theme.NOTE, x_label="", y_label="")

    st.subheader("Transactions")
    st.dataframe(tx, hide_index=True, width="stretch",
                 column_config={"date": "Date", "merchant": "Merchant", "category": "Category",
                                "amount": st.column_config.NumberColumn("Amount", format="dollar")})
    st.caption(f"{len(tx)} transactions. Positive amounts are money out, negative are money in.")
