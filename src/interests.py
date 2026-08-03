"""Predefined interest catalogue shown as addable buttons during onboarding."""
from __future__ import annotations

# Category -> emoji + list of selectable interests.
INTEREST_CATALOG: dict[str, dict] = {
    "Sports": {
        "emoji": "⚽",
        "items": [
            "Cricket", "Football", "Basketball", "Tennis", "Formula 1",
            "Badminton", "Running", "Cycling", "Swimming", "Chess",
        ],
    },
    "Technology": {
        "emoji": "💻",
        "items": [
            "Artificial Intelligence", "Space & Astronomy", "Gadgets",
            "Programming", "Cybersecurity", "Robotics", "Electric Vehicles",
            "Startups", "Gaming",
        ],
    },
    "General Knowledge": {
        "emoji": "🧠",
        "items": [
            "History", "Geography", "Science", "World Politics", "Economics",
            "Mythology", "Inventions", "Current Affairs",
        ],
    },
    "Arts & Culture": {
        "emoji": "🎨",
        "items": [
            "Music", "Movies", "Photography", "Painting", "Literature",
            "Theatre", "Dance", "Architecture",
        ],
    },
    "Lifestyle": {
        "emoji": "🌿",
        "items": [
            "Cosmetics & Skincare", "Fashion", "Travel", "Cooking",
            "Fitness", "Meditation", "Home & Interiors", "Gardening",
        ],
    },
    "Wellbeing": {
        "emoji": "🧘",
        "items": [
            "Mindfulness", "Nutrition", "Sleep Science", "Yoga",
            "Mental Health", "Productivity", "Personal Finance",
        ],
    },
    "Nature & Animals": {
        "emoji": "🐾",
        "items": [
            "Wildlife", "Oceans", "Birds", "Pets", "Climate & Environment",
            "Plants", "Volcanoes & Earth",
        ],
    },
}


def all_interest_items() -> list[str]:
    """Flat list of every predefined interest."""
    items: list[str] = []
    for cat in INTEREST_CATALOG.values():
        items.extend(cat["items"])
    return items


# Suggested journaling focus areas (used as quick-add chips).
JOURNAL_SUGGESTIONS: list[str] = [
    "Gratitude",
    "Wins of the day",
    "Mood & emotions",
    "Relationships",
    "Work & career",
    "Health & energy",
    "Personal growth",
    "Stress & worries",
    "Creativity & ideas",
    "Money & spending",
]

# Suggested starter habits with a sensible default cadence.
HABIT_SUGGESTIONS: list[dict] = [
    {"name": "Drink 4L of water", "cadence": "Daily", "target": 1},
    {"name": "Eat at least 1 fruit", "cadence": "Daily", "target": 1},
    {"name": "Read a book", "cadence": "Daily", "target": 1},
    {"name": "Yoga or gym", "cadence": "Weekly", "target": 4},
    {"name": "10-minute meditation", "cadence": "Daily", "target": 1},
    {"name": "8 hours of sleep", "cadence": "Daily", "target": 1},
    {"name": "10,000 steps", "cadence": "Daily", "target": 1},
    {"name": "No sugar day", "cadence": "Weekly", "target": 3},
]
