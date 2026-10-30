"""Alerts, Cards, and Subscriptions tabs: short, read-only views."""
from __future__ import annotations

from datetime import date

import streamlit as st

from app.services.payoff import PayoffPlan, compare
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
    render_payoff_plan(ctx)


def _md(text: str) -> str:
    """Streamlit markdown reads $...$ as a math formula, which garbles two dollar amounts in one line."""
    return text.replace("$", "\\$")


def _months_from_now(months: int) -> date:
    m = date.today().month - 1 + months
    return date(date.today().year + m // 12, m % 12 + 1, 1)


def _plan_summary(plan: PayoffPlan, title: str, blurb: str, recommended: bool) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**" + (" (lower interest)" if recommended else ""))
        st.caption(blurb)
        if not plan.feasible:
            st.markdown("Never pays off at this payment.")
            return
        theme.figures([(f"{plan.months} months", f"debt-free by {_months_from_now(plan.months):%B %Y}"),
                       (money(plan.total_interest), "total interest")])
        st.caption("Order: " + ", then ".join(f"{p.name} (month {p.month})" for p in plan.order))


def render_payoff_plan(ctx: DashboardContext) -> None:
    st.subheader("Payoff plan")
    extra = st.number_input("Extra to put toward cards each month ($)", min_value=0.0, max_value=10_000.0,
                            value=100.0, step=25.0, help="On top of every card's minimum payment.")
    result = compare(ctx.cards, extra)
    if result is None:
        st.success("No card balances to pay off.")
        return

    st.caption(_md(f"Paying {money(result.avalanche.monthly_payment)} a month in total: all minimums plus "
                   f"{money(extra)} extra."))
    av_cheaper = result.interest_saved_by_avalanche >= 1
    left, right = st.columns(2, gap="medium")
    with left:
        _plan_summary(result.avalanche, "Avalanche", "Extra money goes to the highest APR first.", av_cheaper)
    with right:
        _plan_summary(result.snowball, "Snowball", "Extra money goes to the smallest balance first.", False)

    st.markdown(_md(result.recommendation))
    if result.avalanche.feasible:
        theme.payoff_chart({"Avalanche": result.avalanche.balance_by_card,
                            "Snowball": result.snowball.balance_by_card})
    st.caption(_md(" ".join(result.assumptions) + " Educational estimate, not financial advice."))


def render_subscriptions(ctx: DashboardContext) -> None:
    subs = ctx.subscriptions
    if not subs:
        st.info("No recurring charges in the last 90 days.")
        return
    theme.figures([(money(sum(s.amount for s in subs)), f"a month across {len(subs)} charges"),
                   (money(sum(s.yearly_cost for s in subs)), "a year at this rate")])
    theme.subscription_list(subs, money, pretty)
    st.caption("Detected automatically: the same merchant charging the same price about a month apart.")
