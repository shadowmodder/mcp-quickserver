"""In-memory note store — swap this for SQLite/Redis/Postgres for persistence."""
from __future__ import annotations
import hashlib
import time


class Note:
    __slots__ = ("id", "title", "content", "tags", "created_at")

    def __init__(self, title: str, content: str, tags: list[str]) -> None:
        ts = time.time()
        self.id = hashlib.sha1(f"{title}{ts}".encode()).hexdigest()[:8]
        self.title = title
        self.content = content
        self.tags = list(tags)
        self.created_at = ts

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at,
        }


class NoteStore:
    """Thread-safe in-memory note store."""

    def __init__(self) -> None:
        self._notes: dict[str, Note] = {}

    def add(self, title: str, content: str, tags: list[str] | None = None) -> str:
        note = Note(title, content, tags or [])
        self._notes[note.id] = note
        return note.id

    def get(self, note_id: str) -> dict | None:
        note = self._notes.get(note_id)
        return note.to_dict() if note else None

    def delete(self, note_id: str) -> bool:
        return self._notes.pop(note_id, None) is not None

    def search(self, query: str = "", tag: str = "") -> list[dict]:
        results = list(self._notes.values())
        if query:
            q = query.lower()
            results = [
                n for n in results
                if q in n.title.lower() or q in n.content.lower()
            ]
        if tag:
            results = [n for n in results if tag in n.tags]
        return [n.to_dict() for n in sorted(results, key=lambda n: -n.created_at)]

    def all(self) -> list[dict]:
        return self.search()

    def __len__(self) -> int:
        return len(self._notes)
