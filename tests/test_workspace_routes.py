"""Trust-boundary and recovery checks for personal saved-work routes."""

import json
from html.parser import HTMLParser
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

import main
from lib.engine.config import get_settings
from lib.engine.llm_client import LLMClient
from lib.storage import HistoryStore
from lib.storage.history_store import ANNOTATION_FIELDS, ANNOTATION_LIMITS


class _FragmentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
        self.results = []
        self.paging = []
        self._textarea = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "input" and values.get("name"):
            self.fields[values["name"]] = values.get("value", "")
        if tag == "textarea" and values.get("name"):
            self._textarea = values["name"]
            self.fields[self._textarea] = ""
        if tag == "button" and values.get("hx-get", "").startswith("/result/"):
            self.results.append(values["hx-get"].removeprefix("/result/"))
        if tag == "button" and values.get("hx-get") == "/history":
            self.paging.append(json.loads(values["hx-vals"]))

    def handle_endtag(self, tag):
        if tag == "textarea":
            self._textarea = None

    def handle_data(self, data):
        if self._textarea is not None:
            self.fields[self._textarea] += data


def _parse(response):
    parser = _FragmentParser()
    parser.feed(response.text)
    return parser


@pytest.fixture
def workspace_client(tmp_path, monkeypatch):
    """Use isolated storage and make model access fail if a route attempts it."""
    monkeypatch.setenv("ALLOW_MISSING_API_KEY", "true")
    get_settings.cache_clear()
    store = HistoryStore(str(tmp_path / "workspace-history"))
    monkeypatch.setattr(main, "history_store", store)
    main.app.state.limiter._storage.reset()
    provider = AsyncMock()
    getter = Mock(return_value=provider)
    guards = {
        "client": getter,
        "query": AsyncMock(side_effect=AssertionError("Unexpected advisor query")),
        "roundtable": AsyncMock(side_effect=AssertionError("Unexpected roundtable")),
        "generate": AsyncMock(side_effect=AssertionError("Unexpected model call")),
        "generate_json": AsyncMock(side_effect=AssertionError("Unexpected model call")),
    }
    monkeypatch.setattr(main, "get_llm_client", getter)
    monkeypatch.setattr(main, "query_experts", guards["query"])
    monkeypatch.setattr(main, "run_roundtable", guards["roundtable"])
    monkeypatch.setattr(LLMClient, "generate", guards["generate"])
    monkeypatch.setattr(LLMClient, "generate_json", guards["generate_json"])
    with TestClient(main.app) as client:
        response = client.get("/")
        assert response.status_code == 200
        token = client.cookies.get("csrf_token")
        assert token
        yield client, store, token, guards
        # Check before lifespan's intentional client.close() at shutdown.
        for guard in guards.values():
            guard.assert_not_called()
    main.app.state.limiter._storage.reset()


def _seed(store, count=1, result_type="query"):
    ids = [f"workspace-{index:03}" for index in range(count)]
    documents = []
    metadata = []
    for index in range(count):
        document = {
            "query": f"Question {index}",
            "experts": ["agriculture"],
            "responses": [
                {
                    "role": "agriculture",
                    "label": "Agricultural Science Expert",
                    "response": "Original advisor answer.",
                }
            ],
            "result_type": result_type,
            "timestamp": "2026-10-16T12:00:00",
        }
        if result_type == "roundtable":
            document.update(
                {
                    "rounds": 1,
                    "transcript": [
                        {
                            "role": "agriculture",
                            "speaker": "Agricultural Science Expert",
                            "round": 1,
                            "status": "success",
                            "text": "Original advisor answer.",
                        }
                    ],
                    "final_answer": "Original synthesis.",
                }
            )
        documents.append(json.dumps(document))
        metadata.append(
            {
                "query": document["query"],
                "experts": json.dumps(document["experts"]),
                "result_type": result_type,
                "timestamp": document["timestamp"],
                **({"panel_label": "Effort review"} if index == 0 else {}),
            }
        )
    store._collection.add(
        ids=ids,
        embeddings=[[0.0] for _ in ids],
        documents=documents,
        metadatas=metadata,
    )
    return ids


def test_history_search_finds_old_notes_panel_and_pages_all_matches(workspace_client):
    client, store, _, _ = workspace_client
    ids = _seed(store, 25)
    store.update_annotations(ids[0], {"title": "Resume the door project"})

    found = client.get("/history", params={"q": "DOOR"})
    panel = client.get("/history", params={"q": "EFFORT REVIEW"})
    first = client.get("/history", params={"q": "Question", "offset": 0})
    second = client.get("/history", params={"q": "Question", "offset": 10})
    final = client.get("/history", params={"q": "Question", "offset": 20})

    assert all(
        response.status_code == 200 for response in (found, panel, first, second, final)
    )
    assert _parse(found).results == _parse(panel).results == [ids[0]]
    assert _parse(first).results == list(reversed(ids[15:25]))
    assert _parse(second).results == list(reversed(ids[5:15]))
    assert _parse(final).results == list(reversed(ids[:5]))
    assert _parse(first).paging == [{"q": "Question", "offset": 10}]
    assert _parse(second).paging == [
        {"q": "Question", "offset": 0},
        {"q": "Question", "offset": 20},
    ]
    assert _parse(final).paging == [{"q": "Question", "offset": 10}]


