"""AI Advisors - FastAPI Application."""

import json
import asyncio
import uuid
import os
from pathlib import Path
import logging
import secrets
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.exceptions import RequestValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from lib.engine.config import get_settings, PROJECT_ROOT
from lib.contracts import InvalidRecord, MODEL_ID, fingerprint, validate_result
from lib.services.run_service import RunManager
from lib.services.record_export import (
    complete_markdown,
    archive_record,
    validate_archive,
)
from lib.services.workbench_service import (
    reusable_asset,
    effort_comparison,
    quality_cases,
)
from lib.engine.llm_client import get_llm_client
from lib.experts import (
    DEFAULT_PANEL_ID,
    build_advisor_context,
    get_all_experts,
    get_all_panels,
    get_panel,
)
from lib.experts.catalog import validate_advisor_context
from lib.services import (
    build_executive_brief_html,
    build_executive_brief_markdown,
    query_experts,
    run_roundtable,
    retry_roundtable,
)
from lib.services.roundtable_state import roundtable_view
from lib.services.result_view import history_page, result_summary
from lib.storage import history_store
from lib.storage.history_store import ANNOTATION_STATUSES
from lib.utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
CSRF_COOKIE_NAME = "csrf_token"
ROUNDTABLE_ROUND_OPTIONS = (1, 2, 3, 4, 5)


def _get_or_create_csrf_token(request: Request) -> str:
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        token = secrets.token_urlsafe(32)
    return token


def _validate_csrf(request: Request, csrf_token: str) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    return bool(cookie_token and csrf_token and cookie_token == csrf_token)


def _normalize_rounds(rounds: int) -> int:
    """Clamp roundtable rounds to the supported UI range."""
    return max(ROUNDTABLE_ROUND_OPTIONS[0], min(rounds, ROUNDTABLE_ROUND_OPTIONS[-1]))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    get_settings()
    logger.info("AI Advisors started successfully")
    try:
        yield
    finally:
        manager = getattr(app.state, "run_manager", None)
        if manager is not None:
            await manager.close()
        await get_llm_client().close()


# Initialize FastAPI
app = FastAPI(
    title="AI Advisors",
    description="Configurable AI advisor panels powered by LLMs",
    version="2.1.0",
    lifespan=lifespan,
)

# Add rate limiting middleware and exception handler
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))


async def _store(name: str, *args, **kwargs):
    """Resolve the lazy store and run blocking database work off the event loop."""
    return await asyncio.to_thread(
        lambda: getattr(history_store, name)(*args, **kwargs)
    )


async def _manager() -> RunManager:
    workspace = await asyncio.to_thread(lambda: history_store.workspace)
    manager = getattr(app.state, "run_manager", None)
    if manager is None or manager.workspace.path != workspace.path:
        manager = RunManager(workspace)
        app.state.run_manager = manager
    return manager


def _error(
    request: Request, message: str, status: int = 400, target: str = "#operation-status"
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "partials/error.html",
        {"message": message},
        status_code=status,
        headers={"HX-Retarget": target, "HX-Reswap": "innerHTML"},
    )


def _unexpected(
    request: Request,
    operation: str,
    error: Exception,
    target: str = "#operation-status",
) -> HTMLResponse:
    reference = uuid.uuid4().hex[:12]
    logger.error(
        "%s failed; reference=%s type=%s", operation, reference, type(error).__name__
    )
    return _error(
        request,
        f"{operation} could not finish. Your input and completed work are retained. Try again when available. Reference: {reference}.",
        503,
        target,
    )


