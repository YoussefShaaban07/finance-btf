"""Finance BFF: AI-powered personal finance dashboard.

Run:  streamlit run app.py
Works with zero keys (demo data). Add keys in .streamlit/secrets.toml to connect a Plaid
sandbox bank, live stock prices, and the AI assistant. See README.md.
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from dashboard.setup import load_secrets

load_secrets()  # must run before importing the backend, which reads keys on import

from app.ai.chat import MAX_MESSAGE_CHARS, chat  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.schemas import ChatMessage  # noqa: E402
from app.services import goals as goals_svc  # noqa: E402
from app.services.alerts import card_alerts, unusual_charges  # noqa: E402
from app.services.finance import compute_net_worth, spending_summary  # noqa: E402
from app.services.market import get_quote  # noqa: E402
from app.services.plaid_link import link_sandbox_bank, linked_institutions, plaid_ready, unlink_all  # noqa: E402
from app.services.subscriptions import find_subscriptions  # noqa: E402
from dashboard import theme  # noqa: E402
from dashboard.data import Snapshot, load  # noqa: E402

# TEAM TODO: change this to your team name
TEAM_NAME = "Finance BFF"
TAGLINE = "Your whole financial life in one place, plus an AI you can ask."

# TODO(auth): one shared demo user for now. Add real login before any real person uses this.
USER_ID = "demo-user"

st.set_page_config(page_title=TEAM_NAME, page_icon="💸", layout="wide")
theme.inject_css()
init_db()
settings = get_settings()
ss = st.session_state
ss.setdefault("data_version", 0)
ss.setdefault("chat", [])


def money(x: float) -> str:
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def pretty(cat: str) -> str:
    return cat.replace("_", " ").title().replace(" And ", " & ")


def refresh():
    ss.data_version += 1


# ======================= SIDEBAR: bank connection & settings =======================
with st.sidebar:
    st.header("🏦 Bank connection")
    plaid_ok, plaid_reason = plaid_ready()
    db = SessionLocal()
    try:
        linked = linked_institutions(db, USER_ID) if plaid_ok else []
    finally:
        db.close()

    if linked:
        st.success("Connected: " + ", ".join(linked))
        if st.button("Disconnect bank", width="stretch"):
            db = SessionLocal()
            try:
                unlink_all(db, USER_ID)
            finally:
                db.close()
            refresh()
            st.rerun()
    elif plaid_ok:
        st.info("Plaid Sandbox is ready. Connect a fake bank to replace the demo data.")
        if st.button("Connect sandbox bank", type="primary", width="stretch"):
            with st.spinner("Connecting to First Platypus Bank (Sandbox)…"):
                db = SessionLocal()
                try:
                    link_sandbox_bank(db, USER_ID)
                    refresh()
                    st.toast("Bank connected! 🎉")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Couldn't connect: {e}")
                finally:
                    db.close()
    else:
        st.warning(f"Demo mode: showing sample data.\n\n{plaid_reason}")

    st.divider()
    st.header("⚙️ Settings")
    days = st.selectbox("Time range", [7, 30, 90], index=1, format_func=lambda d: f"Last {d} days")
    if st.button("🔄 Refresh data", width="stretch"):
        refresh()
        st.rerun()

    st.divider()
    st.caption("Status")
    st.caption(f"{'🟢' if linked else '🟡'} Bank data: {'Plaid Sandbox' if linked else 'demo'}")
    st.caption(f"{'🟢' if settings.finnhub_api_key else '🟡'} Stock prices: {'live' if settings.finnhub_api_key else 'demo'}")
    ai = settings.ai_provider
    st.caption(f"{'🟢' if ai else '🔴'} AI assistant: {ai.title() if ai else 'needs key'}")

# ======================= DATA =======================
data = load(USER_ID, ss.data_version)
snap = Snapshot(data)
for err in data["errors"]:
    st.warning(f"Some data didn't load ({err}). Sandbox data can take a minute after connecting. Hit Refresh.")

accounts, cards, holdings = snap.get_accounts(), snap.get_credit_cards(), snap.get_holdings()
txns = snap.get_transactions(days)
txns90 = snap.get_transactions(90)
nw = compute_net_worth(accounts)
spend = spending_summary(txns)
monthly_net = spending_summary(txns90)["net"] / 3
alerts = unusual_charges(snap.get_transactions(30)) + card_alerts(cards)
subs = find_subscriptions(txns90)
savings_balance = sum(a.balance for a in accounts if a.type == "depository" and (a.subtype or "") == "savings") \
    or sum(a.balance for a in accounts if a.type == "depository")


def goal_progress() -> list:
    db = SessionLocal()
    try:
        return [goals_svc.progress(g, savings_balance, monthly_net) for g in goals_svc.list_goals(db, USER_ID)]
    finally:
        db.close()


# ======================= HEADER =======================
theme.hero(TEAM_NAME, TAGLINE, money(nw.net_worth),
           f"{'🏦 Sandbox bank data' if not snap.is_demo else '✨ Demo data'} · educational only, not financial advice")
saving = spend["net"] >= 0
theme.stat_cards([
    ("💰", "Assets", money(nw.assets), f"{len([a for a in accounts if a.type not in ('credit', 'loan')])} accounts", theme.GREEN),
    ("🧾", "Debts", money(nw.liabilities), "cards + loans", theme.ORANGE),
    ("🛍️", f"Spent · {days}d", money(spend["spent"]), f"income {money(spend['income'])}", theme.PINK),
    ("📈" if saving else "📉", f"Cash flow · {days}d", money(spend["net"]),
     "saving 🎉" if saving else "overspending", theme.CYAN if saving else theme.RED),
    ("🔔", "Alerts", str(len(alerts)), "need a look" if alerts else "all clear", theme.AMBER if alerts else theme.GREEN),
])

tabs = st.tabs(["📊 Overview", f"🔔 Alerts ({len(alerts)})", "💳 Cards", "🔁 Subscriptions",
                "🎯 Goals", "📈 Stocks", "🤖 Ask AI"])

# ======================= OVERVIEW =======================
with tabs[0]:
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Where your money went")
        if spend["by_category"]:
            theme.category_chart(spend["by_category"], pretty)
        else:
            st.info("No spending in this range yet.")

        st.subheader("Daily spending")
        if txns:
            daily = (pd.DataFrame([{"Date": t.date, "Spent": t.amount} for t in txns
                                   if t.amount > 0 and t.category not in ("TRANSFER_OUT", "LOAN_PAYMENTS")])
                     .groupby("Date").sum())
            if not daily.empty:
                theme.daily_chart(daily)

    with right:
        st.subheader("Accounts")
        theme.account_list(accounts, money)
        if alerts:
            st.subheader("Heads up")
            theme.alert_cards(alerts[:3])

    st.subheader("Transactions")
    f1, f2 = st.columns([2, 1])
    search = f1.text_input("Search merchant", placeholder="e.g. Amazon")
    cats = sorted({t.category for t in txns})
    picked = f2.multiselect("Category", cats, format_func=pretty)
    shown = [t for t in txns if (not search or search.lower() in t.name.lower()) and (not picked or t.category in picked)]
    st.dataframe(
        pd.DataFrame([{"Date": t.date, "Merchant": t.name, "Category": pretty(t.category), "Amount": -t.amount}
                      for t in shown]),
        hide_index=True, width="stretch",
        column_config={"Amount": st.column_config.NumberColumn(format="dollar")},
    )
    st.caption(f"{len(shown)} transactions · negative = money out")

# ======================= ALERTS =======================
with tabs[1]:
    theme.alert_cards(alerts)
    st.caption("Unusual = at least 2× what you normally spend at that merchant or category. "
               "Cards: payment due within 7 days, or utilization at or above 30%.")

# ======================= CARDS =======================
with tabs[2]:
    if not cards:
        st.info("No credit cards found.")
    else:
        total_bal = sum(c.balance for c in cards)
        total_lim = sum(c.limit or 0 for c in cards)
        overall = total_bal / total_lim * 100 if total_lim else 0
        theme.stat_cards([
            ("💳", "Total card balance", money(total_bal), f"of {money(total_lim)} total limit", theme.PINK),
            ("📊", "Overall utilization", f"{overall:.1f}%",
             "great 🟢" if overall < 10 else "okay, keep it under 30% 🟡" if overall < 30 else "high 🔴",
             theme.GREEN if overall < 10 else theme.AMBER if overall < 30 else theme.RED),
        ])
        card_cols = st.columns(min(len(cards), 3))
        for i, c in enumerate(cards):
            with card_cols[i % len(card_cols)]:
                theme.credit_card(c, i, money)
        st.caption("Under 30% utilization helps your credit score; under 10% is great.")

# ======================= SUBSCRIPTIONS =======================
with tabs[3]:
    if not subs:
        st.info("No recurring charges found in the last 90 days.")
    else:
        theme.stat_cards([
            ("🔁", "Recurring per month", money(sum(s.amount for s in subs)), f"{len(subs)} charges", theme.VIOLET),
            ("📆", "Per year", money(sum(s.yearly_cost for s in subs)), "if nothing changes", theme.PINK),
        ])
        theme.subscription_cards(subs, money, pretty)
        st.caption("Found automatically: same merchant, same price, about a month apart.")

# ======================= GOALS =======================
with tabs[4]:
    st.caption(f"Progress is measured against your savings balance ({money(savings_balance)}).")
    for g in goal_progress():
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{g.name}**: {money(g.saved)} of {money(g.target)} by {g.target_date:%b %Y}")
            c1.progress(g.pct / 100, text=f"{g.pct:.0f}%")
            c1.caption(g.on_track_note)
            if c2.button("Delete", key=f"del_{g.id}"):
                db = SessionLocal()
                try:
                    goals_svc.delete_goal(db, USER_ID, g.id)
                finally:
                    db.close()
                st.rerun()
    with st.form("new_goal", clear_on_submit=True):
        st.markdown("**New goal**")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name", placeholder="Emergency fund")
        target = c2.number_input("Target ($)", min_value=1.0, value=10000.0, step=100.0)
        when = c3.date_input("By", value=date.today() + timedelta(days=180), min_value=date.today())
        if st.form_submit_button("Add goal", type="primary"):
            db = SessionLocal()
            try:
                goals_svc.add_goal(db, USER_ID, name, target, when)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            finally:
                db.close()

# ======================= STOCKS =======================
with tabs[5]:
    if holdings:
        value = sum(h.value for h in holdings)
        cost = sum(h.cost_basis or h.value for h in holdings)
        st.metric("Portfolio", money(value), delta=f"{money(value - cost)} all-time")
        st.dataframe(
            pd.DataFrame([{"Ticker": h.ticker, "Name": h.name, "Shares": h.quantity, "Price": h.price,
                           "Value": h.value, "Gain": h.value - (h.cost_basis or h.value)} for h in holdings]),
            hide_index=True, width="stretch",
            column_config={k: st.column_config.NumberColumn(format="dollar") for k in ("Price", "Value", "Gain")},
        )
    else:
        st.info("No investment accounts linked.")
    st.subheader("Watchlist")
    symbols = st.text_input("Tickers (comma-separated)", "SPY, QQQ, AAPL, NVDA")
    cols = st.columns(4)
    for i, sym in enumerate([s.strip().upper() for s in symbols.split(",") if s.strip()][:12]):
        try:
            q = get_quote(sym)
            cols[i % 4].metric(q.symbol, money(q.price), f"{q.change_pct:+.2f}%")
        except Exception:  # noqa: BLE001
            cols[i % 4].metric(sym, "n/a")
    if not settings.finnhub_api_key:
        st.caption("Demo prices. Add FINNHUB_API_KEY for live quotes.")

# ======================= ASK AI =======================
with tabs[6]:
    st.caption("Ask about your money. Penny looks up your actual numbers with tools instead of guessing. "
               "She can't move money or make trades.")
    for m in ss.chat:
        st.chat_message(m["role"]).markdown(m["content"])

    starters = ["Where did my money go this month?", "Any unusual charges?", "How much do I spend on subscriptions?",
                "Which card should I pay off first?", "Can I afford a $1,200 laptop?", "Am I on track for my goals?"]
    if not ss.chat:
        cols = st.columns(3)
        for i, q in enumerate(starters):
            if cols[i % 3].button(q, key=f"starter_{i}", width="stretch"):
                ss.pending = q
                st.rerun()
    elif st.button("Clear chat"):
        ss.chat = []
        st.rerun()

    typed = st.chat_input("Ask a money question…", max_chars=MAX_MESSAGE_CHARS)
    question = typed or ss.pop("pending", None)
    if question:
        ss.chat.append({"role": "user", "content": question})
        st.chat_message("user").markdown(question)
        if not settings.ai_provider:
            reply = ("I'm not connected yet. Get a free key at https://aistudio.google.com/apikey, add "
                     "`GEMINI_API_KEY = \"...\"` to `.streamlit/secrets.toml`, then restart the app.")
        else:
            with st.chat_message("assistant"), st.spinner("Checking your accounts…"):
                try:
                    r = chat([ChatMessage(**m) for m in ss.chat[-20:]], snap,
                             goals_fn=lambda: [g.model_dump(mode="json") for g in goal_progress()])
                    reply = r.reply + (f"\n\n<sub>🔧 looked up: {', '.join(dict.fromkeys(r.tools_used))}</sub>"
                                       if r.tools_used else "")
                except Exception as e:  # noqa: BLE001
                    reply = f"Sorry, something went wrong talking to the AI: {type(e).__name__}"
        ss.chat.append({"role": "assistant", "content": reply})
        st.rerun()
