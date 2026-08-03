"""First-run onboarding: habits -> journaling focus -> interests -> skill."""
from __future__ import annotations

import streamlit as st

from . import db, llm
from .interests import (
    HABIT_SUGGESTIONS,
    INTEREST_CATALOG,
    JOURNAL_SUGGESTIONS,
)


def _init_state() -> None:
    st.session_state.setdefault("onboard_step", 1)
    st.session_state.setdefault("ob_habits", [])
    st.session_state.setdefault("ob_focus", [])
    st.session_state.setdefault("ob_interests", [])


def _progress(step: int) -> None:
    labels = ["Habits", "Journal", "Interests"]
    dots = "  ".join(
        f"**{i + 1}. {name}**" if i + 1 == step else f"{i + 1}. {name}"
        for i, name in enumerate(labels)
    )
    st.markdown(dots)
    st.progress(step / 3)


# ---------------------------------------------------------------------------
# Step 1 — Habits
# ---------------------------------------------------------------------------
def _step_habits() -> None:
    st.markdown('<p class="mr-section-title">Which habits do you want to '
                'track?</p>', unsafe_allow_html=True)
    st.markdown('<p class="mr-help">Add your own, or tap a suggestion. Set '
                'whether it\'s a daily or weekly goal.</p>',
                unsafe_allow_html=True)

    # Quick-add suggestions.
    st.write("**Popular habits**")
    cols = st.columns(2)
    for i, sug in enumerate(HABIT_SUGGESTIONS):
        with cols[i % 2]:
            label = f"➕ {sug['name']} · {sug['cadence']}"
            if sug["cadence"] == "Weekly":
                label += f" {sug['target']}x"
            if st.button(label, key=f"sug_habit_{i}", use_container_width=True):
                _add_habit(sug["name"], sug["cadence"], sug["target"])

    st.divider()

    # Custom habit form.
    with st.form("add_habit", clear_on_submit=True):
        st.write("**Add a custom habit**")
        name = st.text_input("Habit description",
                             placeholder="e.g. Drink 4L of water")
        c1, c2 = st.columns(2)
        cadence = c1.selectbox("Cadence", ["Daily", "Weekly"])
        target = c2.number_input(
            "Times per period", min_value=1, max_value=14, value=1,
            help="Daily = times/day, Weekly = times/week",
        )
        if st.form_submit_button("Add habit", use_container_width=True):
            if name.strip():
                _add_habit(name.strip(), cadence, int(target))
            else:
                st.warning("Give your habit a name first.")

    _render_selected_habits()

    st.divider()
    disabled = len(st.session_state["ob_habits"]) == 0
    if st.button("Next: Journaling →", type="primary",
                 use_container_width=True, disabled=disabled):
        st.session_state["onboard_step"] = 2
        st.rerun()
    if disabled:
        st.caption("Add at least one habit to continue.")


def _add_habit(name: str, cadence: str, target: int) -> None:
    habits = st.session_state["ob_habits"]
    if any(h["name"].lower() == name.lower() for h in habits):
        st.toast(f"'{name}' is already added.")
        return
    habits.append({"name": name, "cadence": cadence, "target": target})
    st.rerun()


def _render_selected_habits() -> None:
    habits = st.session_state["ob_habits"]
    if not habits:
        return
    st.write("**Your habits**")
    for i, h in enumerate(habits):
        c1, c2 = st.columns([6, 1])
        cadence = h["cadence"]
        suffix = f" · {h['target']}x / week" if cadence == "Weekly" else " · daily"
        c1.markdown(f"• **{h['name']}**{suffix}")
        if c2.button("✕", key=f"del_habit_{i}"):
            habits.pop(i)
            st.rerun()