def test_resume_uses_saved_notes_and_only_explicit_unfinished_items(workspace_client):
    client, store, _, _ = workspace_client
    ids = _seed(store, 20)
    notes = {
        "title": "My return point",
        "status": "decided",
        "next_step": "Dictate the next assignment",
        "last_step": "Saved the reviewed draft",
        "blocker": "Waiting for source evidence",
        "outcome": "Fewer recovery steps",
    }
    store.update_annotations(ids[19], notes)
    store.update_annotations(ids[0], {"status": "waiting", "title": "Old waiting item"})
    store.update_annotations(
        ids[1], {"status": "undecided", "title": "Old undecided item"}
    )
    store.update_annotations(ids[18], {"status": "tried"})

    response = client.get("/resume", params={"result_id": ids[19]})

    assert response.status_code == 200
    assert all(
        response.context["resume_result"][field] == value
        for field, value in notes.items()
    )
    assert [item["id"] for item in response.context["unfinished"]] == [ids[1], ids[0]]
    assert f'data-resume-result-id="{ids[19]}"' in response.text


def test_missing_resume_returns_forget_marker(workspace_client):
    client, _, _, _ = workspace_client
    response = client.get("/resume", params={"result_id": "missing-record"})
    assert response.status_code == 200
    assert 'data-forget-result-id="missing-record"' in response.text
    assert response.context["resume_result"] is None


@pytest.mark.parametrize("result_type", ["query", "roundtable"])
def test_notes_replay_and_exports_never_rewrite_source_or_call_models(
    workspace_client, result_type
):
    client, store, csrf, _ = workspace_client
    result_id = _seed(store, result_type=result_type)[0]
    source_before = store._collection.get(
        ids=[result_id], include=["documents", "metadatas"]
    )
    export_paths = (f"/export/{result_id}", f"/export/{result_id}/brief")
    exports_before = [client.get(path) for path in export_paths]
    attempted = {
        "title": '"><script data-workspace-probe>title</script>',
        "status": "waiting",
        "next_step": "</textarea><script data-workspace-probe>step</script>&next",
        "last_step": "Saved the source",
        "blocker": "A human observation",
        "outcome": "Personal result marker: lower effort",
        "outcome_rating": "",
    }

    saved = client.post(
        f"/result/{result_id}/notes", data={**attempted, "csrf_token": csrf}
    )
    replay = client.get(f"/result/{result_id}")
    resume = client.get("/resume", params={"result_id": result_id})
    history = client.get("/history", params={"q": "Personal result marker"})
    exports_after = [client.get(path) for path in export_paths]

    assert all(
        response.status_code == 200
        for response in (
            *exports_before,
            saved,
            replay,
            resume,
            history,
            *exports_after,
        )
    )
    assert saved.headers["HX-Trigger"] == "resultSaved"
    assert store.get_annotations(result_id) == attempted
    for response in (saved, replay):
        parsed = _parse(response)
        for field in ("title", "next_step", "last_step", "blocker", "outcome"):
            assert parsed.fields[field] == attempted[field]
        assert "<script data-workspace-probe>" not in response.text
    assert _parse(history).results == [result_id]
    assert "<script data-workspace-probe>" not in resume.text
    assert [response.content for response in exports_after] == [
        response.content for response in exports_before
    ]
    assert (
        store._collection.get(ids=[result_id], include=["documents", "metadatas"])
        == source_before
    )


@pytest.mark.parametrize(
    ("failure", "expected_status"),
    [("csrf", 403), ("missing", 404), ("invalid", 400), ("storage", 503)],
)
def test_notes_failures_preserve_attempted_dictation_in_same_fragment(
    workspace_client, monkeypatch, failure, expected_status
):
    client, store, csrf, _ = workspace_client
    result_id = _seed(store)[0]
    old = store.update_annotations(result_id, {"title": "Previously saved"})
    attempted = dict.fromkeys(ANNOTATION_FIELDS, "")
    attempted.update(
        {
            "title": "My dictated title & continuation",
            "next_step": "Do not lose this dictated next action <later>",
            "status": "waiting",
        }
    )
    if failure == "csrf":
        csrf = "invalid-token"
    elif failure == "missing":
        result_id = "missing-record"
    elif failure == "invalid":
        attempted["title"] = "x" * (ANNOTATION_LIMITS["title"] + 1)
    elif failure == "storage":
        monkeypatch.setattr(
            store,
            "update_annotations",
            Mock(side_effect=RuntimeError("Private storage details must stay private")),
        )

    response = client.post(
        f"/result/{result_id}/notes", data={**attempted, "csrf_token": csrf}
    )

    assert response.status_code == expected_status
    assert 'class="card personal-notes"' in response.text
    assert 'role="alert"' in response.text
    assert "HX-Trigger" not in response.headers
    for field in ("title", "next_step", "last_step", "blocker", "outcome"):
        assert _parse(response).fields[field] == attempted[field]
    assert "Private storage details" not in response.text
    assert store.get_annotations("workspace-000") == old


def test_notes_optional_fields_default_to_blank(workspace_client):
    client, store, csrf, _ = workspace_client
    result_id = _seed(store)[0]
    response = client.post(f"/result/{result_id}/notes", data={"csrf_token": csrf})
    assert response.status_code == 200
    assert store.get_annotations(result_id) == dict.fromkeys(ANNOTATION_FIELDS, "")
