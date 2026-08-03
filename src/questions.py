"""The daily swipeable card deck — the heart of the tracking experience."""
from __future__ import annotations

import datetime as _dt
import random

import streamlit as st
import streamlit.components.v1 as components

from . import db, llm


def _today_key() -> str:
    return _dt.date.today().isoformat()


def _ensure_cards(user: dict) -> None:
    """Generate today's deck once and cache it in session state."""
    key = f"deck::{user['id']}::{_today_key()}"
    if st.session_state.get("deck_key") == key and st.session_state.get("cards"):
        return
    with st.spinner("Crafting today's questions just for you…"):
        seed = random.randint(1, 1_000_000)
        cards = llm.generate_daily_cards(
            skill=user.get("skill") or {},
            habits=user.get("habits", []),
            journal_focus=user.get("journalFocus", []),
            interests=user.get("interests", []),
            seed=seed,
        )
    st.session_state["cards"] = cards
    st.session_state["deck_key"] = key
    st.session_state["card_index"] = 0
    st.session_state["answers"] = {}


def _set_answer(card_id: str, value) -> None:
    st.session_state["answers"][card_id] = value


def _advance() -> None:
    total = len(st.session_state["cards"])
    st.session_state["card_index"] = min(
        st.session_state["card_index"] + 1, total - 1
    )


def _go_back() -> None:
    st.session_state["card_index"] = max(st.session_state["card_index"] - 1, 0)


# ---------------------------------------------------------------------------
# Swipe / keyboard support (visual nudge + arrow keys)
# ---------------------------------------------------------------------------
def _swipe_listener() -> None:
    """Lightweight touch/keyboard hint. Buttons remain the source of truth."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        function clickByText(txt){
            const btns = doc.querySelectorAll('button');
            for (const b of btns){ if(b.innerText.trim().startsWith(txt)){ b.click(); return; } }
        }
        doc.onkeydown = function(e){
            if(e.key === 'ArrowRight'){ clickByText('Next'); }
            if(e.key === 'ArrowLeft'){ clickByText('◀'); }
        };
        let sx = null;
        doc.ontouchstart = (e)=>{ sx = e.changedTouches[0].screenX; };
        doc.ontouchend = (e)=>{
            if(sx === null) return;
            const dx = e.changedTouches[0].screenX - sx;
            if(dx < -60){ clickByText('Next'); }
            if(dx > 60){ clickByText('◀'); }
            sx = null;
        };
        </script>
        """,
        height=0,
    )


