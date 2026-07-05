"""Module-level server instance used in tests and direct imports.

Tools, resources, and prompts are registered here against a shared NoteStore.
The __main__ entry point calls mcp.run(); for custom host/port set MCP_HOST / MCP_PORT.
"""
from __future__ import annotations
import json

from mcp.server.fastmcp import FastMCP

from .store import NoteStore

store = NoteStore()
mcp = FastMCP(
    "mcp-quickserver",
    instructions=(
        "A note-taking server. Use add_note to store information, "
        "search_notes to find it later, and get_note to retrieve a specific entry."
    ),
)


# ── Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def add_note(title: str, content: str, tags: list[str] | None = None) -> str:
    """Save a note with an optional list of tags. Returns the note ID."""
    note_id = store.add(title, content, tags)
    return f"Saved. Note ID: {note_id}"


@mcp.tool()
def get_note(note_id: str) -> str:
    """Retrieve a note by its ID."""
    note = store.get(note_id)
    if note is None:
        raise ValueError(f"No note with id {note_id!r}")
    return json.dumps(note, indent=2)


@mcp.tool()
def search_notes(query: str = "", tag: str = "") -> str:
    """Search notes by keyword (title or content) and/or tag.

    Returns a JSON array sorted newest-first. Pass empty strings to list everything.
    """
    results = store.search(query=query, tag=tag)
    if not results:
        return "No notes found."
    summary = [
        {"id": n["id"], "title": n["title"], "tags": n["tags"]} for n in results
    ]
    return json.dumps(summary, indent=2)


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Permanently delete a note by its ID."""
    if not store.delete(note_id):
        raise ValueError(f"No note with id {note_id!r}")
    return f"Deleted note {note_id}"


# ── Resources ─────────────────────────────────────────────────────────────

@mcp.resource("notes://all")
def all_notes_resource() -> str:
    """All stored notes as a JSON array."""
    return json.dumps(store.all(), indent=2)


@mcp.resource("notes://{note_id}")
def note_resource(note_id: str) -> str:
    """A single note as JSON, addressed by ID."""
    note = store.get(note_id)
    if note is None:
        raise ValueError(f"No note with id {note_id!r}")
    return json.dumps(note, indent=2)


# ── Prompt ────────────────────────────────────────────────────────────────

@mcp.prompt()
def summarize_notes(tag: str = "") -> str:
    """Build a prompt to summarize stored notes, optionally filtered by tag."""
    notes = store.search(tag=tag)
    if not notes:
        subject = f"notes tagged '{tag}'" if tag else "any notes"
        return f"There are no {subject} stored yet."
    body = "\n\n".join(f"### {n['title']}\n{n['content']}" for n in notes)
    header = f"notes tagged '{tag}'" if tag else "all notes"
    return (
        f"Please read the following {header} and provide a concise summary, "
        f"grouping related ideas together:\n\n{body}"
    )
