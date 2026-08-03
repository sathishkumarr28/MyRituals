"""Home dashboard shown after onboarding."""
from __future__ import annotations

import datetime as _dt

import streamlit as st

from . import db


def _streak(sessions: list[dict]) -> int:
    """Count consecutive days (ending today or yesterday) with a session."""
    dates = {s.get("date") for s in sessions}
    streak = 0
    day = _dt.date.today()
    if day.isoformat() not in dates:
        day = day - _dt.timedelta(days=1)
        if day.isoformat() not in dates:
            return 0
    while day.isoformat() in dates:
        streak += 1
        day -= _dt.timedelta(days=1)
    return streak


def render(user: dict) -> None:
    st.markdown(f"### Hi {user.get('name', 'there')} 👋")
    st.caption("Your daily 5 minutes for habits, journaling and a little learning.")

    sessions = db.get_store().get_responses(user["id"], limit=60)
    streak = _streak(sessions)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Streak", f"{streak} day{'s' if streak != 1 else ''}")
    c2.metric("🗂️ Habits", len(user.get("habits", [])))
    c3.metric("📓 Check-ins", len(sessions))

    st.write("")
    if st.button("▶️  Start today's check-in", type="primary",
                 use_container_width=True):
        st.session_state["view"] = "deck"
        st.rerun()

    # Habits overview.
    with st.expander("🎯 My habits", expanded=True):
        habits = user.get("habits", [])
        if not habits:
            st.write("No habits yet.")
        for h in habits:
            suffix = (f"{h['target']}x / week" if h.get("cadence") == "Weekly"
                      else "daily")
            st.markdown(f"• **{h['name']}** · {suffix}")

    with st.expander("✍️ Journaling focus"):
        st.write(", ".join(user.get("journalFocus", [])) or "—")

    with st.expander("💡 Interests"):
        st.write(", ".join(user.get("interests", [])) or "—")

    # Recent history.
    if sessions:
        with st.expander("📅 Recent check-ins"):
            for s in sessions[:10]:
                st.markdown(
                    f"**{s.get('date')}** — "
                    f"{s.get('answeredCount', 0)}/{s.get('totalCount', 0)} answered"
                )
