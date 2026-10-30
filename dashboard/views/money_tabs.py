"""Alerts, Cards, and Subscriptions tabs: short, read-only views."""
from __future__ import annotations

import streamlit as st

from dashboard import theme
from dashboard.context import DashboardContext
from dashboard.format import money, pretty


def render_alerts(ctx: DashboardContext) -> None:
    theme.alert_list(ctx.alerts)
    st.caption("A charge is unusual when it's at least twice what you normally spend at that merchant or in that "
               "category. Cards are flagged when a payment is due within 7 days or utilization is 30% or more.")


def render_cards(ctx: DashboardContext) -> None:
    if not ctx.cards:
        st.info("No credit cards on this connection.")
        return
    balance = sum(c.balance for c in ctx.cards)
    limit = sum(c.limit or 0 for c in ctx.cards)
    overall = balance / limit * 100 if limit else 0
    advice = ("Under 10%, which is excellent." if overall < 10
              else "Under 30%, which is fine." if overall < 30
              else "Over 30%, which can lower your credit score.")
    theme.figures([(money(balance), f"owed across {len(ctx.cards)} cards"),
                   (f"{overall:.1f}%", f"of {money(limit)} total limit used")])
    st.caption(advice)
    cols = st.columns(min(len(ctx.cards), 3))
    for i, card in enumerate(ctx.cards):
        with cols[i % len(cols)]:
            theme.credit_card(card, i, money)


def render_subscriptions(ctx: DashboardContext) -> None:
    subs = ctx.subscriptions
    if not subs:
        st.info("No recurring charges in the last 90 days.")
        return
    theme.figures([(money(sum(s.amount for s in subs)), f"a month across {len(subs)} charges"),
                   (money(sum(s.yearly_cost for s in subs)), "a year at this rate")])
    theme.subscription_list(subs, money, pretty)
    st.caption("Detected automatically: the same merchant charging the same price about a month apart.")
