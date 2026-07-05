"""NoteStore tests — no MCP protocol involved, no event loop needed."""
import pytest
from mcpquickserver.store import NoteStore


@pytest.fixture
def store():
    return NoteStore()


def test_add_and_get(store):
    note_id = store.add("Test", "Hello world", tags=["demo"])
    note = store.get(note_id)
    assert note is not None
    assert note["title"] == "Test"
    assert note["content"] == "Hello world"
    assert note["tags"] == ["demo"]
    assert note["id"] == note_id


def test_get_missing_returns_none(store):
    assert store.get("doesnotexist") is None


def test_delete_existing(store):
    note_id = store.add("Delete me", "content")
    assert store.delete(note_id) is True
    assert store.get(note_id) is None


def test_delete_missing_returns_false(store):
    assert store.delete("ghost") is False


def test_search_by_title(store):
    store.add("Python tips", "Use comprehensions")
    store.add("Go patterns", "Use interfaces")
    results = store.search(query="Python")
    assert len(results) == 1
    assert results[0]["title"] == "Python tips"


def test_search_by_content(store):
    store.add("Note A", "discuss goroutines here")
    store.add("Note B", "something else entirely")
    results = store.search(query="goroutines")
    assert len(results) == 1
    assert results[0]["title"] == "Note A"


def test_search_by_tag(store):
    store.add("Rust post", "memory safety", tags=["rust", "systems"])
    store.add("Python post", "dynamic typing", tags=["python"])
    store.add("Untagged", "no tags")
    results = store.search(tag="rust")
    assert len(results) == 1
    assert results[0]["title"] == "Rust post"


def test_search_query_and_tag_combined(store):
    store.add("Rust memory", "ownership model", tags=["rust"])
    store.add("Rust async", "tokio runtime", tags=["rust"])
    store.add("Python async", "asyncio", tags=["python"])
    results = store.search(query="async", tag="rust")
    assert len(results) == 1
    assert results[0]["title"] == "Rust async"


def test_search_empty_returns_all(store):
    store.add("A", "content a")
    store.add("B", "content b")
    assert len(store.search()) == 2


def test_search_no_match_returns_empty(store):
    store.add("A", "content")
    assert store.search(query="zzz_no_match") == []


def test_all_returns_all(store):
    store.add("X", "x content")
    store.add("Y", "y content")
    all_notes = store.all()
    titles = {n["title"] for n in all_notes}
    assert titles == {"X", "Y"}


def test_len(store):
    assert len(store) == 0
    store.add("A", "a")
    store.add("B", "b")
    assert len(store) == 2
    store.delete(store.all()[0]["id"])
    assert len(store) == 1


def test_results_sorted_newest_first(store):
    import time
    id1 = store.add("First", "first note")
    time.sleep(0.01)
    id2 = store.add("Second", "second note")
    results = store.all()
    assert results[0]["id"] == id2
    assert results[1]["id"] == id1


def test_note_has_created_at(store):
    note_id = store.add("Timestamped", "check the ts")
    note = store.get(note_id)
    assert isinstance(note["created_at"], float)
    assert note["created_at"] > 0


def test_tags_default_to_empty_list(store):
    note_id = store.add("No tags", "content")
    note = store.get(note_id)
    assert note["tags"] == []
