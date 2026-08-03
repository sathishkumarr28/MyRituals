"""LLM helpers — builds each user's personal *skill* profile and generates the
dynamic, non-repetitive daily tracking cards.

Uses the Azure OpenAI v1 endpoint via ``langchain_openai.ChatOpenAI`` (the same
pattern used elsewhere in this workspace). All functions degrade gracefully to
hand-written fallbacks when the LLM is unavailable so the app never breaks.
"""
from __future__ import annotations

import json
import random
import re
from typing import Any

from . import config

try:  # pragma: no cover - import guard
    from langchain_openai import ChatOpenAI

    _HAS_LLM = True
except Exception:  # pragma: no cover
    _HAS_LLM = False


_llm_singleton: Any | None = None


def _get_llm() -> Any | None:
    """Return a cached ChatOpenAI client, or None when unavailable."""
    global _llm_singleton
    if not (_HAS_LLM and config.llm_ready()):
        return None
    if _llm_singleton is None:
        _llm_singleton = ChatOpenAI(
            model=config.CHAT_DEPLOYMENT,
            max_retries=2,
            temperature=0.8,
        )
    return _llm_singleton


def _extract_json(text: str) -> Any:
    """Best-effort JSON extraction from an LLM reply."""
    text = text.strip()
    # Strip ```json fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Grab the outermost { } or [ ] block.
        for opener, closer in (("[", "]"), ("{", "}")):
            start, end = text.find(opener), text.rfind(closer)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    continue
    raise ValueError("Could not parse JSON from LLM response")


# ===========================================================================
# 1. Personal "skill" profile
# ===========================================================================
def build_user_skill(habits: list[dict], journal_focus: list[str],
                     interests: list[str]) -> dict:
    """Create a compact per-user *skill* the app uses to personalise prompts."""
    llm = _get_llm()
    habit_lines = ", ".join(
        f"{h['name']} ({h.get('cadence', 'Daily')}"
        + (f", {h['target']}x" if h.get("target") else "")
        + ")"
        for h in habits
    ) or "none specified"
    focus_line = ", ".join(journal_focus) or "general reflection"
    interest_line = ", ".join(interests) or "general topics"

    fallback = {
        "persona": "A motivated person building better daily habits.",
        "tone": "warm, encouraging and playful",
        "coaching_themes": journal_focus or ["consistency", "self-reflection"],
        "habit_focus": [h["name"] for h in habits],
        "interests": interests,
        "summary": (
            f"Wants to build habits like {habit_lines}. "
            f"Journals about {focus_line}. Curious about {interest_line}."
        ),
    }

    if llm is None:
        return fallback

    system = (
        "You are a habit & journaling coach. Given a user's habits, journaling "
        "focus and interests, produce a compact JSON 'skill profile' that will "
        "be used to personalise daily prompts. Return ONLY JSON with keys: "
        "persona (1 sentence), tone (short phrase), coaching_themes (array of "
        "strings), habit_focus (array), interests (array), summary (2 sentences)."
    )
    user = (
        f"Habits: {habit_lines}\n"
        f"Journaling focus: {focus_line}\n"
        f"Interests: {interest_line}"
    )
    try:
        reply = llm.invoke([("system", system), ("human", user)]).content
        data = _extract_json(reply)
        if isinstance(data, dict):
            data.setdefault("interests", interests)
            data.setdefault("habit_focus", [h["name"] for h in habits])
            return data
    except Exception as exc:  # pragma: no cover
        print(f"[MyRitual] build_user_skill fallback: {exc}")
    return fallback


# ===========================================================================
# 2. Daily tracking cards
# ===========================================================================
# Card types the UI knows how to render.
VALID_TYPES = {"yes_no", "mood", "scale", "text", "fact_card"}


