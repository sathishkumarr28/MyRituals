"""Cosmos DB data-access layer for MyRitual.

Two containers are used:

* ``users``      — one document per user holding profile, habits, journaling
                   focus, interests and the LLM-generated personal *skill*.
* ``responses``  — one document per completed daily tracking session.

If Cosmos credentials are missing, a lightweight in-memory fallback store is
used so the app still runs locally for demos.
"""
from __future__ import annotations

import datetime as _dt
import threading
from typing import Any

from . import config

# ---------------------------------------------------------------------------
# Optional import — the app still runs without the azure sdk / credentials.
# ---------------------------------------------------------------------------
try:  # pragma: no cover - import guard
    from azure.cosmos import CosmosClient, PartitionKey, exceptions

    _HAS_SDK = True
except Exception:  # pragma: no cover
    _HAS_SDK = False


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# ===========================================================================
# In-memory fallback (used when Cosmos is not configured / unreachable)
# ===========================================================================
class _MemoryStore:
    """Minimal dict-backed stand-in for the two Cosmos containers."""

    def __init__(self) -> None:
        self._users: dict[str, dict] = {}
        self._responses: list[dict] = []
        self._lock = threading.Lock()
        self.backend = "memory"

    # --- users ---
    def get_user(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    def upsert_user(self, doc: dict) -> dict:
        with self._lock:
            doc.setdefault("createdAt", _now_iso())
            doc["updatedAt"] = _now_iso()
            self._users[doc["id"]] = doc
        return doc

    # --- responses ---
    def save_response(self, doc: dict) -> dict:
        with self._lock:
            doc.setdefault("createdAt", _now_iso())
            self._responses.append(doc)
        return doc

    def get_responses(self, user_id: str, limit: int = 30) -> list[dict]:
        rows = [r for r in self._responses if r.get("userId") == user_id]
        rows.sort(key=lambda r: r.get("createdAt", ""), reverse=True)
        return rows[:limit]


# ===========================================================================
# Cosmos-backed store
# ===========================================================================
class _CosmosStore:
    def __init__(self) -> None:
        self.backend = "cosmos"
        self._client = CosmosClient(config.COSMOS_ENDPOINT, credential=config.COSMOS_KEY)
        self._db = self._client.create_database_if_not_exists(id=config.COSMOS_DATABASE)
        self._users = self._db.create_container_if_not_exists(
            id=config.USERS_CONTAINER,
            partition_key=PartitionKey(path="/id"),
        )
        self._responses = self._db.create_container_if_not_exists(
            id=config.RESPONSES_CONTAINER,
            partition_key=PartitionKey(path="/userId"),
        )

    # --- users ---
    def get_user(self, user_id: str) -> dict | None:
        try:
            return self._users.read_item(item=user_id, partition_key=user_id)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def upsert_user(self, doc: dict) -> dict:
        doc.setdefault("createdAt", _now_iso())
        doc["updatedAt"] = _now_iso()
        return self._users.upsert_item(doc)

    # --- responses ---
    def save_response(self, doc: dict) -> dict:
        doc.setdefault("createdAt", _now_iso())
        return self._responses.create_item(doc)

    def get_responses(self, user_id: str, limit: int = 30) -> list[dict]:
        query = (
            "SELECT TOP @limit * FROM c WHERE c.userId = @uid "
            "ORDER BY c.createdAt DESC"
        )
        params = [
            {"name": "@limit", "value": limit},
            {"name": "@uid", "value": user_id},
        ]
        return list(
            self._responses.query_items(
                query=query,
                parameters=params,
                partition_key=user_id,
            )
        )


# ===========================================================================
# Singleton accessor
# ===========================================================================
_store: Any | None = None


def get_store() -> Any:
    """Return a process-wide store instance (Cosmos if available)."""
    global _store
    if _store is not None:
        return _store

    if _HAS_SDK and config.cosmos_ready():
        try:
            _store = _CosmosStore()
            return _store
        except Exception as exc:  # pragma: no cover - network/credential issues
            print(f"[MyRitual] Cosmos init failed, using memory store: {exc}")

    _store = _MemoryStore()
    return _store


# ---------------------------------------------------------------------------
# Convenience helpers used by the UI layer
# ---------------------------------------------------------------------------
def new_user_doc(user_id: str, email: str, name: str, provider: str) -> dict:
    return {
        "id": user_id,
        "email": email,
        "name": name,
        "provider": provider,
        "onboarded": False,
        "habits": [],
        "journalFocus": [],
        "interests": [],
        "skill": None,
        "type": "user",
    }
