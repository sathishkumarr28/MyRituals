"""Central configuration and environment loading for MyRitual.

Loads credentials from the base workspace `.env` (one level above this app
folder) so the same Azure OpenAI + Cosmos DB credentials are reused.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Locate and load the .env file. It lives in the base workspace folder, which
# is the parent of this application folder. We search upward as a fallback.
# ---------------------------------------------------------------------------
_APP_DIR = Path(__file__).resolve().parent.parent          # habit_journal_app/
_BASE_DIR = _APP_DIR.parent                                 # tutorial-agentic-ai/

for _candidate in (_APP_DIR / ".env", _BASE_DIR / ".env"):
    if _candidate.exists():
        load_dotenv(_candidate, override=False)
        break
else:  # pragma: no cover - fallback to default search behaviour
    load_dotenv(override=False)


# ---------------------------------------------------------------------------
# Azure OpenAI (v1 endpoint) — picked up automatically by langchain_openai
# via OPENAI_API_KEY / OPENAI_BASE_URL, but we expose them here too.
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")
CHAT_DEPLOYMENT: str = os.getenv("CHAT_DEPLOYMENT", "gpt-5.4-mini-1")
EMBED_DEPLOYMENT: str = os.getenv("EMBED_DEPLOYMENT", "text-embedding-3-small-2")

# ---------------------------------------------------------------------------
# Cosmos DB
# ---------------------------------------------------------------------------
COSMOS_ENDPOINT: str | None = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY: str | None = os.getenv("COSMOS_KEY")

COSMOS_DATABASE: str = os.getenv("COSMOS_DATABASE", "myritual")
USERS_CONTAINER: str = "users"
RESPONSES_CONTAINER: str = "responses"

# ---------------------------------------------------------------------------
# App level flags
# ---------------------------------------------------------------------------
APP_NAME = "MyRitual"
APP_TAGLINE = "Track habits. Journal in 5 minutes. Learn something new every day."

# Number of daily tracking cards to generate.
DAILY_QUESTION_COUNT = int(os.getenv("DAILY_QUESTION_COUNT", "22"))


def llm_ready() -> bool:
    """Return True when Azure OpenAI credentials are present."""
    return bool(OPENAI_API_KEY and OPENAI_BASE_URL)


def cosmos_ready() -> bool:
    """Return True when Cosmos DB credentials are present."""
    return bool(COSMOS_ENDPOINT and COSMOS_KEY)
