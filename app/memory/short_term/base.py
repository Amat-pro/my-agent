from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MemoryMessage:
    role: str
    content: str


class ShortTermMemory(Protocol):
    def append(self, session_id: str, role: str, content: str) -> None:
        """Append a message to a session."""

    def list_messages(self, session_id: str) -> list[MemoryMessage]:
        """Return messages for a session."""


class InMemoryShortTermMemory:
    def __init__(self) -> None:
        self._messages: dict[str, list[MemoryMessage]] = {}

    def append(self, session_id: str, role: str, content: str) -> None:
        self._messages.setdefault(session_id, []).append(MemoryMessage(role=role, content=content))

    def list_messages(self, session_id: str) -> list[MemoryMessage]:
        return list(self._messages.get(session_id, []))
