"""Session state in one place, so key names aren't scattered across views."""
import streamlit as st


def init() -> None:
    st.session_state.setdefault("data_version", 0)
    st.session_state.setdefault("chat", [])


def data_version() -> int:
    return st.session_state.data_version


def refresh_data() -> None:
    """Bump the version so the cached loader fetches fresh data on the next run."""
    st.session_state.data_version += 1
