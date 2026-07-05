"""Server wiring tests — calls tool/resource/prompt functions directly.

The module-level `store` in server.py is replaced with a fresh NoteStore per
test via monkeypatching. Tool functions look up `store` in the module globals
at call time, so the patch is transparent.
"""
import json
import pytest

import mcpquickserver.server as srv
from mcpquickserver.store import NoteStore


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch):
    fresh = NoteStore()
    monkeypatch.setattr(srv, "store", fresh)
    return fresh


# ── Tool tests ────────────────────────────────────────────────────────────

def test_add_note_returns_id_and_saves(fresh_store):
    result = srv.add_note("My note", "Some content", tags=["test"])
    assert "Saved" in result
    assert len(fresh_store) == 1


def test_add_note_without_tags(fresh_store):
    result = srv.add_note("Untagged", "content")
    assert "Saved" in result
    note = fresh_store.all()[0]
    assert note["tags"] == []


def test_get_note_returns_json(fresh_store):
    note_id = fresh_store.add("Hello", "World")
    result = srv.get_note(note_id)
    data = json.loads(result)
    assert data["title"] == "Hello"
    assert data["content"] == "World"


def test_get_note_not_found_raises(fresh_store):
    with pytest.raises(ValueError, match="No note"):
        srv.get_note("bad_id")


def test_search_notes_by_keyword(fresh_store):
    fresh_store.add("Alpha", "first note", tags=["a"])
    fresh_store.add("Beta", "second note", tags=["b"])
    result = srv.search_notes(query="first")
    hits = json.loads(result)
    assert len(hits) == 1
    assert hits[0]["title"] == "Alpha"


def test_search_notes_by_tag(fresh_store):
    fresh_store.add("ML note", "gradient descent", tags=["ml"])
    fresh_store.add("Ops note", "deploy steps", tags=["ops"])
    result = srv.search_notes(tag="ml")
    hits = json.loads(result)
    assert len(hits) == 1
    assert hits[0]["title"] == "ML note"


def test_search_notes_no_match(fresh_store):
    result = srv.search_notes(query="zzz")
    assert result == "No notes found."


def test_search_notes_empty_returns_all(fresh_store):
    fresh_store.add("A", "a content")
    fresh_store.add("B", "b content")
    result = srv.search_notes()
    hits = json.loads(result)
    assert len(hits) == 2


def test_delete_note_success(fresh_store):
    note_id = fresh_store.add("Gone", "remove me")
    result = srv.delete_note(note_id)
    assert "Deleted" in result
    assert len(fresh_store) == 0


def test_delete_note_not_found_raises(fresh_store):
    with pytest.raises(ValueError, match="No note"):
        srv.delete_note("ghost")


# ── Resource tests ────────────────────────────────────────────────────────

def test_all_notes_resource_empty(fresh_store):
    result = srv.all_notes_resource()
    assert json.loads(result) == []


def test_all_notes_resource_populated(fresh_store):
    fresh_store.add("X", "x content")
    fresh_store.add("Y", "y content")
    notes = json.loads(srv.all_notes_resource())
    assert len(notes) == 2


def test_note_resource_found(fresh_store):
    note_id = fresh_store.add("Resource test", "content")
    data = json.loads(srv.note_resource(note_id))
    assert data["title"] == "Resource test"


def test_note_resource_not_found_raises(fresh_store):
    with pytest.raises(ValueError):
        srv.note_resource("nope")


# ── Prompt tests ──────────────────────────────────────────────────────────

def test_summarize_prompt_empty_store(fresh_store):
    result = srv.summarize_notes()
    assert "no" in result.lower()


def test_summarize_prompt_includes_all_titles(fresh_store):
    fresh_store.add("Concept A", "explanation of A")
    fresh_store.add("Concept B", "explanation of B")
    result = srv.summarize_notes()
    assert "Concept A" in result
    assert "Concept B" in result


def test_summarize_prompt_tag_filter(fresh_store):
    fresh_store.add("ML note", "gradient descent", tags=["ml"])
    fresh_store.add("Other note", "something else", tags=["other"])
    result = srv.summarize_notes(tag="ml")
    assert "gradient descent" in result
    assert "something else" not in result


# ── Registration smoke test ───────────────────────────────────────────────

def test_all_four_tools_registered():
    tool_names = {t.name for t in srv.mcp._tool_manager._tools.values()}
    assert {"add_note", "get_note", "search_notes", "delete_note"}.issubset(tool_names)


def test_tools_have_descriptions():
    for tool in srv.mcp._tool_manager._tools.values():
        assert tool.description, f"Tool {tool.name!r} missing description"
