"""Fictional regression fixtures for durability, boundaries, and lossless recovery.

Provider calls use MockTransport. Stores and backups stay inside pytest's tmp_path.
These checks do not establish browser, live-model, or owner acceptance.
"""

from __future__ import annotations

import asyncio
import copy
import json
import importlib
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import chromadb
import httpx
import pytest
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from lib.contracts import InvalidRecord, sources, validate_result
from lib.engine.config import Settings, get_settings
from lib.engine.execution import Execution, RunStopped, current_execution
from lib.engine.llm_client import LLMClient
from lib.experts import build_advisor_context
from lib.services.consensus_contracts import normalize_extensions
from lib.services.record_export import (
    archive_record,
    complete_markdown,
    validate_archive,
)
from lib.services.run_service import RunManager
from lib.services.workbench_service import (
    effort_comparison,
    reusable_asset,
    quality_cases,
)
from lib.storage import HistoryStore
from lib.storage.workspace_store import WorkspaceStore


def query_record() -> dict:
    return {
        "query": "Exact question? Preserve `units` and https://example.invalid/reference",
        "experts": ["agriculture"],
        "responses": [
            {
                "role": "agriculture",
                "label": "Captured advisor",
                "response": "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n\nFourth paragraph.\n\nFINAL QUALIFICATION: only after a supplied measurement. https://example.invalid/final\n```python\nx = 1\n```",
            }
        ],
        "result_type": "query",
        "advisor_context": build_advisor_context("agriculture", ["agriculture"]),
    }


@pytest.mark.parametrize(
    "content", [None, "", "   ", 7, [{"type": "image_url", "image_url": "unusable"}]]
)
@pytest.mark.asyncio
async def test_unusable_provider_output_is_never_success(content):
    client = LLMClient(
        "fictional", "https://provider.test/v1/chat/completions", "fictional-model"
    )
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": content}, "finish_reason": "stop"}
                    ]
                },
            )
        )
    )
    try:
        with pytest.raises(ValueError):
            await client.generate("Fictional question", "Fictional instructions")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_supported_blocks_and_truncation_have_distinct_outcomes():
    replies = iter(
        [
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "First\n"},
                                {"type": "text", "text": "Second"},
                            ]
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {"content": "A partial answer"},
                        "finish_reason": "length",
                    }
                ]
            },
        ]
    )
    client = LLMClient(
        "fictional", "https://provider.test/completions", "fictional-model"
    )
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=next(replies))
        )
    )
    try:
        assert await client.generate("Question", "Instructions") == "First\nSecond"
        with pytest.raises(ValueError, match="truncated"):
            await client.generate("Question", "Instructions")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_receipt_is_durable_before_dispatch_and_after_uncertain_transport():
    snapshots = []

    async def persist(state):
        snapshots.append(copy.deepcopy(state))

    execution = Execution({"query": "Fictional"}, persist)

    def lost_response(request):
        assert snapshots[-1]["execution_receipts"][0]["status"] == "in_flight"
        assert "Authorization" not in json.dumps(snapshots)
        raise httpx.ReadTimeout("private provider diagnostics", request=request)

    client = LLMClient(
        "fictional-secret", "https://provider.test/completions", "fictional-model"
    )
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(lost_response))
    token = current_execution.set(execution)
    try:
        with pytest.raises(httpx.ReadTimeout):
            await client.generate("Fictional content", "Instructions")
    finally:
        current_execution.reset(token)
        await client.close()
    receipt = snapshots[-1]["execution_receipts"][0]
    assert receipt["status"] == "transport_uncertain"
    assert len(receipt["request_sha256"]) == 64
    assert "fictional-secret" not in json.dumps(receipt)


@pytest.mark.asyncio
async def test_structured_nested_null_does_not_pass_schema():
    client = LLMClient(
        "fictional", "https://provider.test/completions", "fictional-model"
    )
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"finding":{"claim":null}}'}}]
                },
            )
        )
    )
    schema = {
        "type": "object",
        "required": ["finding"],
        "properties": {
            "finding": {
                "type": "object",
                "required": ["claim"],
                "properties": {"claim": {"type": "string"}},
            }
        },
    }
    try:
        with pytest.raises(ValueError, match="claim"):
            await client.generate_json(
                "Question", "Instructions", schema_name="fixture", schema=schema
            )
    finally:
        await client.close()


