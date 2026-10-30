"""Goals tab: savings goals measured against the savings balance."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from app.db import session_scope
from app.services import goals as goals_svc
from dashboard.context import DashboardContext
from dashboard.format import money


def render(ctx: DashboardContext) -> None:
    st.caption(f"Progress is measured against your savings balance of {money(ctx.savings_balance)}.")
    for g in ctx.goal_progress():
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{g.name}**  \n{money(g.saved)} of {money(g.target)} by {g.target_date:%B %Y}")
            c1.progress(g.pct / 100, text=f"{g.pct:.0f}%")
            c1.caption(g.on_track_note)
            if c2.button("Delete", key=f"del_{g.id}"):
                with session_scope() as db:
                    goals_svc.delete_goal(db, ctx.user_id, g.id)
                st.rerun()

    with st.form("new_goal", clear_on_submit=True):
        st.markdown("**Add a goal**")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name", placeholder="Emergency fund")
        target = c2.number_input("Target ($)", min_value=1.0, value=10000.0, step=100.0)
        when = c3.date_input("By", value=date.today() + timedelta(days=180), min_value=date.today())
        if st.form_submit_button("Add goal", type="primary"):
            try:
                with session_scope() as db:
                    goals_svc.add_goal(db, ctx.user_id, name, target, when)
            except ValueError as e:
                st.error(str(e))
            else:
                st.rerun()
