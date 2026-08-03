"""Shared CSS + small UI helpers for a polished, app-like look."""
from __future__ import annotations

import streamlit as st

_CSS = """
<style>
/* ---- App shell ---- */
.stApp {
    background: linear-gradient(160deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
}
.block-container { padding-top: 2.2rem; max-width: 760px; }

/* ---- Brand ---- */
.mr-brand {
    font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px;
    background: linear-gradient(90deg, #ff6ec4, #7873f5);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.mr-tag { color: #c8c6e6; margin-top: 0; font-size: 0.95rem; }

/* ---- Swipe card ---- */
.mr-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 22px;
    padding: 30px 26px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.35);
    backdrop-filter: blur(10px);
    animation: mr-in 0.35s ease;
    min-height: 240px;
}
@keyframes mr-in {
    from { opacity: 0; transform: translateY(14px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.mr-chip {
    display: inline-block; font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    padding: 4px 12px; border-radius: 999px; margin-bottom: 14px;
}
.mr-chip.habit    { background: rgba(52,211,153,0.18); color: #6ee7b7; }
.mr-chip.journal  { background: rgba(96,165,250,0.18); color: #93c5fd; }
.mr-chip.learning { background: rgba(251,191,36,0.18); color: #fcd34d; }
.mr-card-title { font-size: 1.5rem; font-weight: 800; color: #fff; margin: 4px 0 10px; }
.mr-card-prompt { font-size: 1.08rem; color: #e6e5f5; line-height: 1.5; }
.mr-fact {
    margin-top: 14px; padding: 16px 18px; border-radius: 16px;
    background: rgba(251,191,36,0.10); border-left: 4px solid #fcd34d;
    color: #fdf3d3; font-size: 1.02rem; line-height: 1.55;
}

/* ---- Progress dots ---- */
.mr-dots { text-align: center; margin: 10px 0 4px; letter-spacing: 3px; }

/* ---- Buttons ---- */
.stButton > button {
    border-radius: 14px; font-weight: 700; border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.08); color: #fff; transition: all 0.15s ease;
}
.stButton > button:hover {
    border-color: #7873f5; background: rgba(120,115,245,0.25); transform: translateY(-1px);
}

/* ---- Interest / habit chips as buttons ---- */
.mr-section-title { color:#fff; font-weight:800; font-size:1.25rem; margin-top:0.6rem; }
.mr-help { color:#b9b7d8; font-size:0.9rem; }
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def brand_header() -> None:
    from .config import APP_NAME, APP_TAGLINE

    st.markdown(f'<p class="mr-brand">✨ {APP_NAME}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="mr-tag">{APP_TAGLINE}</p>', unsafe_allow_html=True)