@pytest.mark.parametrize(
    "change",
    [
        {"responses": ["wrong shape"]},
        {"responses": [{"role": "agriculture", "response": None}]},
        {"result_type": "roundtable", "transcript": 42},
        {
            "result_type": "roundtable",
            "consensus_brief": {"recommendations": [{"action": None}]},
        },
        {
            "result_type": "roundtable",
            "consensus_brief": {"key_findings": [{"evidence_points": [None]}]},
        },
        {"schema_version": 999},
    ],
)
def test_invalid_records_fail_before_storage(change):
    with pytest.raises(InvalidRecord):
        validate_result({**query_record(), **change})


def test_complete_export_preserves_question_qualification_links_and_code():
    record = query_record()
    result = complete_markdown(record)
    assert record["query"] in result
    assert record["responses"][0]["response"] in result
    assert "FINAL QUALIFICATION" in result
    assert "https://example.invalid/final" in result
    assert "````text" in result
    assert "AI participant" in result
    assert "## Sources" not in result


def test_new_collection_saves_without_embedding_and_retry_is_idempotent(
    tmp_path, monkeypatch
):
    store = HistoryStore(str(tmp_path / "history"))
    original = Collection.add
    calls = []

    def add(collection, **kwargs):
        assert collection.name == "query_history_v3"
        assert collection._embedding_function is None
        assert kwargs["embeddings"] == [[0.0]]
        calls.append(kwargs)
        return original(collection, **kwargs)

    monkeypatch.setattr(Collection, "add", add)
    record = query_record()
    first = store.save_result(
        record["query"],
        record["experts"],
        record["responses"],
        advisor_context=record["advisor_context"],
        idempotency_key="same-submission",
    )
    second = store.save_result(
        record["query"],
        record["experts"],
        record["responses"],
        advisor_context=record["advisor_context"],
        idempotency_key="same-submission",
    )
    assert first == second and len(first) == 64
    assert len(calls) == 1
    assert complete_markdown(store.get_result_by_id(first))


def test_legacy_collection_is_read_without_migration(tmp_path):
    root = str(tmp_path / "legacy")
    client = chromadb.PersistentClient(
        path=root, settings=ChromaSettings(anonymized_telemetry=False)
    )
    legacy = client.create_collection("query_history", embedding_function=None)
    record = query_record()
    legacy.add(
        ids=["abcdef12"],
        embeddings=[[1.0, 2.0]],
        documents=[json.dumps(record)],
        metadatas=[
            {
                "query": record["query"],
                "experts": '["agriculture"]',
                "result_type": "query",
                "timestamp": "2026-01-01",
            }
        ],
    )
    before = legacy.get(include=["documents", "metadatas", "embeddings"])
    store = HistoryStore(root)
    assert store.get_result_by_id("abcdef12")["query"] == record["query"]
    after = legacy.get(include=["documents", "metadatas", "embeddings"])
    assert before["documents"] == after["documents"]
    assert before["metadatas"] == after["metadatas"]
    assert before["embeddings"].tolist() == after["embeddings"].tolist()
    assert store._collection.count() == 0


def test_forced_uuid_collision_cannot_alias_another_result(tmp_path, monkeypatch):
    store = HistoryStore(str(tmp_path / "history"))
    first = store.save_result(
        "First fictional question",
        ["agriculture"],
        [{"role": "agriculture", "response": "First answer"}],
    )
    identifiers = iter([first, "12345678-1234-1234-1234-123456789012"])
    module = importlib.import_module("lib.storage.history_store")
    monkeypatch.setattr(
        module, "uuid", SimpleNamespace(uuid4=lambda: next(identifiers))
    )
    second = store.save_result(
        "Second fictional question",
        ["agriculture"],
        [{"role": "agriculture", "response": "Second answer"}],
    )
    assert second != first
    assert store.get_result_by_id(first)["query"] == "First fictional question"
    assert store.get_result_by_id(second)["query"] == "Second fictional question"