@app.exception_handler(RequestValidationError)
async def form_validation_error(
    request: Request, error: RequestValidationError
) -> HTMLResponse:
    return _error(
        request,
        "Check the required fields and number formats. Your current work is retained.",
        422,
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_error(request: Request, error: RateLimitExceeded) -> HTMLResponse:
    response = _error(
        request,
        "Too many requests. Your work is retained; wait a minute before retrying.",
        429,
    )
    response.headers["Retry-After"] = "60"
    return response


async def _execute_state(state: dict) -> dict:
    if state["result_type"] == "query":
        return await query_experts(state["query"], state["roles"])
    if state.get("transcript"):
        return await retry_roundtable(state)
    return await run_roundtable(
        state["query"],
        state["roles"],
        state["rounds"],
        advisor_context=state.get("advisor_context"),
    )


def _generated(request: Request, state: dict) -> HTMLResponse:
    context = {
        **state,
        "result_id": None,
        "csrf_token": _get_or_create_csrf_token(request),
        "result_summary": result_summary(state),
        "result_payload": state,
        "save_key": state.get("run_id") or fingerprint(state),
    }
    if state["result_type"] == "roundtable":
        context.update(roundtable_view(state))
    return templates.TemplateResponse(
        request,
        (
            "partials/roundtable.html"
            if state["result_type"] == "roundtable"
            else "partials/responses.html"
        ),
        context,
    )


async def _launch(
    request: Request, state: dict, background: bool, key: str, acknowledge: bool = False
) -> HTMLResponse:
    manager = await _manager()
    record = await manager.create(
        state, _execute_state, key=key, background=background, acknowledge=acknowledge
    )
    if background:
        return templates.TemplateResponse(
            request,
            "partials/run.html",
            {"run": record, "csrf_token": _get_or_create_csrf_token(request)},
        )
    if record.get("error") and not (
        record["state"].get("responses") or record["state"].get("transcript")
    ):
        return _error(
            request,
            record["error"] + " Open Working runs to recover this attempt.",
            503,
        )
    return _generated(request, record["state"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, result_id: str = "") -> HTMLResponse:
    """Render the main application page."""
    try:
        csrf_token = _get_or_create_csrf_token(request)
        experts = get_all_experts()
        response = templates.TemplateResponse(
            request,
            "index.html",
            {
                "experts": experts,
                "panels": get_all_panels(),
                "panel": get_panel(DEFAULT_PANEL_ID),
                "csrf_token": csrf_token,
                "suggested_queries": get_panel(DEFAULT_PANEL_ID).suggested_queries,
                "round_options": ROUNDTABLE_ROUND_OPTIONS,
                "initial_result_id": (
                    result_id
                    if result_id
                    and len(result_id) <= 80
                    and all(c.isalnum() or c in "-_" for c in result_id)
                    else ""
                ),
                "configured_models": {
                    "advisor": get_settings().openrouter_model,
                    "synthesis": get_settings().openrouter_synthesis_model
                    or get_settings().openrouter_model,
                },
                "run_limits": {
                    "calls": get_settings().max_run_calls,
                    "seconds": get_settings().max_run_seconds,
                    "output": get_settings().max_output_tokens,
                },
            },
        )
        if CSRF_COOKIE_NAME not in request.cookies:
            response.set_cookie(
                CSRF_COOKIE_NAME,
                csrf_token,
                samesite="lax",
                httponly=True,
            )
        return response
    except Exception as e:
        logger.error("Index load failed (%s)", type(e).__name__)
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "message": "Failed to load application.",
                "details": "Use the local operation reference if this repeats.",
            },
            status_code=500,
        )


