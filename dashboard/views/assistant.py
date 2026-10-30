"""Ask AI tab: chat with Penny, who reads the same numbers the dashboard shows."""
from __future__ import annotations

import logging

import streamlit as st

from app.ai.chat import MAX_MESSAGE_CHARS, AIError, chat
from app.schemas import ChatMessage
from dashboard.context import DashboardContext

log = logging.getLogger(__name__)
HISTORY_TURNS = 20
STARTERS = [
    "Where did my money go this month?",
    "Any unusual charges?",
    "How much do I spend on subscriptions?",
    "Which card should I pay off first?",
    "Can I afford a $1,200 laptop?",
    "Am I on track for my goals?",
]
NO_KEY_REPLY = ("The assistant needs an API key. Get a free one at https://aistudio.google.com/apikey, add "
                '`GEMINI_API_KEY = "..."` to `.streamlit/secrets.toml`, then restart the app.')


def _ask(question: str, ctx: DashboardContext) -> tuple[str, bool]:
    """Returns (reply, failed). Failed replies are shown but never sent back to the model as history."""
    if not ctx.settings.ai_provider:
        return NO_KEY_REPLY, True
    history = [ChatMessage(role=m["role"], content=m["content"])
               for m in st.session_state.chat[-HISTORY_TURNS:] if not m.get("error")]
    try:
        r = chat(history, ctx.snapshot, goals_fn=lambda: [g.model_dump(mode="json") for g in ctx.goal_progress()])
    except AIError as e:
        return str(e), True
    except Exception as e:
        log.exception("Assistant call failed")
        return f"The assistant hit an error ({type(e).__name__}). Try again in a moment.", True
    sources = f"\n\n<sub>Looked up: {', '.join(dict.fromkeys(r.tools_used))}</sub>" if r.tools_used else ""
    return r.reply + sources, False


def render(ctx: DashboardContext) -> None:
    ss = st.session_state
    st.caption("Ask about your money. Penny looks up your actual numbers instead of guessing, and can't move "
               "money or make trades.")
    for m in ss.chat:
        st.chat_message(m["role"]).markdown(m["content"])

    if not ss.chat:
        cols = st.columns(3)
        for i, q in enumerate(STARTERS):
            if cols[i % 3].button(q, key=f"starter_{i}", width="stretch"):
                ss.pending = q
                st.rerun()
    elif st.button("Clear conversation"):
        ss.chat = []
        st.rerun()

    question = st.chat_input("Ask a question about your money", max_chars=MAX_MESSAGE_CHARS) or ss.pop("pending", None)
    if not question:
        return
    ss.chat.append({"role": "user", "content": question})
    st.chat_message("user").markdown(question)
    with st.chat_message("assistant"), st.spinner("Looking at your accounts…"):
        reply, failed = _ask(question, ctx)
    ss.chat.append({"role": "assistant", "content": reply, "error": failed})
    st.rerun()