def test_archive_round_trip_and_conflict_are_additive(tmp_path):
    first, second = HistoryStore(str(tmp_path / "first")), HistoryStore(
        str(tmp_path / "second")
    )
    record = query_record()
    key = first.save_result(
        record["query"],
        record["experts"],
        record["responses"],
        advisor_context=record["advisor_context"],
    )
    notes = first.update_annotations(
        key, {"outcome": "Fictional measured result", "outcome_rating": "helped"}
    )
    saved = first.get_result_by_id(key)
    row = validate_archive(archive_record(saved, notes))[0]
    imported = second.import_record(row["result"], row["annotations"])
    assert second.get_result_by_id(imported) == saved
    assert second.preview_import(row["result"]).startswith("Already present")

    assert second.get_annotations(imported) == notes
    second.update_annotations(imported, {"outcome": "Locally updated"})
    assert second.import_record(row["result"], row["annotations"]) == imported
    assert second.get_annotations(imported)["outcome"] == "Locally updated"
    changed = {**row["result"], "query": "A conflicting imported question"}
    assert second.preview_import(changed).startswith("Conflicting ID")
    new_id = second.import_record(changed, notes)
    assert new_id != imported
    assert second.get_result_by_id(imported) == saved


def test_import_without_id_is_idempotent_and_partial_notes_can_resume(
    tmp_path, monkeypatch
):
    store = HistoryStore(str(tmp_path / "history"))
    record = query_record()
    original = store.update_annotations
    monkeypatch.setattr(
        store,
        "update_annotations",
        Mock(side_effect=OSError("fictional interrupted notes write")),
    )
    with pytest.raises(OSError):
        store.import_record(record, {"outcome": "Keep this outcome"})
    assert len(store.get_history()) == 1
    monkeypatch.setattr(store, "update_annotations", original)
    key = store.import_record(record, {"outcome": "Keep this outcome"})
    assert store.get_annotations(key)["outcome"] == "Keep this outcome"
    assert len(store.get_history()) == 1


@pytest.mark.asyncio
async def test_checkpoint_survives_interruption_and_resume_requires_acknowledgment(
    tmp_path,
):
    workspace = WorkspaceStore(tmp_path)
    manager = RunManager(workspace)
    reached = asyncio.Event()

    async def interrupted(state):
        execution = current_execution.get()
        execution.receipts.append({"status": "in_flight"})
        await execution.checkpoint(
            {
                "responses": [
                    {"role": "agriculture", "response": "Completed before interruption"}
                ]
            }
        )
        reached.set()
        await asyncio.Event().wait()

    record = await manager.create(
        {"query": "Fictional", "roles": ["agriculture"], "result_type": "query"},
        interrupted,
        key="one",
    )
    await reached.wait()
    await manager.close()
    reopened = RunManager(workspace)
    recovered = await reopened.get(record["id"])
    assert recovered["status"] == "interrupted" and recovered["ambiguous"]
    assert (
        recovered["state"]["responses"][0]["response"]
        == "Completed before interruption"
    )
    executor = AsyncMock(return_value={"responses": recovered["state"]["responses"]})
    with pytest.raises(ValueError, match="Acknowledge"):
        await reopened.resume(record["id"], executor)
    executor.assert_not_awaited()
    await reopened.resume(record["id"], executor, acknowledge=True)
    await asyncio.gather(*list(reopened.tasks.values()))
    assert (await reopened.get(record["id"]))["status"] == "complete"


@pytest.mark.asyncio
async def test_duplicate_submission_does_not_dispatch_and_attempt_limit_is_enforced(
    tmp_path, monkeypatch
):
    manager = RunManager(WorkspaceStore(tmp_path))
    state = {"query": "Fictional", "roles": ["agriculture"], "result_type": "query"}
    executor = AsyncMock(
        return_value={
            "responses": [{"role": "agriculture", "error": "Fictional failure"}]
        }
    )
    first = await manager.create(
        copy.deepcopy(state), executor, key="same", background=False
    )
    second = await manager.create(
        copy.deepcopy(state), executor, key="same", background=False
    )
    assert first["id"] == second["id"]
    executor.assert_awaited_once()
    settings = copy.copy(get_settings())
    settings.max_run_attempts = 1
    monkeypatch.setattr("lib.services.run_service.get_settings", lambda: settings)
    with pytest.raises(ValueError, match="attempt limit"):
        await manager.resume(first["id"], executor)


@pytest.mark.asyncio
async def test_execution_budget_and_pause_prevent_additional_dispatch():
    execution = Execution({}, AsyncMock(), max_calls=1)
    execution.receipts.append({"status": "returned"})
    with pytest.raises(RunStopped, match="call limit"):
        execution.before_call()
    execution.paused = True
    with pytest.raises(RunStopped, match="Paused"):
        execution.before_call()