@app.post("/query", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def query(
    request: Request,
    query: str = Form(...),
    roles: List[str] = Form(default=[]),
    csrf_token: str = Form(...),
    panel_id: str = Form(default=DEFAULT_PANEL_ID),
    task_brief: str = Form(default="{}"),
    sources: str = Form(default="[]"),
    background: bool = Form(default=False),
    submission_key: str = Form(default=""),
    advisor_model: str = Form(default=""),
    synthesis_model: str = Form(default=""),
    parent_result_id: str = Form(default=""),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(
            request,
            "Invalid CSRF token. Refresh this page; your local draft will remain available.",
            403,
        )
    try:
        if not roles:
            raise ValueError("Please select at least one expert.")
        if not query.strip():
            raise ValueError("Please enter a query.")
        for model in (advisor_model, synthesis_model):
            if model and not MODEL_ID.fullmatch(model):
                raise ValueError("Use a valid configured provider model ID.")
        state = {
            "query": query,
            "roles": roles,
            "result_type": "query",
            "advisor_context": build_advisor_context(panel_id, roles),
            "task_brief": json.loads(task_brief),
            "sources": json.loads(sources),
            "advisor_model": advisor_model,
            "synthesis_model": synthesis_model,
            "parent_result_id": parent_result_id,
        }
        return await _launch(request, state, background, submission_key)
    except (ValueError, TypeError) as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Query", error)


@app.post("/roundtable", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def roundtable(
    request: Request,
    query: str = Form(...),
    roles: List[str] = Form(default=[]),
    rounds: int = Form(default=3),
    csrf_token: str = Form(...),
    panel_id: str = Form(default=DEFAULT_PANEL_ID),
    task_brief: str = Form(default="{}"),
    sources: str = Form(default="[]"),
    background: bool = Form(default=False),
    submission_key: str = Form(default=""),
    advisor_model: str = Form(default=""),
    synthesis_model: str = Form(default=""),
    parent_result_id: str = Form(default=""),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(
            request,
            "Invalid CSRF token. Refresh this page; your local draft will remain available.",
            403,
        )
    try:
        if len(roles) < 2:
            raise ValueError("Roundtable requires at least 2 experts.")
        if not query.strip():
            raise ValueError("Please enter a query.")
        for model in (advisor_model, synthesis_model):
            if model and not MODEL_ID.fullmatch(model):
                raise ValueError("Use a valid configured provider model ID.")
        state = {
            "query": query,
            "roles": roles,
            "rounds": _normalize_rounds(rounds),
            "result_type": "roundtable",
            "advisor_context": build_advisor_context(panel_id, roles),
            "task_brief": json.loads(task_brief),
            "sources": json.loads(sources),
            "advisor_model": advisor_model,
            "synthesis_model": synthesis_model,
            "parent_result_id": parent_result_id,
        }
        return await _launch(request, state, background, submission_key)
    except (ValueError, TypeError) as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Roundtable", error)


@app.post("/roundtable/retry", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def retry_roundtable_result(
    request: Request,
    state: str = Form(...),
    csrf_token: str = Form(...),
    background: bool = Form(default=False),
    acknowledge: bool = Form(default=False),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(
            request,
            "Invalid CSRF token. Reload the saved result and try again.",
            403,
            "#roundtable-retry-status",
        )
    try:
        value = json.loads(state)
        from lib.services.roundtable_state import normalize_roundtable_state

        value = normalize_roundtable_state(value)
        value["result_type"] = "roundtable"
        value.pop("run_id", None)
        return await _launch(request, value, background, "", acknowledge=acknowledge)
    except (ValueError, TypeError) as error:
        return _error(request, str(error), 400, "#roundtable-retry-status")
    except Exception as error:
        return _unexpected(request, "Retry", error, "#roundtable-retry-status")


@app.get("/history", response_class=HTMLResponse)
async def get_history(
    request: Request,
    q: str = "",
    offset: int = 0,
    panel: str = "",
    status: str = "",
    tag: str = "",
    archived: bool = False,
    after: str = "",
    before: str = "",
) -> HTMLResponse:
    """Get saved query history."""
    try:
        q, offset = q.strip()[:300], max(0, offset)
        filters = {
            "panel": panel,
            "statuses": (status,) if status else None,
            "tag": tag,
            "archived": archived,
            "after": after,
            "before": before,
        }
        history = await _store(
            "get_history", limit=11, search=q, offset=offset, **filters
        )
        return templates.TemplateResponse(
            request, "partials/history_list.html", history_page(history, q, offset)
        )
    except Exception as e:
        logger.error("History read failed (%s)", type(e).__name__)
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "message": "Failed to load history.",
                "details": "Use the local operation reference if this repeats.",
            },
            status_code=500,
        )


@app.get("/resume", response_class=HTMLResponse)
async def resume_saved_work(request: Request, result_id: str = "") -> HTMLResponse:
    """Offer existing work without retrying or submitting a provider request."""
    try:
        result = await _store("get_result_by_id", result_id) if result_id else None
        if result is not None:
            result = {**result, **await _store("get_annotations", result_id)}
        return templates.TemplateResponse(
            request,
            "partials/resume.html",
            {
                "resume_result": result,
                "resume_missing_id": result_id if result_id and result is None else "",
                "unfinished": await _store("get_open_items", limit=3),
            },
        )
    except Exception:
        logger.error("Resume lookup failed")
        return templates.TemplateResponse(
            request,
            "partials/resume.html",
            {
                "resume_result": None,
                "unfinished": [],
                "resume_error": "Saved work could not be loaded. Try Saved Results again when storage is available.",
            },
        )


@app.get("/result/{result_id}", response_class=HTMLResponse)
async def get_result(request: Request, result_id: str) -> HTMLResponse:
    """Get a saved result by ID."""
    try:
        result = await _store("get_result_by_id", result_id)
        csrf_token = _get_or_create_csrf_token(request)

        if not result:
            return templates.TemplateResponse(
                request,
                "partials/missing_result.html",
                {"result_id": result_id},
                status_code=404,
            )

        workspace = (await _manager()).workspace
        organization = (
            await asyncio.to_thread(workspace.get, "organization", result_id) or {}
        )
        personal_context = {
            "organization": organization,
            "annotations": await _store("get_annotations", result_id),
            "annotation_statuses": ANNOTATION_STATUSES,
            "result_summary": result_summary(result),
            "result_payload": result,
            "sources": result.get("sources", []),
            "task_brief": result.get("task_brief", {}),
        }
        if result.get("result_type") == "roundtable":
            response = templates.TemplateResponse(
                request,
                "partials/roundtable.html",
                {
                    **roundtable_view({**result, "roles": result.get("experts", [])}),
                    **personal_context,
                    "result_id": result_id,
                    "csrf_token": csrf_token,
                },
            )
        else:
            response = templates.TemplateResponse(
                request,
                "partials/responses.html",
                {
                    "query": result["query"],
                    "responses": result.get("responses", []),
                    "advisor_context": result.get("advisor_context"),
                    **personal_context,
                    "result_id": result_id,
                    "csrf_token": csrf_token,
                },
            )
        if CSRF_COOKIE_NAME not in request.cookies:
            response.set_cookie(
                CSRF_COOKIE_NAME, csrf_token, samesite="lax", httponly=True
            )
        return response
    except InvalidRecord as error:
        return _error(request, str(error), 422)
    except Exception as e:
        logger.error("Result read failed (%s)", type(e).__name__)
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "message": "Failed to load result.",
                "details": "Use the local operation reference if this repeats.",
            },
            status_code=500,
        )


@app.post("/result/{result_id}/notes", response_class=HTMLResponse)
async def update_personal_notes(
    request: Request,
    result_id: str,
    title: str = Form(default=""),
    status: str = Form(default=""),
    next_step: str = Form(default=""),
    last_step: str = Form(default=""),
    blocker: str = Form(default=""),
    outcome: str = Form(default=""),
    outcome_rating: str = Form(default=""),
    csrf_token: str = Form(default=""),
) -> HTMLResponse:
    """Save optional user annotations separately, retaining submitted text on failure."""
    annotations = {
        "title": title,
        "status": status,
        "next_step": next_step,
        "last_step": last_step,
        "blocker": blocker,
        "outcome": outcome,
        "outcome_rating": outcome_rating,
    }
    context = {
        "result_id": result_id,
        "annotations": annotations,
        "annotation_statuses": ANNOTATION_STATUSES,
        "csrf_token": _get_or_create_csrf_token(request),
    }
    status_code = 200
    try:
        if not _validate_csrf(request, csrf_token):
            context["notes_error"] = (
                "Your session changed. Your notes are still here; try Save notes again."
            )
            status_code = 403
        elif await _store("get_result_by_id", result_id) is None:
            context["notes_error"] = (
                "The saved result is no longer available. Your entered notes have not been discarded."
            )
            status_code = 404
        else:
            context["annotations"] = await _store(
                "update_annotations", result_id, annotations
            )
            context["notes_saved"] = True
    except ValueError as error:
        context["notes_error"] = str(error)
        status_code = 400
    except Exception:
        logger.error("Personal note save failed for result %s", result_id)
        context["notes_error"] = (
            "Notes could not be saved. Your entered text is kept here; retry when storage is available."
        )
        status_code = 503
    response = templates.TemplateResponse(
        request,
        "partials/personal_notes.html",
        context,
        status_code=status_code,
        headers={"HX-Trigger": "resultSaved"} if status_code == 200 else None,
    )
    if CSRF_COOKIE_NAME not in request.cookies:
        response.set_cookie(
            CSRF_COOKIE_NAME, context["csrf_token"], samesite="lax", httponly=True
        )
    return response


@app.post("/save", response_class=HTMLResponse)
async def save_result(
    request: Request,
    query: str = Form(default=""),
    result_type: str = Form(default="query"),
    responses: Optional[str] = Form(default=None),
    roundtable_data: Optional[str] = Form(default=None),
    csrf_token: str = Form(...),
    advisor_context: Optional[str] = Form(default=None),
    run_id: str = Form(default=""),
    save_key: str = Form(default=""),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(
            request,
            "Invalid CSRF token. Refresh before retrying Save; your question draft remains available.",
            403,
            "#save-status",
        )
    try:
        if run_id:
            record = await (await _manager()).get(run_id)
            if record["status"] in ("running", "queued"):
                raise ValueError("Pause the run before saving its current checkpoint.")
            data = dict(record["state"])
            data["experts"] = data["roles"]
            data.update(
                run_status=record["status"],
                run_error=record.get("error", ""),
                attempts=record["attempts"],
            )
        elif result_type == "roundtable" and roundtable_data:
            data = json.loads(roundtable_data)
            if not isinstance(data, dict):
                raise ValueError("Roundtable data must be an object.")
            data.update(
                query=query, result_type="roundtable", experts=data.get("roles", [])
            )
        elif result_type == "query" and responses:
            entries = json.loads(responses)
            if not isinstance(entries, list) or any(
                not isinstance(item, dict) for item in entries
            ):
                raise ValueError("Responses must be a list of advisor records.")
            data = {
                "query": query,
                "result_type": "query",
                "responses": entries,
                "experts": [item.get("role") for item in entries],
            }
        else:
            raise ValueError("No valid result data to save.")
        if advisor_context and not run_id:
            data["advisor_context"] = json.loads(advisor_context)
        data = validate_result(data)
        extra = {}
        if data.get("advisor_context") is not None:
            extra["advisor_context"] = data["advisor_context"]
        if run_id:
            extra.update(execution_data=data, idempotency_key=run_id)
        elif save_key:
            extra["idempotency_key"] = save_key
        if data["result_type"] == "roundtable":
            roundtable_payload = {
                key: value
                for key, value in data.items()
                if key not in {"query", "experts", "result_type", "schema_version"}
            }
            result_id = await _store(
                "save_result",
                query=data["query"],
                experts=data["experts"],
                responses=[],
                result_type="roundtable",
                roundtable_data=roundtable_payload,
                **extra,
            )
        else:
            result_id = await _store(
                "save_result",
                query=data["query"],
                experts=data["experts"],
                responses=data.get("responses", []),
                result_type="query",
                **extra,
            )
        response = templates.TemplateResponse(
            request,
            "partials/save_success.html",
            {
                "result_id": result_id,
                "query": data["query"],
                "result_type": data["result_type"],
                "rounds": data.get("rounds", 0),
                "num_experts": len(data["experts"]),
            },
            headers={
                "HX-Trigger": "resultSaved",
                "HX-Retarget": (
                    ".roundtable-header"
                    if data["result_type"] == "roundtable"
                    else ".responses-header"
                ),
                "HX-Reswap": "outerHTML",
            },
        )
        return response
    except (ValueError, TypeError) as error:
        return _error(request, str(error), 400, "#save-status")
    except Exception as error:
        return _unexpected(request, "Save", error, "#save-status")


@app.get("/export/{result_id}")
async def export_result(request: Request, result_id: str) -> Response:
    """Export a saved result as markdown."""
    try:
        result = await _store("get_result_by_id", result_id)
        if not result:
            return templates.TemplateResponse(
                request,
                "404.html",
                {"message": "Saved result not found.", "result_id": result_id},
                status_code=404,
            )
        markdown = complete_markdown(result)

        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=advisor-query-{result_id}.md"
            },
        )
    except Exception as e:
        logger.error("Export failed (%s)", type(e).__name__)
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "message": "Failed to export result.",
                "details": "Use the local operation reference if this repeats.",
            },
            status_code=500,
        )