# ---------------------------------------------------------------------------
# Card renderers
# ---------------------------------------------------------------------------
def _render_card_body(card: dict) -> None:
    cat = card.get("category", "journal")
    st.markdown(
        f'<div class="mr-card">'
        f'<span class="mr-chip {cat}">{cat}</span>'
        f'<div class="mr-card-title">{card["title"]}</div>'
        f'<div class="mr-card-prompt">{card["prompt"]}</div>'
        + (f'<div class="mr-fact">{card["fact"]}</div>' if card.get("fact") else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_inputs(card: dict) -> None:
    cid = card["id"]
    ctype = card["type"]
    current = st.session_state["answers"].get(cid)
    st.write("")

    if ctype in ("yes_no", "fact_card"):
        opts = card.get("options") or ["Yes", "No"]
        cols = st.columns(len(opts))
        for i, opt in enumerate(opts):
            marker = "🔘 " if current == opt else ""
            if cols[i].button(f"{marker}{opt}", key=f"{cid}_opt_{i}",
                              use_container_width=True):
                _set_answer(cid, opt)
                _advance()
                st.rerun()

    elif ctype == "mood":
        opts = card.get("options") or ["😞", "😐", "🙂", "😄", "🤩"]
        cols = st.columns(len(opts))
        for i, opt in enumerate(opts):
            marker = "✅ " if current == opt else ""
            if cols[i].button(f"{marker}{opt}", key=f"{cid}_mood_{i}",
                              use_container_width=True):
                _set_answer(cid, opt)
                _advance()
                st.rerun()

    elif ctype == "scale":
        cols = st.columns(5)
        for i in range(1, 6):
            marker = "🔵 " if current == i else ""
            if cols[i - 1].button(f"{marker}{i}", key=f"{cid}_scale_{i}",
                                  use_container_width=True):
                _set_answer(cid, i)
                _advance()
                st.rerun()
        st.caption("1 = low · 5 = high")

    elif ctype == "text":
        val = st.text_area("Your note", value=current or "",
                           key=f"{cid}_text", label_visibility="collapsed",
                           placeholder="Type a quick thought… (optional)")
        if val != (current or ""):
            _set_answer(cid, val)


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------
def _save_session(user: dict) -> None:
    cards = st.session_state["cards"]
    answers = st.session_state["answers"]
    doc = {
        "id": f"{user['id']}-{_today_key()}-{random.randint(1000, 9999)}",
        "userId": user["id"],
        "date": _today_key(),
        "type": "daily_session",
        "answers": [
            {
                "cardId": c["id"],
                "category": c.get("category"),
                "cardType": c["type"],
                "topic": c.get("topic"),
                "prompt": c["prompt"],
                "answer": answers.get(c["id"]),
            }
            for c in cards
        ],
        "answeredCount": sum(1 for c in cards if answers.get(c["id"]) not in (None, "")),
        "totalCount": len(cards),
    }
    db.get_store().save_response(doc)
    st.session_state["last_saved"] = doc


def _render_summary(user: dict) -> None:
    st.success("🎉 Session saved! You showed up for yourself today.")
    doc = st.session_state.get("last_saved", {})
    st.metric("Cards answered", f"{doc.get('answeredCount', 0)} / {doc.get('totalCount', 0)}")

    habit_yes = sum(
        1 for a in doc.get("answers", [])
        if a["category"] == "habit" and a["answer"] == "Yes"
    )
    habit_total = sum(1 for a in doc.get("answers", []) if a["category"] == "habit")
    if habit_total:
        st.write(f"**Habits kept today:** {habit_yes} / {habit_total} ✅")

    with st.expander("Review your answers"):
        for a in doc.get("answers", []):
            ans = a.get("answer")
            if ans in (None, ""):
                continue
            st.markdown(f"**{a['prompt']}**  \n→ {ans}")

    c1, c2 = st.columns(2)
    if c1.button("🔄 New deck", use_container_width=True):
        for k in ("cards", "deck_key", "card_index", "answers", "last_saved"):
            st.session_state.pop(k, None)
        st.rerun()
    if c2.button("🏠 Done", type="primary", use_container_width=True):
        st.session_state["view"] = "home"
        for k in ("cards", "deck_key", "card_index", "answers", "last_saved"):
            st.session_state.pop(k, None)
        st.rerun()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def render(user: dict) -> None:
    if st.session_state.get("last_saved"):
        _render_summary(user)
        return

    _ensure_cards(user)
    cards = st.session_state["cards"]
    if not cards:
        st.warning("Couldn't build a deck right now. Please try again.")
        if st.button("Retry"):
            for k in ("cards", "deck_key"):
                st.session_state.pop(k, None)
            st.rerun()
        return

    idx = st.session_state["card_index"]
    total = len(cards)
    card = cards[idx]

    # Progress dots.
    answered = st.session_state["answers"]
    dots = "".join(
        "🟣" if i == idx else ("🟢" if cards[i]["id"] in answered else "⚪")
        for i in range(total)
    )
    st.markdown(f'<div class="mr-dots">{dots}</div>', unsafe_allow_html=True)
    st.caption(f"Card {idx + 1} of {total} · swipe or use the arrows")

    _render_card_body(card)
    _render_inputs(card)

    st.write("")
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("◀ Prev", use_container_width=True, disabled=idx == 0):
        _go_back()
        st.rerun()
    if c2.button("Skip", use_container_width=True):
        _advance()
        st.rerun()
    if idx < total - 1:
        if c3.button("Next ▶", type="primary", use_container_width=True):
            _advance()
            st.rerun()
    else:
        if c3.button("✅ Finish", type="primary", use_container_width=True):
            _save_session(user)
            st.rerun()

    _swipe_listener()