def test_source_ids_and_disagreements_resolve_only_to_captured_evidence():
    with pytest.raises(ValueError, match="not supplied"):
        normalize_extensions(
            {
                "claims": [
                    {
                        "claim": "Invented support",
                        "support": "supplied",
                        "source_ids": ["S9"],
                    }
                ]
            },
            {"S1"},
            set(),
        )
    with pytest.raises(ValueError, match="contribution that did not complete"):
        normalize_extensions(
            {
                "disagreements": [
                    {
                        "point": "Timing",
                        "viewpoints": ["First advisor suggests waiting"],
                        "check": "Inspect the supplied deadline",
                        "source_ids": [],
                        "turn_ids": ["R2/climate"],
                    }
                ]
            },
            set(),
            {"R1/climate"},
        )
    assert (
        sources([{"label": "Fictional", "passage": "A supplied observation"}])[0]["id"]
        == "S1"
    )


def test_reusable_inputs_and_effort_calculation_remain_deliberate():
    context = reusable_asset(
        "context", {"name": "My constraints", "background": "Fictional low-input task"}
    )
    assert context["background"] == "Fictional low-input task"
    result = effort_comparison(
        {
            "manual": "30",
            "setup": "5",
            "review": "7",
            "correction": "3",
            "recovery": "2",
        }
    )
    assert result["assisted"] == "17" and result["difference"] == "13"
    with pytest.raises(ValueError):
        effort_comparison({"manual": "NaN"})


def test_quality_pack_has_six_valid_distinct_fictional_cases():
    cases = quality_cases()
    assert len(cases) == len({case["id"] for case in cases}) == 6
    assert all(
        "fictional" in case["query"].lower() and case["expect"] for case in cases
    )


@pytest.mark.parametrize(
    "url,model,port",
    [
        ("", "model", 8123),
        ("https://user:password@provider.test", "model", 8123),
        ("http://remote.test", "model", 8123),
        ("https://provider.test", "", 8123),
        ("https://provider.test", "model", 0),
    ],
)
def test_invalid_settings_fail_without_provider_dispatch(url, model, port):
    with pytest.raises(ValueError):
        Settings("fictional", url, model, port, False).validate()


def test_stopped_backup_restore_preserves_private_data_in_new_directory(
    tmp_path, monkeypatch
):
    from lib import operations

    root = tmp_path / "project"
    root.mkdir()
    (root / "source.py").write_text("# fictional source\n")
    (root / ".env").write_text("FICTIONAL_PRIVATE=not-a-real-secret\n")
    history = root / "history"
    history.mkdir()
    (history / "fixture.txt").write_text("fictional saved answers and personal notes")
    monkeypatch.setattr(operations, "PROJECT_ROOT", root)
    monkeypatch.setattr(operations, "CONTROL", root / ".local-state" / "instance.json")
    monkeypatch.setattr(operations, "data_directory", lambda: history)
    monkeypatch.setattr(operations, "listening", lambda port: False)
    monkeypatch.setattr(
        operations.subprocess, "check_output", lambda *args, **kwargs: b"source.py\0"
    )
    snapshot = operations.backup(tmp_path / "snapshot")
    destination = tmp_path / "restored"
    operations.restore(snapshot, destination)
    assert (destination / "source" / "source.py").read_text() == (
        root / "source.py"
    ).read_text()
    assert (destination / "history" / "fixture.txt").read_text() == (
        history / "fixture.txt"
    ).read_text()
    assert (destination / "private.env").read_text() == (root / ".env").read_text()
    with pytest.raises(ValueError, match="never overlaid"):
        operations.restore(snapshot, destination)
    (snapshot / "history" / "fixture.txt").write_text("tampered")
    with pytest.raises(ValueError, match="integrity"):
        operations.restore(snapshot, tmp_path / "another")
    assert not (tmp_path / "another").exists()


def test_backup_refuses_live_process_before_copying(tmp_path, monkeypatch):
    from lib import operations

    monkeypatch.setattr(operations, "listening", lambda port: True)
    with pytest.raises(ValueError, match="Stop the app"):
        operations.backup(tmp_path / "must-not-exist")
    assert not (tmp_path / "must-not-exist").exists()
