"""Overview tab: where money went, accounts, and the transaction list."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import theme
from dashboard.context import DashboardContext
from dashboard.format import money, pretty

NOT_SPENDING = ("TRANSFER_OUT", "LOAN_PAYMENTS")


def render(ctx: DashboardContext) -> None:
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Spending by category")
        if ctx.spend["by_category"]:
            theme.category_chart(ctx.spend["by_category"], pretty)
        else:
            st.info("No spending in this range. Try a longer time range in the sidebar.")

        st.subheader("Spending by day")
        rows = [{"Date": t.date, "Spent": t.amount} for t in ctx.txns
                if t.amount > 0 and t.category not in NOT_SPENDING]
        if rows:
            theme.daily_chart(pd.DataFrame(rows).groupby("Date").sum())

    with right:
        st.subheader("Accounts")
        theme.account_list(ctx.accounts, money)
        if ctx.alerts:
            st.subheader("Needs attention")
            theme.alert_list(ctx.alerts[:3])

    st.subheader("Transactions")
    f1, f2 = st.columns([2, 1])
    search = f1.text_input("Search merchants", placeholder="Amazon")
    picked = f2.multiselect("Category", sorted({t.category for t in ctx.txns}), format_func=pretty)
    shown = [t for t in ctx.txns
             if (not search or search.lower() in t.name.lower()) and (not picked or t.category in picked)]
    st.dataframe(
        pd.DataFrame([{"Date": t.date, "Merchant": t.name, "Category": pretty(t.category), "Amount": -t.amount}
                      for t in shown]),
        hide_index=True, width="stretch",
        column_config={"Amount": st.column_config.NumberColumn(format="dollar")},
    )
    st.caption(f"{len(shown)} transactions. Negative amounts are money out.")
