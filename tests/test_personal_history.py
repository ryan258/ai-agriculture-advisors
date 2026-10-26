"""Temporary-store coverage for metadata search and separate personal notes."""

import json
from pathlib import Path

import pytest
from chromadb.api.models.Collection import Collection

from lib.storage import HistoryStore
from lib.storage.history_store import ANNOTATION_FIELDS, ANNOTATION_LIMITS


def _seed(store: HistoryStore, count: int = 1) -> list[str]:
    """Insert source fixtures with explicit embeddings, avoiding model work."""
    ids = [f"saved-{index:03}" for index in range(count)]
    store._collection.add(
        ids=ids,
        embeddings=[[0.0] for _ in ids],
        documents=[
            json.dumps(
                {
                    "query": f"Question {index}",
                    "experts": ["agriculture"],
                    "responses": [{"role": "agriculture", "response": "Original"}],
                }
            )
            for index in range(count)
        ],
        metadatas=[
            {
                "query": f"Question {index}",
                "timestamp": "2026-10-16T12:00:00",
                "experts": '["agriculture"]',
                "result_type": "query",
                **({"panel_label": "Effort review"} if index == 0 else {}),
            }
            for index in range(count)
        ],
    )
    return ids


def test_history_search_scans_all_metadata_in_bounded_batches(
    tmp_path: Path, monkeypatch
) -> None:
    store = HistoryStore(str(tmp_path / "history"))
    ids = _seed(store, 205)
    store.update_annotations(ids[0], {"title": "Resume the DOOR project"})
    calls = []
    original_get = Collection.get

    def tracked_get(collection, *args, **kwargs):
        calls.append((collection.name, kwargs))
        return original_get(collection, *args, **kwargs)

    monkeypatch.setattr(Collection, "get", tracked_get)
    found = store.get_history(search="door")

    assert [row["id"] for row in found] == [ids[0]]
    assert found[0]["title"] == "Resume the DOOR project"
    assert found[0]["panel_label"] == "Effort review"
    assert all(kwargs["include"] == ["metadatas"] for _, kwargs in calls)
    source_calls = [kwargs for name, kwargs in calls if name == "query_history_v3"]
    assert [kwargs["offset"] for kwargs in source_calls] == [0, 100, 200]
    assert all(kwargs["limit"] == 100 for kwargs in source_calls)
    assert store.get_history(search="EFFORT REVIEW")[0]["id"] == ids[0]
    assert store.get_history(search="question 204")[0]["id"] == ids[-1]
    assert store.get_history(search="no such result") == []


def test_history_has_stable_tie_order_and_filters_before_pagination(tmp_path: Path):
    store = HistoryStore(str(tmp_path / "history"))
    ids = _seed(store, 15)
    store.update_annotations(ids[0], {"status": "waiting", "blocker": "A reply"})
    store.update_annotations(ids[1], {"status": "undecided"})
    store.update_annotations(ids[14], {"status": "tried"})

    assert [row["id"] for row in store.get_history(limit=2, offset=1)] == [
        ids[13],
        ids[12],
    ]
    assert [row["id"] for row in store.get_open_items()] == [ids[1], ids[0]]
    assert store.get_history(search="waiting")[0]["blocker"] == "A reply"
    assert store.get_history(limit=0) == []
    assert store.get_history(offset=30) == []
    assert store.get_history(limit=1)[0]["panel_label"] == ""


def test_reading_legacy_history_does_not_create_annotation_collection(tmp_path: Path):
    store = HistoryStore(str(tmp_path / "history"))
    ids = _seed(store)
    before = [collection.name for collection in store._client.list_collections()]

    notes = store.get_annotations(ids[0])
    row = store.get_history()[0]

    assert notes == dict.fromkeys(ANNOTATION_FIELDS, "")
    assert all(row[field] == "" for field in ANNOTATION_FIELDS)
    assert [
        collection.name for collection in store._client.list_collections()
    ] == before


def test_personal_annotations_preserve_source_and_reopen_without_embeddings(
    tmp_path: Path, monkeypatch
):
    location = str(tmp_path / "history")
    store = HistoryStore(location)
    result_id = _seed(store)[0]
    original = store._collection.get(
        ids=[result_id], include=["documents", "metadatas"]
    )
    original_upsert = Collection.upsert
    calls = []

    def checked_upsert(collection, *args, **kwargs):
        assert collection.name == "personal_annotations"
        assert collection._embedding_function is None
        assert "documents" not in kwargs
        assert kwargs["embeddings"] == [[0.0]]
        calls.append(kwargs)
        return original_upsert(collection, *args, **kwargs)

    monkeypatch.setattr(Collection, "upsert", checked_upsert)
    store.update_annotations(
        result_id,
        {
            "title": " A next task ",
            "next_step": "Dictate the question",
            "status": "waiting",
        },
    )
    store.update_annotations(result_id, {"outcome": "Tried it; less rereading"})
    reopened = HistoryStore(location)

    assert reopened.get_annotations(result_id) == {
        "title": "A next task",
        "status": "waiting",
        "next_step": "Dictate the question",
        "last_step": "",
        "blocker": "",
        "outcome": "Tried it; less rereading",
        "outcome_rating": "",
    }
    assert (
        reopened._collection.get(ids=[result_id], include=["documents", "metadatas"])
        == original
    )
    annotations = reopened._annotation_collection()
    assert annotations.get(ids=[result_id], include=["documents"])["documents"] == [
        None
    ]
    assert len(calls) == 2
    assert reopened.update_annotations(result_id, {"title": ""})["title"] == ""


@pytest.mark.parametrize(
    "updates",
    [
        {"status": "completed"},
        {"unknown": "text"},
        {"title": None},
        {"title": "x" * (ANNOTATION_LIMITS["title"] + 1)},
        {"next_step": "x" * (ANNOTATION_LIMITS["next_step"] + 1)},
        {"outcome": "x" * (ANNOTATION_LIMITS["outcome"] + 1)},
    ],
)
def test_invalid_annotations_fail_without_storage_mutation(tmp_path: Path, updates):
    store = HistoryStore(str(tmp_path / "history"))
    result_id = _seed(store)[0]

    with pytest.raises(ValueError):
        store.update_annotations(result_id, updates)

    assert store._annotation_collection() is None


def test_annotations_reject_missing_result_before_creating_collection(tmp_path: Path):
    store = HistoryStore(str(tmp_path / "history"))
    with pytest.raises(ValueError, match="Saved result not found"):
        store.update_annotations("missing", {"title": "Cannot create an orphan"})
    assert store._annotation_collection() is None


def test_new_result_metadata_captures_panel_label(tmp_path: Path, monkeypatch):
    store = HistoryStore(str(tmp_path / "history"))
    captured = []

    def capture_add(collection, **kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(Collection, "add", capture_add)
    store.save_result(
        "A task",
        ["agriculture"],
        [],
        advisor_context={
            "panel": {"id": "agriculture", "label": "Historical panel label"},
            "advisors": [
                {
                    "role": "agriculture",
                    "label": "Agriculture",
                    "system_prompt": "Inspect the task",
                    "limitations": "No live evidence",
                }
            ],
        },
    )

    assert captured[0]["metadatas"][0]["panel_label"] == "Historical panel label"
    assert (
        json.loads(captured[0]["documents"][0])["advisor_context"]["panel"]["label"]
        == "Historical panel label"
    )
