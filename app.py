"""SpendWise: AI-powered personal finance dashboard.

Run:  streamlit run app.py
Works with zero keys (sample data). Add keys in .streamlit/secrets.toml to connect a Plaid sandbox bank, live
stock prices, and the AI assistant. See README.md.

This file only wires things together. Data loading is in dashboard/data.py, derived numbers in
dashboard/context.py, and each tab is a module in dashboard/views/.
"""
import logging

import streamlit as st

from dashboard.setup import load_secrets

load_secrets()  # must run before importing the backend, which reads keys on import

from app.config import get_settings  # noqa: E402
from app.db import init_db  # noqa: E402
from dashboard import state, theme  # noqa: E402
from dashboard.context import DashboardContext  # noqa: E402
from dashboard.data import Snapshot, load  # noqa: E402
from dashboard.format import money  # noqa: E402
from dashboard.views import assistant, bank_feed, goals, overview, sidebar, stocks  # noqa: E402
from dashboard.views.money_tabs import render_alerts, render_cards, render_subscriptions  # noqa: E402

# TEAM TODO: change this to your team name
TEAM_NAME = "SpendWise"
TAGLINE = "All your accounts in one place, and an assistant that answers from your real numbers."

# TODO(auth): one shared demo user for now. Add real login before any real person uses this.
USER_ID = "demo-user"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
st.set_page_config(page_title=TEAM_NAME, page_icon="💸", layout="wide")
theme.inject_css()
init_db()
state.init()
settings = get_settings()

choice = sidebar.render(USER_ID, settings)
data = load(USER_ID, state.data_version())
ctx = DashboardContext(user_id=USER_ID, days=choice.days, settings=settings, snapshot=Snapshot(data),
                       errors=data["errors"], linked_banks=choice.linked_banks)

for err in ctx.errors:
    st.warning(f"Some data didn't load ({err}). Sandbox data can take a minute after connecting; "
               "use Refresh data in the sidebar.")

# ----------------------------------------------------------------------------------------- header
flow = ctx.spend["net"]
liquid = [a for a in ctx.accounts if a.type not in theme.LIABILITY_TYPES]
theme.hero(
    TEAM_NAME, TAGLINE, money(ctx.net_worth.net_worth),
    source=("Plaid Sandbox data" if not ctx.is_demo else "Sample data") + ". Educational only, not financial advice.",
    rows=[
        theme.LedgerRow("Assets", money(ctx.net_worth.assets), theme.PLAIN, f"{len(liquid)} accounts"),
        theme.LedgerRow("Debts", money(-ctx.net_worth.liabilities), theme.BAD, "cards and loans"),
        theme.LedgerRow(f"Spent, last {choice.days} days", money(ctx.spend["spent"]), theme.PLAIN,
                        f"income {money(ctx.spend['income'])}"),
        theme.LedgerRow(f"Cash flow, last {choice.days} days", money(flow), theme.GOOD if flow >= 0 else theme.BAD,
                        "saving" if flow >= 0 else "spending more than you earn"),
    ],
)

# ----------------------------------------------------------------------------------------- tabs
alerts_label = f"Alerts ({len(ctx.alerts)})" if ctx.alerts else "Alerts"
tabs = st.tabs(["Overview", alerts_label, "Cards", "Subscriptions", "Goals", "Stocks", "Bank feed", "Ask AI"])
views = [overview.render, render_alerts, render_cards, render_subscriptions, goals.render, stocks.render,
         bank_feed.render, assistant.render]
for tab, view in zip(tabs, views, strict=True):
    with tab:
        view(ctx)
