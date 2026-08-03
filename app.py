"""MyRitual — Streamlit entry point.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from src import auth, config, home, onboarding, questions, styles
from src import db  # noqa: F401  (ensures store initialises early)

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

styles.inject()


def _sidebar(user: dict) -> None:
    with st.sidebar:
        st.markdown(f"**{user.get('name', 'You')}**")
        st.caption(user.get("email", ""))
        backend = db.get_store().backend
        st.caption(f"Storage: {'☁️ Cosmos DB' if backend == 'cosmos' else '🧪 in-memory (demo)'}")
        st.caption(f"AI: {'🟢 on' if config.llm_ready() else '⚪ fallback'}")
        st.divider()
        if st.button("🏠 Home", use_container_width=True):
            st.session_state["view"] = "home"
            st.rerun()
        if st.button("♻️ Redo setup", use_container_width=True):
            user["onboarded"] = False
            db.get_store().upsert_user(user)
            st.session_state["user"] = user
            st.rerun()
        if st.button("🚪 Sign out", use_container_width=True):
            auth.logout()


def main() -> None:
    styles.brand_header()
    st.write("")

    user = auth.require_login()
    if user is None:
        return  # login screen already rendered

    _sidebar(user)

    if not user.get("onboarded"):
        onboarding.render()
        return

    view = st.session_state.setdefault("view", "home")
    if view == "deck":
        questions.render(user)
    else:
        home.render(user)


if __name__ == "__main__":
    main()