@app.get("/export/{result_id}/brief", response_class=HTMLResponse)
async def export_result_brief(request: Request, result_id: str) -> HTMLResponse:
    """Render a saved result as an executive brief."""
    try:
        result = await _store("get_result_by_id", result_id)
        if not result:
            return templates.TemplateResponse(
                request,
                "partials/error.html",
                {"message": "Result not found."},
                status_code=404,
            )

        html = build_executive_brief_html(result)
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error("Brief failed (%s)", type(e).__name__)
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "message": "Failed to build executive brief.",
                "details": "Use the local operation reference if this repeats.",
            },
            status_code=500,
        )


@app.get("/local-status")
async def local_status() -> dict:
    return {
        "application": "AI Advisors",
        "version": app.version,
        "pid": os.getpid(),
        "instance": os.getenv("AI_ADVISORS_INSTANCE", "unmanaged"),
    }


@app.get("/work/{result_id}", response_class=HTMLResponse)
async def open_saved_work(request: Request, result_id: str) -> HTMLResponse:
    return await index(request, result_id)


@app.get("/runs", response_class=HTMLResponse)
async def recent_runs(request: Request) -> HTMLResponse:
    try:
        return templates.TemplateResponse(
            request, "partials/runs.html", {"runs": await (await _manager()).recent()}
        )
    except Exception as error:
        return _unexpected(request, "Working runs", error)


