"""Server-side HTMX recovery protocol with isolated history and mocked providers."""

import json
from html.parser import HTMLParser
from unittest.mock import AsyncMock, Mock

import pytest

import main
from tests.test_routes import client, _get_csrf_token


class SaveButton(HTMLParser):
    def __init__(self):
        super().__init__()
        self.payload = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("hx-post") == "/save":
            self.payload = json.loads(values["hx-vals"])


def generate(client, monkeypatch):
    token = _get_csrf_token(client)
    monkeypatch.setattr(
        main,
        "query_experts",
        AsyncMock(
            return_value={
                "responses": [
                    {
                        "role": "agriculture",
                        "label": "Fictional advisor",
                        "response": "FINAL preserved qualification.",
                    }
                ]
            }
        ),
    )
    response = client.post(
        "/query",
        data={
            "query": "Fictional question",
            "roles": "agriculture",
            "csrf_token": token,
            "submission_key": "fixture",
        },
    )
    assert response.status_code == 200
    button = SaveButton()
    button.feed(response.text)
    return token, response, button.payload


def test_failed_save_retains_result_and_success_replaces_only_named_header(
    client, monkeypatch
):
    token, generated, payload = generate(client, monkeypatch)
    save = main.history_store.save_result
    monkeypatch.setattr(
        main.history_store,
        "save_result",
        Mock(side_effect=RuntimeError("private storage path and content")),
    )
    failed = client.post("/save", data=payload)
    assert failed.status_code == 503
    assert failed.headers["HX-Retarget"] == "#save-status"
    assert failed.headers["HX-Reswap"] == "innerHTML"
    assert "data-operation-error" in failed.text
    assert "private storage path" not in failed.text
    assert 'hx-post="/save"' in generated.text
    assert "FINAL preserved qualification" in generated.text
    monkeypatch.setattr(main.history_store, "save_result", save)
    saved = client.post("/save", data={**payload, "query": "tampering is ignored"})
    assert saved.status_code == 200
    assert saved.headers["HX-Retarget"] == ".responses-header"
    assert saved.headers["HX-Reswap"] == "outerHTML"
    assert saved.headers["HX-Trigger"] == "resultSaved"
    again = client.post("/save", data=payload)
    assert again.status_code == 200
    rows = main.history_store.get_history()
    assert len(rows) == 1
    result = main.history_store.get_result_by_id(rows[0]["id"])
    assert result["query"] == "Fictional question"
    assert (
        "FINAL preserved qualification" in client.get(f"/export/{rows[0]['id']}").text
    )


def test_malformed_save_has_truthful_error_and_no_database_write(client, monkeypatch):
    token = _get_csrf_token(client)
    save = Mock()
    monkeypatch.setattr(main.history_store, "save_result", save)
    response = client.post(
        "/save",
        data={
            "query": "Fictional question",
            "result_type": "roundtable",
            "roundtable_data": json.dumps(
                {"roles": ["agriculture", "climate"], "rounds": 1, "transcript": 42}
            ),
            "csrf_token": token,
        },
    )
    assert response.status_code == 400
    assert response.headers["HX-Retarget"] == "#save-status"
    save.assert_not_called()


def test_saved_retry_cannot_bypass_uncertain_remote_work_warning(client, monkeypatch):
    from fastapi.responses import HTMLResponse

    token = _get_csrf_token(client)
    key = main.history_store.save_result(
        "Fictional interrupted question",
        ["agriculture"],
        [
            {
                "role": "agriculture",
                "error": "A connection ended before completion was known",
            }
        ],
        execution_data={"execution_receipts": [{"status": "transport_uncertain"}]},
    )
    replay = client.get(f"/result/{key}")
    assert 'name="acknowledge"' in replay.text
    launch = AsyncMock(return_value=HTMLResponse("Fictional recovery prepared"))
    monkeypatch.setattr(main, "_launch", launch)
    blocked = client.post(f"/result/{key}/retry", data={"csrf_token": token})
    assert blocked.status_code == 400
    launch.assert_not_awaited()
    allowed = client.post(
        f"/result/{key}/retry", data={"csrf_token": token, "acknowledge": "true"}
    )
    assert allowed.status_code == 200
    assert launch.await_args.args[1]["parent_result_id"] == key
    assert "execution_receipts" not in launch.await_args.args[1]


@pytest.mark.parametrize(
    "data, status",
    [
        ({"query": "Fictional", "roles": "agriculture", "csrf_token": "bad"}, 403),
        ({"roles": "agriculture"}, 422),
    ],
)
def test_form_errors_are_html_with_preservation_targets(client, data, status):
    _get_csrf_token(client)
    response = client.post("/query", data=data)
    assert response.status_code == status
    assert "text/html" in response.headers["Content-Type"]
    assert response.headers["HX-Retarget"] == "#operation-status"


def test_rate_limit_is_html_and_retains_current_work(client, monkeypatch):
    token = _get_csrf_token(client)
    monkeypatch.setattr(
        main,
        "query_experts",
        AsyncMock(
            return_value={
                "responses": [{"role": "agriculture", "response": "Fictional"}]
            }
        ),
    )
    for _ in range(30):
        client.post(
            "/query",
            data={"query": "Fictional", "roles": "agriculture", "csrf_token": token},
        )
    response = client.post(
        "/query",
        data={"query": "Fictional", "roles": "agriculture", "csrf_token": token},
    )
    assert response.status_code == 429
    assert response.headers["HX-Retarget"] == "#operation-status"
    assert response.headers["Retry-After"] == "60"


def test_import_preview_does_not_write_saved_results_and_import_is_additive(
    client, monkeypatch
):
    token = _get_csrf_token(client)
    monkeypatch.setattr(
        main,
        "query_experts",
        AsyncMock(side_effect=AssertionError("No provider calls")),
    )
    archive = {
        "archive_format": "ai-advisors",
        "archive_version": 1,
        "records": [
            {
                "result": {
                    "id": "legacy01",
                    "query": "Imported fictional question",
                    "experts": ["agriculture"],
                    "responses": [
                        {"role": "agriculture", "response": "Preserve complete content"}
                    ],
                },
                "annotations": {"outcome": "Private fictional outcome"},
            }
        ],
    }
    preview = client.post(
        "/archive/preview",
        files={"file": ("fixture.json", json.dumps(archive), "application/json")},
        data={"csrf_token": token},
    )
    assert preview.status_code == 200
    assert main.history_store.get_history() == []
    key = preview.context["import_id"]
    assert (
        client.post(f"/archive/import/{key}", data={"csrf_token": token}).status_code
        == 200
    )
    assert (
        client.post(f"/archive/import/{key}", data={"csrf_token": token}).status_code
        == 200
    )
    assert len(main.history_store.get_history()) == 1
    assert client.get("/work/legacy01").status_code == 200
    assert "Private fictional outcome" not in client.get("/export/legacy01/json").text
    assert (
        "Private fictional outcome"
        in client.get("/export/legacy01/json?include_notes=true").text
    )
