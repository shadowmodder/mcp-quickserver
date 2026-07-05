# mcp-quickserver

A working MCP (Model Context Protocol) server template. Fork it, swap the store, add your tools.

Demonstrates all three MCP primitives — **tools**, **resources**, and **prompts** — with both stdio and SSE transports, proper error handling, and a test harness that runs without a connected client.

---

## What's included

| Primitive | What it does |
|-----------|--------------|
| **Tools** | `add_note`, `get_note`, `search_notes`, `delete_note` |
| **Resources** | `notes://all` (full list), `notes://{id}` (single note) |
| **Prompts** | `summarize_notes` — builds a summarisation prompt, optionally filtered by tag |

The backing store is an in-memory `NoteStore`. Replacing it with SQLite, Postgres, or Redis is a one-file change.

---

## Install

```bash
pip install -e .
```

Requires Python ≥ 3.10 and the `mcp` SDK.

---

## Wire to Claude Desktop

Copy `claude_desktop_config.json.example` into your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "quickserver": {
      "command": "python",
      "args": ["-m", "mcpquickserver"],
      "cwd": "/absolute/path/to/mcp-quickserver"
    }
  }
}
```

Restart Claude Desktop. The tools appear automatically in the tool picker.

## Wire to Claude Code

```bash
# From within your project
claude mcp add quickserver -- python -m mcpquickserver
```

Or add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "quickserver": {
      "command": "python",
      "args": ["-m", "mcpquickserver"]
    }
  }
}
```

## Run as an HTTP server (SSE transport)

```bash
MCP_HOST=0.0.0.0 MCP_PORT=9000 python -m mcpquickserver --transport sse
```

SSE transport is useful when the client runs in a different process or on a different machine.

---

## Code layout

```
src/mcpquickserver/
├── server.py    ← tool/resource/prompt registration against a NoteStore
├── store.py     ← NoteStore business logic (swap this for persistence)
└── __main__.py  ← CLI entry point
```

### Adding a tool

```python
# server.py
@mcp.tool()
def word_count(text: str) -> str:
    """Count the words in a block of text."""
    return str(len(text.split()))
```

FastMCP generates the JSON schema from the type annotations. The docstring becomes the tool description shown to the model.

### Adding a resource

```python
@mcp.resource("config://settings")
def settings_resource() -> str:
    """Current server configuration as JSON."""
    return json.dumps({"version": "0.1.0", "store": "memory"})
```

Dynamic URI segments work too — `notes://{note_id}` captures `note_id` from the URI and passes it as a parameter.

### Adding a prompt template

```python
@mcp.prompt()
def draft_email(recipient: str, topic: str) -> str:
    """Build a prompt to draft a professional email."""
    return f"Please draft a professional email to {recipient} about: {topic}"
```

---

## Error handling

Tools that raise an exception return an `is_error: true` result to the model so it can recover — the exception does not propagate to the caller or crash the server:

```python
@mcp.tool()
def get_note(note_id: str) -> str:
    """Retrieve a note by its ID."""
    note = store.get(note_id)
    if note is None:
        raise ValueError(f"No note with id {note_id!r}")  # → is_error result
    return json.dumps(note, indent=2)
```

---

## Tests

```bash
pip install -e ".[dev]"
pytest -v
```

Tests cover the `NoteStore` business logic and all tool/resource/prompt handlers directly. No connected client required. The `store` module attribute is monkeypatched per test so each test starts with a clean slate.

---

## Replacing the store

`NoteStore` in `store.py` exposes five methods: `add`, `get`, `delete`, `search`, `all`. Any object that implements those five is a drop-in replacement:

```python
# e.g. SQLite backend
class SqliteNoteStore:
    def __init__(self, db_path: str): ...
    def add(self, title, content, tags=None) -> str: ...
    def get(self, note_id) -> dict | None: ...
    def delete(self, note_id) -> bool: ...
    def search(self, query="", tag="") -> list[dict]: ...
    def all(self) -> list[dict]: ...
```

Swap the `store = NoteStore()` line in `server.py` and the rest is unchanged.