# ---------------------------------------------------------------------------
# Step 2 — Journaling focus
# ---------------------------------------------------------------------------
def _step_focus() -> None:
    st.markdown('<p class="mr-section-title">What do you want to journal '
                'about?</p>', unsafe_allow_html=True)
    st.markdown('<p class="mr-help">Pick the areas of life you want to '
                'reflect on. Tap to add or remove.</p>',
                unsafe_allow_html=True)

    selected = st.session_state["ob_focus"]
    cols = st.columns(2)
    for i, item in enumerate(JOURNAL_SUGGESTIONS):
        with cols[i % 2]:
            active = item in selected
            label = f"{'✅' if active else '➕'} {item}"
            if st.button(label, key=f"focus_{i}", use_container_width=True):
                selected.remove(item) if active else selected.append(item)
                st.rerun()

    with st.form("add_focus", clear_on_submit=True):
        custom = st.text_input("Add your own focus area",
                               placeholder="e.g. Parenting")
        if st.form_submit_button("Add", use_container_width=True):
            if custom.strip() and custom.strip() not in selected:
                selected.append(custom.strip())
                st.rerun()

    if selected:
        st.success("Journaling about: " + ", ".join(selected))

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("← Back", use_container_width=True):
        st.session_state["onboard_step"] = 1
        st.rerun()
    disabled = len(selected) == 0
    if c2.button("Next: Interests →", type="primary",
                 use_container_width=True, disabled=disabled):
        st.session_state["onboard_step"] = 3
        st.rerun()
    if disabled:
        st.caption("Pick at least one focus area to continue.")


# ---------------------------------------------------------------------------
# Step 3 — Interests
# ---------------------------------------------------------------------------
def _step_interests() -> None:
    st.markdown('<p class="mr-section-title">What are you curious about?</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="mr-help">We\'ll sprinkle in fun facts about these '
                'while you check in each day.</p>', unsafe_allow_html=True)

    selected = st.session_state["ob_interests"]
    for cat, meta in INTEREST_CATALOG.items():
        st.write(f"**{meta['emoji']} {cat}**")
        cols = st.columns(3)
        for i, item in enumerate(meta["items"]):
            with cols[i % 3]:
                active = item in selected
                label = f"{'✅' if active else '＋'} {item}"
                if st.button(label, key=f"int_{cat}_{i}",
                             use_container_width=True):
                    selected.remove(item) if active else selected.append(item)
                    st.rerun()

    if selected:
        st.success(f"{len(selected)} interests selected: "
                   + ", ".join(selected))

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("← Back", use_container_width=True):
        st.session_state["onboard_step"] = 2
        st.rerun()
    disabled = len(selected) == 0
    if c2.button("🎉 Finish setup", type="primary",
                 use_container_width=True, disabled=disabled):
        _finish()
    if disabled:
        st.caption("Pick at least one interest to continue.")


# ---------------------------------------------------------------------------
# Finish — build skill + persist
# ---------------------------------------------------------------------------
def _finish() -> None:
    user = st.session_state["user"]
    habits = st.session_state["ob_habits"]
    focus = st.session_state["ob_focus"]
    interests = st.session_state["ob_interests"]

    with st.spinner("Personalising your experience…"):
        skill = llm.build_user_skill(habits, focus, interests)
        user.update({
            "habits": habits,
            "journalFocus": focus,
            "interests": interests,
            "skill": skill,
            "onboarded": True,
        })
        db.get_store().upsert_user(user)

    st.session_state["user"] = user
    # Clear onboarding scratch state.
    for key in ("onboard_step", "ob_habits", "ob_focus", "ob_interests"):
        st.session_state.pop(key, None)
    st.balloons()
    st.rerun()


def render() -> None:
    """Entry point for the onboarding wizard."""
    _init_state()
    step = st.session_state["onboard_step"]
    st.markdown(f"### Welcome, {st.session_state['user'].get('name', 'friend')} 👋")
    _progress(step)
    st.write("")
    if step == 1:
        _step_habits()
    elif step == 2:
        _step_focus()
    else:
        _step_interests()
