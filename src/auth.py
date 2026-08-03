"""Authentication for MyRitual.

Two paths are supported:

1. **Real OAuth (Google / Apple)** via Streamlit's native ``st.login`` (OpenID
   Connect). This activates automatically once you add an ``[auth]`` section to
   ``.streamlit/secrets.toml`` (see README). Works great on Azure Web App.

2. **Demo email sign-in** — a zero-config fallback so the app is fully usable
   locally without registering an OAuth client.
"""
from __future__ import annotations

import hashlib

import streamlit as st

from . import db


def _user_id(email: str) -> str:
    """Stable id derived from the email address."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:24]


def _oauth_configured() -> bool:
    """True when an [auth] block exists in secrets (native OIDC enabled)."""
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def _load_or_create_user(email: str, name: str, provider: str) -> dict:
    store = db.get_store()
    uid = _user_id(email)
    user = store.get_user(uid)
    if user is None:
        user = store.upsert_user(db.new_user_doc(uid, email, name, provider))
    return user


def current_user() -> dict | None:
    """Return the signed-in user document, or None."""
    return st.session_state.get("user")


def logout() -> None:
    """Sign the user out of both the app session and OIDC (if used)."""
    for key in ("user", "cards", "card_index", "answers", "onboard_step"):
        st.session_state.pop(key, None)
    if _oauth_configured():
        try:
            st.logout()
        except Exception:
            pass
    st.rerun()


def _provider_buttons() -> None:
    """Render Google / Apple sign-in buttons backed by st.login."""
    st.markdown("#### Sign in to continue")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟦  Continue with Google", use_container_width=True):
            try:
                st.login("google")
            except Exception:
                st.login()
    with col2:
        if st.button("  Continue with Apple", use_container_width=True):
            try:
                st.login("apple")
            except Exception:
                st.login()


def _demo_login() -> None:
    """Config-free email sign-in used when OAuth is not set up."""
    st.markdown("#### Sign in")
    st.caption(
        "Google / Apple sign-in activates automatically once OAuth is "
        "configured in `.streamlit/secrets.toml` (see README). For now, use "
        "quick email sign-in below."
    )
    with st.form("demo_login", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        name = st.text_input("Display name", placeholder="Your name")
        submitted = st.form_submit_button("Continue", use_container_width=True)
    if submitted:
        if not email or "@" not in email:
            st.error("Please enter a valid email address.")
            return
        user = _load_or_create_user(email, name or email.split("@")[0], "demo")
        st.session_state["user"] = user
        st.rerun()


def require_login() -> dict | None:
    """Gate the app behind authentication.

    Returns the user doc when signed in, otherwise renders the login screen and
    returns ``None`` (the caller should stop rendering).
    """
    if current_user() is not None:
        return current_user()

    # Native OIDC path.
    if _oauth_configured():
        exp_user = getattr(st, "user", None)
        if exp_user is not None and getattr(exp_user, "is_logged_in", False):
            email = getattr(exp_user, "email", None) or "unknown@user"
            name = getattr(exp_user, "name", None) or email.split("@")[0]
            provider = "oauth"
            user = _load_or_create_user(email, name, provider)
            st.session_state["user"] = user
            return user
        _provider_buttons()
        return None

    _demo_login()
    return None