@app.get("/runs/{run_id}", response_class=HTMLResponse)
async def working_run(request: Request, run_id: str) -> HTMLResponse:
    try:
        record = await (await _manager()).get(run_id)
        state = record["state"]
        record["completed"] = (
            sum(
                item.get("status", "success") == "success"
                for item in state.get("transcript", [])
            )
            if state["result_type"] == "roundtable"
            else sum(
                bool(item.get("response")) and not item.get("error")
                for item in state.get("responses", [])
            )
        )
        rendered = (
            _generated(
                request,
                {**state, "_running": record["status"] in ("running", "queued")},
            ).body.decode()
            if state.get("responses") or state.get("transcript")
            else ""
        )
        return templates.TemplateResponse(
            request,
            "partials/run.html",
            {
                "run": record,
                "rendered_result": rendered,
                "csrf_token": _get_or_create_csrf_token(request),
            },
        )
    except ValueError as error:
        return _error(request, str(error), 404)
    except Exception as error:
        return _unexpected(request, "Working run", error)


@app.post("/runs/{run_id}/pause", response_class=HTMLResponse)
async def pause_run(
    request: Request, run_id: str, csrf_token: str = Form(...)
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        manager = await _manager()
        await manager.get(run_id)
        manager.pause(run_id)
        return await working_run(request, run_id)
    except ValueError as error:
        return _error(request, str(error), 404)
    except Exception as error:
        return _unexpected(request, "Pause", error)


@app.post("/runs/{run_id}/resume", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def resume_run(
    request: Request,
    run_id: str,
    csrf_token: str = Form(...),
    acknowledge: bool = Form(default=False),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        await (await _manager()).resume(run_id, _execute_state, acknowledge=acknowledge)
        return await working_run(request, run_id)
    except ValueError as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Resume", error)


@app.get("/library", response_class=HTMLResponse)
async def personal_library(request: Request) -> HTMLResponse:
    try:
        manager = await _manager()
        starters, contexts, history = await asyncio.gather(
            asyncio.to_thread(manager.workspace.list, "starter"),
            asyncio.to_thread(manager.workspace.list, "context"),
            _store("get_history", limit=100),
        )
        return templates.TemplateResponse(
            request,
            "partials/library.html",
            {
                "starters": starters,
                "contexts": contexts,
                "quality_cases": quality_cases(),
                "saved_choices": history,
                "csrf_token": _get_or_create_csrf_token(request),
            },
        )
    except Exception as error:
        return _unexpected(request, "Personal library", error)


@app.post("/library/{kind}", response_class=HTMLResponse)
async def save_personal_asset(
    request: Request,
    kind: str,
    name: str = Form(...),
    content: str = Form(...),
    panel_id: str = Form(default=DEFAULT_PANEL_ID),
    roles: List[str] = Form(default=[]),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        asset = reusable_asset(
            kind,
            {
                "name": name,
                "query": content,
                "background": content,
                "panel_id": panel_id,
                "roles": roles,
            },
        )
        manager = await _manager()
        await asyncio.to_thread(manager.workspace.put, kind, asset["id"], asset)
        return await personal_library(request)
    except ValueError as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Save reusable text", error)


@app.post("/source/excerpt", response_class=HTMLResponse)
async def source_excerpt(
    request: Request, file: UploadFile = File(...), csrf_token: str = Form(...)
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        if Path(file.filename or "").suffix.lower() not in (".txt", ".md"):
            raise ValueError("Choose a UTF-8 text or Markdown file.")
        data = await file.read(100001)
        if len(data) > 100000:
            raise ValueError("Choose a file below 100 KB, or supply a smaller excerpt.")
        passage = data.decode("utf-8-sig")
        return templates.TemplateResponse(
            request,
            "partials/excerpt.html",
            {
                "label": Path(file.filename or "Source").name,
                "passage": passage,
                "csrf_token": csrf_token,
            },
        )
    except (ValueError, UnicodeError) as error:
        return _error(request, str(error))
    finally:
        await file.close()


@app.get("/followup/{result_id}", response_class=HTMLResponse)
async def followup_form(request: Request, result_id: str) -> HTMLResponse:
    try:
        result = await _store("get_result_by_id", result_id)
        if result is None:
            return _error(request, "Saved result not found", 404)
        notes = await _store("get_annotations", result_id)
        return templates.TemplateResponse(
            request,
            "partials/followup.html",
            {
                "result": result,
                "outcome_preview": notes.get("outcome", ""),
                "csrf_token": _get_or_create_csrf_token(request),
            },
        )
    except Exception as error:
        return _unexpected(request, "Follow-up preview", error)


@app.post("/followup/{result_id}", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def start_followup(
    request: Request,
    result_id: str,
    query: str = Form(...),
    include_context: bool = Form(default=False),
    include_outcome: bool = Form(default=False),
    prior_excerpt: str = Form(default=""),
    include_result: bool = Form(default=False),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        original = await _store("get_result_by_id", result_id)
        if not original:
            return _error(request, "Saved result not found", 404)
        state = {
            "query": query,
            "roles": original["experts"],
            "result_type": original["result_type"],
            "rounds": 1,
            "advisor_context": original.get("advisor_context"),
            "parent_result_id": result_id,
            "task_brief": original.get("task_brief", {}) if include_context else {},
            "sources": original.get("sources", []) if include_context else [],
        }
        if include_result:
            state["task_brief"] = {
                **state["task_brief"],
                "background": state["task_brief"].get("background", "")
                + "\nUser-selected prior AI analysis (unverified): "
                + prior_excerpt,
            }
        if include_outcome:
            notes = await _store("get_annotations", result_id)
            state["task_brief"] = {
                **state["task_brief"],
                "background": state["task_brief"].get("background", "")
                + "\nUser-selected past outcome: "
                + notes.get("outcome", "Not recorded"),
            }
        return await _launch(request, state, True, "")
    except ValueError as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Follow-up", error)


@app.post("/result/{result_id}/retry", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def retry_saved_result(
    request: Request,
    result_id: str,
    csrf_token: str = Form(...),
    acknowledge: bool = Form(default=False),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        result = await _store("get_result_by_id", result_id)
        if not result:
            return _error(request, "Saved result not found", 404)
        if (
            any(
                item.get("status") in ("in_flight", "transport_uncertain")
                for item in result.get("execution_receipts", [])
            )
            and not acknowledge
        ):
            return _error(
                request,
                "Acknowledge that an interrupted call may have completed remotely before retrying. Your saved result is retained.",
            )
        state = {**result, "roles": result["experts"], "parent_result_id": result_id}
        # This is a new recovery run. Original receipts remain in the parent.
        for key in (
            "id",
            "timestamp",
            "run_id",
            "execution_receipts",
            "run_status",
            "run_error",
            "attempts",
            "planned_calls",
        ):
            state.pop(key, None)
        return await _launch(request, state, True, "")
    except ValueError as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Scoped retry", error)


@app.post("/result/{result_id}/organize", response_class=HTMLResponse)
async def organize_result(
    request: Request,
    result_id: str,
    tags: str = Form(default=""),
    pinned: bool = Form(default=False),
    archived: bool = Form(default=False),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        if await _store("get_result_by_id", result_id) is None:
            return _error(request, "Saved result not found", 404)
        manager = await _manager()
        await asyncio.to_thread(
            manager.workspace.organize,
            result_id,
            tags=tags,
            pinned=pinned,
            archived=archived,
        )
        return HTMLResponse(
            '<p role="status">Organization saved. Archived items remain available with the Archived filter.</p>',
            headers={"HX-Trigger": "resultSaved"},
        )
    except ValueError as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Organize result", error)


@app.get("/compare", response_class=HTMLResponse)
async def compare_saved(request: Request, left: str, right: str) -> HTMLResponse:
    try:
        if left == right:
            return _error(request, "Choose two different saved records for comparison.")
        first, second = await asyncio.gather(
            _store("get_result_by_id", left), _store("get_result_by_id", right)
        )
        if not first or not second:
            return _error(request, "Choose two available saved results", 404)
        first_notes, second_notes = await asyncio.gather(
            _store("get_annotations", left), _store("get_annotations", right)
        )
        return templates.TemplateResponse(
            request,
            "partials/compare.html",
            {
                "first": first,
                "second": second,
                "notes": {left: first_notes, right: second_notes},
                "same_input": bool(
                    first.get("input_sha256")
                    and first.get("input_sha256") == second.get("input_sha256")
                ),
            },
        )
    except Exception as error:
        return _unexpected(request, "Comparison", error)


@app.post("/calculate/effort", response_class=HTMLResponse)
async def calculate_effort(
    request: Request,
    manual: str = Form(...),
    setup: str = Form(...),
    review: str = Form(...),
    correction: str = Form(...),
    recovery: str = Form(...),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        result = effort_comparison(
            {
                "manual": manual,
                "setup": setup,
                "review": review,
                "correction": correction,
                "recovery": recovery,
            }
        )
        return templates.TemplateResponse(
            request, "partials/calculation.html", {"calculation": result}
        )
    except ValueError as error:
        return _error(request, str(error))


@app.get("/export/{result_id}/json")
async def export_archive(
    request: Request, result_id: str, include_notes: bool = False
) -> Response:
    try:
        result = await _store("get_result_by_id", result_id)
        if not result:
            return _error(request, "Saved result not found", 404)
        notes = await _store("get_annotations", result_id) if include_notes else None
        return Response(
            json.dumps(archive_record(result, notes), ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="advisors-{result_id}.json"'
            },
        )
    except Exception as error:
        return _unexpected(request, "Archive export", error)


@app.get("/export/{result_id}/brief.md")
async def export_abridged(request: Request, result_id: str) -> Response:
    try:
        result = await _store("get_result_by_id", result_id)
        if not result:
            return _error(request, "Saved result not found", 404)
        content = (
            "# Abridged brief\n\nThis is a presentation summary. Use Complete record for the exact question, full answers, source passages, and receipts.\n\n"
            + build_executive_brief_markdown(result)
        )
        return Response(
            content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="brief-{result_id}.md"'
            },
        )
    except Exception as error:
        return _unexpected(request, "Brief export", error)


@app.get("/export/{result_id}/report")
async def export_personal_report(
    request: Request, result_id: str, include_notes: bool = False
) -> Response:
    try:
        result = await _store("get_result_by_id", result_id)
        if not result:
            return _error(request, "Saved result not found", 404)
        notes = await _store("get_annotations", result_id) if include_notes else None
        return Response(
            complete_markdown(result, notes),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="decision-report-{result_id}.md"'
            },
        )
    except Exception as error:
        return _unexpected(request, "Decision report", error)


@app.post("/archive/preview", response_class=HTMLResponse)
async def preview_import(
    request: Request, file: UploadFile = File(...), csrf_token: str = Form(...)
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        raw = await file.read(5000001)
        if len(raw) > 5000000:
            raise ValueError("Use an archive up to five megabytes.")
        rows = validate_archive(json.loads(raw))
        for row in rows:
            row["preview_status"] = await _store("preview_import", row["result"])
        key = uuid.uuid4().hex
        manager = await _manager()
        await asyncio.to_thread(
            manager.workspace.put, "import", key, {"id": key, "records": rows}
        )
        return templates.TemplateResponse(
            request,
            "partials/import.html",
            {"import_id": key, "rows": rows, "csrf_token": csrf_token},
        )
    except (ValueError, UnicodeError) as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Import preview", error)
    finally:
        await file.close()


@app.post("/archive/import/{import_id}", response_class=HTMLResponse)
async def commit_import(
    request: Request, import_id: str, csrf_token: str = Form(...)
) -> HTMLResponse:
    if not _validate_csrf(request, csrf_token):
        return _error(request, "Invalid CSRF token", 403)
    try:
        manager = await _manager()
        preview = await asyncio.to_thread(manager.workspace.get, "import", import_id)
        if not preview:
            return _error(
                request,
                "Import preview is unavailable; preview the archive again.",
                404,
            )
        for row in preview["records"]:
            await _store("import_record", row["result"], row["annotations"])
        return HTMLResponse(
            '<p role="status">Additive import completed. Existing content and notes were retained.</p>',
            headers={"HX-Trigger": "resultSaved"},
        )
    except ValueError as error:
        return _error(request, str(error))
    except Exception as error:
        return _unexpected(request, "Archive import", error)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=get_settings().port, access_log=False)
