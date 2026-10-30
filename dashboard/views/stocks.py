"""Stocks tab: portfolio holdings and a watchlist."""
from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from app.services.market import get_quote
from dashboard.context import DashboardContext
from dashboard.format import money

log = logging.getLogger(__name__)
MAX_WATCHLIST = 12


def render(ctx: DashboardContext) -> None:
    if ctx.holdings:
        value = sum(h.value for h in ctx.holdings)
        cost = sum(h.cost_basis or h.value for h in ctx.holdings)
        st.metric("Portfolio value", money(value), delta=f"{money(value - cost)} all time")
        st.dataframe(
            pd.DataFrame([{"Ticker": h.ticker, "Name": h.name, "Shares": h.quantity, "Price": h.price,
                           "Value": h.value, "Gain": h.value - (h.cost_basis or h.value)} for h in ctx.holdings]),
            hide_index=True, width="stretch",
            column_config={k: st.column_config.NumberColumn(format="dollar") for k in ("Price", "Value", "Gain")},
        )
    else:
        st.info("No investment accounts on this connection.")

    st.subheader("Watchlist")
    raw = st.text_input("Tickers, separated by commas", "SPY, QQQ, AAPL, NVDA")
    symbols = list(dict.fromkeys(s.strip().upper() for s in raw.split(",") if s.strip()))[:MAX_WATCHLIST]
    cols = st.columns(4)
    for i, sym in enumerate(symbols):
        try:
            q = get_quote(sym)
            cols[i % 4].metric(q.symbol, money(q.price), f"{q.change_pct:+.2f}%")
        except Exception:
            log.warning("Quote lookup failed for %s", sym, exc_info=True)
            cols[i % 4].metric(sym, "Not found")
    if not ctx.settings.finnhub_api_key:
        st.caption("Sample prices. Add FINNHUB_API_KEY for live quotes.")
