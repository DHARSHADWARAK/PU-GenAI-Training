from copy import deepcopy
from typing import Any


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str) -> dict[str, Any]:
        return deepcopy(self._sessions.get(session_id, {}))

    def set(self, session_id: str, value: dict[str, Any]) -> None:
        self._sessions[session_id] = deepcopy(value)

    def update(self, session_id: str, value: dict[str, Any]) -> dict[str, Any]:
        current = self.get(session_id)
        current.update(value)
        self.set(session_id, current)
        return current


session_store = InMemorySessionStore()