def generate_daily_cards(skill: dict, habits: list[dict],
                         journal_focus: list[str], interests: list[str],
                         count: int | None = None,
                         seed: int | None = None) -> list[dict]:
    """Generate a fresh, varied set of tracking cards for today.

    Each card is a dict shaped like::

        {"id": "q1", "type": "yes_no", "category": "habit",
         "title": "...", "prompt": "...", "options": [...],
         "fact": "...", "topic": "Cricket"}
    """
    count = count or config.DAILY_QUESTION_COUNT
    llm = _get_llm()

    if llm is not None:
        cards = _llm_cards(llm, skill, habits, journal_focus, interests, count, seed)
        if cards:
            return cards
    return _fallback_cards(habits, journal_focus, interests, count, seed)


def _llm_cards(llm: Any, skill: dict, habits: list[dict],
               journal_focus: list[str], interests: list[str],
               count: int, seed: int | None) -> list[dict]:
    habit_lines = "; ".join(
        f"{h['name']} [{h.get('cadence', 'Daily')}]" for h in habits
    ) or "none"
    focus_line = ", ".join(journal_focus) or "general reflection"
    interest_line = ", ".join(interests) or "general topics"
    variety_seed = seed if seed is not None else random.randint(1, 10_000)

    system = (
        "You are the engine behind a delightful daily habit-tracking + 5-minute "
        "journaling + micro-learning app. Generate a set of short cards the user "
        "swipes through. Cards MUST be fun, warm, varied and never boring.\n\n"
        "Return ONLY a JSON array. Each element has keys:\n"
        "  id: unique short string like 'q1'\n"
        "  type: one of 'yes_no', 'mood', 'scale', 'text', 'fact_card'\n"
        "  category: one of 'habit', 'journal', 'learning'\n"
        "  title: a short catchy title (<= 6 words, may include ONE emoji)\n"
        "  prompt: the question or statement (1-2 friendly sentences)\n"
        "  options: for 'yes_no' -> ['Yes','No']; for 'mood' -> 5 emoji+label "
        "strings; for 'scale' -> [] ; for 'text' -> []; for 'fact_card' -> "
        "['Love it','Meh']\n"
        "  fact: for 'fact_card' ONLY, 3-4 punchy lines of a surprising fact "
        "about the user's chosen interest; otherwise ''\n"
        "  topic: the related interest/habit label\n\n"
        "Rules:\n"
        "- Mix the types. Roughly: 40% habit check-ins (yes_no/scale), 30% "
        "journaling (mood/text), 30% learning (fact_card about their interests).\n"
        "- Tie habit cards to the user's actual habits.\n"
        "- Make fact_card facts genuinely interesting and specific to the topic.\n"
        "- Vary phrasing so daily use never feels repetitive.\n"
        "- Keep language positive and motivating."
    )
    user = (
        f"User skill profile: {json.dumps(skill)[:1200]}\n"
        f"Habits: {habit_lines}\n"
        f"Journaling focus: {focus_line}\n"
        f"Interests: {interest_line}\n"
        f"Number of cards: {count}\n"
        f"Variety seed (make output different from other seeds): {variety_seed}\n"
        "Respond with the JSON array only."
    )
    try:
        reply = llm.invoke([("system", system), ("human", user)]).content
        data = _extract_json(reply)
        if isinstance(data, list):
            return _sanitise_cards(data, count)
    except Exception as exc:  # pragma: no cover
        print(f"[MyRitual] generate_daily_cards fallback: {exc}")
    return []


def _sanitise_cards(raw: list[Any], count: int) -> list[dict]:
    """Validate/normalise LLM cards and drop malformed entries."""
    cards: list[dict] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        ctype = str(item.get("type", "")).strip()
        if ctype not in VALID_TYPES:
            continue
        card = {
            "id": str(item.get("id") or f"q{i + 1}"),
            "type": ctype,
            "category": str(item.get("category", "journal")),
            "title": str(item.get("title", "")).strip() or "Check-in",
            "prompt": str(item.get("prompt", "")).strip(),
            "options": item.get("options") or _default_options(ctype),
            "fact": str(item.get("fact", "")).strip(),
            "topic": str(item.get("topic", "")).strip(),
        }
        if not card["prompt"]:
            continue
        cards.append(card)
    # De-duplicate ids.
    seen: set[str] = set()
    for idx, c in enumerate(cards):
        if c["id"] in seen:
            c["id"] = f"q{idx + 1}"
        seen.add(c["id"])
    return cards[:count]


def _default_options(ctype: str) -> list[str]:
    if ctype == "yes_no":
        return ["Yes", "No"]
    if ctype == "mood":
        return ["😞 Rough", "😐 Meh", "🙂 Okay", "😄 Good", "🤩 Amazing"]
    if ctype == "fact_card":
        return ["Love it", "Meh"]
    return []


# ===========================================================================
# 3. Deterministic fallback (no LLM)
# ===========================================================================
_FACTS = {
    "Cricket": "The longest recorded cricket match lasted 12 days in 1939 — "
               "and STILL ended in a draw because the visiting team had to "
               "catch their ship home!",
    "Football": "The fastest goal ever scored took just 2.4 seconds, timed "
                "from kickoff, in a 1998 amateur match in England.",
    "Artificial Intelligence": "The term 'Artificial Intelligence' was coined "
                               "back in 1956 at a summer workshop — decades "
                               "before the computers to run it existed.",
    "Space & Astronomy": "A day on Venus is longer than its year — it spins so "
                          "slowly that one rotation takes 243 Earth days.",
    "History": "Oxford University is older than the Aztec Empire — it was "
               "teaching students by 1096, centuries before Tenochtitlan.",
    "Music": "Listening to music you love releases dopamine, the same feel-good "
             "chemical triggered by good food and exercise.",
}


def _fallback_cards(habits: list[dict], journal_focus: list[str],
                    interests: list[str], count: int,
                    seed: int | None) -> list[dict]:
    rng = random.Random(seed)
    cards: list[dict] = []
    idx = 1

    def add(card: dict) -> None:
        nonlocal idx
        card["id"] = f"q{idx}"
        idx += 1
        cards.append(card)

    # Habit check-ins.
    for h in habits:
        cadence = h.get("cadence", "Daily")
        add({
            "type": "yes_no",
            "category": "habit",
            "title": f"✅ {h['name'][:22]}",
            "prompt": f"Did you keep up with '{h['name']}' today? "
                      f"({cadence} goal)",
            "options": ["Yes", "No"],
            "fact": "",
            "topic": h["name"],
        })

    # Journaling.
    mood_prompts = [
        "How did today actually feel for you?",
        "What was the emotional weather of your day?",
    ]
    add({
        "type": "mood",
        "category": "journal",
        "title": "🌤️ Today's mood",
        "prompt": rng.choice(mood_prompts),
        "options": _default_options("mood"),
        "fact": "",
        "topic": "mood",
    })
    for focus in journal_focus:
        add({
            "type": "text",
            "category": "journal",
            "title": f"✍️ {focus}",
            "prompt": f"One quick note on '{focus}' today — what stood out?",
            "options": [],
            "fact": "",
            "topic": focus,
        })
    add({
        "type": "scale",
        "category": "journal",
        "title": "🔋 Energy level",
        "prompt": "How was your energy today, on a scale of 1 to 5?",
        "options": [],
        "fact": "",
        "topic": "energy",
    })

    # Learning fact cards.
    for interest in interests:
        fact = _FACTS.get(
            interest,
            f"Here's something to explore about {interest} today — "
            f"curiosity keeps the mind young. Look up one new thing about it!",
        )
        add({
            "type": "fact_card",
            "category": "learning",
            "title": f"💡 {interest[:20]} fact",
            "prompt": f"A little spark about {interest}:",
            "options": ["Love it", "Meh"],
            "fact": fact,
            "topic": interest,
        })

    rng.shuffle(cards)
    for i, c in enumerate(cards, 1):
        c["id"] = f"q{i}"
    return cards[:count]
