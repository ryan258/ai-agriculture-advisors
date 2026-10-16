"""AI Advisors - FastAPI Application."""

import json
import logging
import secrets
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from lib.engine.config import get_settings
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
    yield
    # Shutdown
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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
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
        logger.error(f"Error loading index: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Failed to load application.", "details": str(e)},
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
) -> HTMLResponse:
    """
    Query selected experts in parallel.

    Returns HTML partial with expert responses.
    """
    if not _validate_csrf(request, csrf_token):
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Invalid CSRF token. Please refresh and try again."},
        )

    if not roles:
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Please select at least one expert."},
        )

    if not query.strip():
        return templates.TemplateResponse(
            request, "partials/error.html", {"message": "Please enter a query."}
        )

    try:
        advisor_context = build_advisor_context(panel_id, roles)
        result = await query_experts(query, roles)
        return templates.TemplateResponse(
            request,
            "partials/responses.html",
            {
                "query": query,
                "responses": result["responses"],
                "advisor_context": advisor_context,
                "result_summary": result_summary({**result, "result_type": "query"}),
                "result_id": None,
                "csrf_token": csrf_token,
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Error in query: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "An error occurred.", "details": str(e)},
        )


@app.post("/roundtable", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def roundtable(
    request: Request,
    query: str = Form(...),
    roles: List[str] = Form(default=[]),
    rounds: int = Form(default=3),
    csrf_token: str = Form(...),
    panel_id: str = Form(default=DEFAULT_PANEL_ID),
) -> HTMLResponse:
    """
    Run a roundtable discussion among selected experts.

    Returns HTML partial with transcript and consensus.
    """
    if not _validate_csrf(request, csrf_token):
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Invalid CSRF token. Please refresh and try again."},
        )

    if len(roles) < 2:
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Roundtable requires at least 2 experts."},
        )

    if not query.strip():
        return templates.TemplateResponse(
            request, "partials/error.html", {"message": "Please enter a query."}
        )

    try:
        advisor_context = build_advisor_context(panel_id, roles)
        rounds = _normalize_rounds(rounds)
        result = await run_roundtable(
            query, roles, rounds, advisor_context=advisor_context
        )
        view = roundtable_view(
            {
                **result,
                "query": query,
                "roles": roles,
                "advisor_context": advisor_context,
            }
        )
        return templates.TemplateResponse(
            request,
            "partials/roundtable.html",
            {
                **view,
                "result_summary": result_summary(
                    {**result, "result_type": "roundtable"}
                ),
                "result_id": None,
                "csrf_token": csrf_token,
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Error in roundtable: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "An error occurred.", "details": str(e)},
        )


@app.post("/roundtable/retry", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def retry_roundtable_result(
    request: Request,
    state: str = Form(...),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    """Resume the submitted discussion without making calls for completed answers."""
    try:
        if not _validate_csrf(request, csrf_token):
            raise ValueError(
                "Invalid CSRF token. Reload the saved result and try again."
            )
        result = await retry_roundtable(json.loads(state))
        return templates.TemplateResponse(
            request,
            "partials/roundtable.html",
            {
                **roundtable_view(result),
                "result_summary": result_summary(
                    {**result, "result_type": "roundtable"}
                ),
                "result_id": None,
                "csrf_token": csrf_token,
            },
        )
    except (ValueError, TypeError) as error:
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": str(error)},
            headers={"HX-Retarget": "#roundtable-retry-status"},
        )
    except Exception:
        logger.exception("Roundtable retry failed")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {
                "message": "Retry could not complete. Your existing answers are still here."
            },
            headers={"HX-Retarget": "#roundtable-retry-status"},
        )


@app.get("/history", response_class=HTMLResponse)
async def get_history(request: Request, q: str = "", offset: int = 0) -> HTMLResponse:
    """Get saved query history."""
    try:
        q, offset = q.strip()[:300], max(0, offset)
        history = history_store.get_history(limit=11, search=q, offset=offset)
        return templates.TemplateResponse(
            request, "partials/history_list.html", history_page(history, q, offset)
        )
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Failed to load history.", "details": str(e)},
            status_code=500,
        )


@app.get("/resume", response_class=HTMLResponse)
async def resume_saved_work(request: Request, result_id: str = "") -> HTMLResponse:
    """Offer existing work without retrying or submitting a provider request."""
    try:
        result = history_store.get_result_by_id(result_id) if result_id else None
        if result is not None:
            result = {**result, **history_store.get_annotations(result_id)}
        return templates.TemplateResponse(
            request,
            "partials/resume.html",
            {
                "resume_result": result,
                "resume_missing_id": result_id if result_id and result is None else "",
                "unfinished": history_store.get_open_items(limit=3),
            },
        )
    except Exception:
        logger.exception("Could not load the resume entry point")
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
        result = history_store.get_result_by_id(result_id)
        csrf_token = _get_or_create_csrf_token(request)

        if not result:
            return templates.TemplateResponse(
                request,
                "partials/missing_result.html",
                {"result_id": result_id},
                status_code=404,
            )

        personal_context = {
            "annotations": history_store.get_annotations(result_id),
            "annotation_statuses": ANNOTATION_STATUSES,
            "result_summary": result_summary(result),
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
    except Exception as e:
        logger.error(f"Error loading result {result_id}: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Failed to load result.", "details": str(e)},
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
        elif history_store.get_result_by_id(result_id) is None:
            context["notes_error"] = (
                "The saved result is no longer available. Your entered notes have not been discarded."
            )
            status_code = 404
        else:
            context["annotations"] = history_store.update_annotations(
                result_id, annotations
            )
            context["notes_saved"] = True
    except ValueError as error:
        context["notes_error"] = str(error)
        status_code = 400
    except Exception:
        logger.exception("Could not save personal notes for result %s", result_id)
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
    query: str = Form(...),
    result_type: str = Form(default="query"),
    responses: Optional[str] = Form(default=None),
    roundtable_data: Optional[str] = Form(default=None),
    csrf_token: str = Form(...),
    advisor_context: Optional[str] = Form(default=None),
) -> HTMLResponse:
    """Save a query result to persistent storage."""
    try:
        if not _validate_csrf(request, csrf_token):
            return templates.TemplateResponse(
                request,
                "partials/error.html",
                {"message": "Invalid CSRF token. Please refresh and try again."},
            )

        if result_type == "roundtable" and roundtable_data:
            rt_data = json.loads(roundtable_data)
            context_args = {}
            if advisor_context:
                context_args["advisor_context"] = validate_advisor_context(
                    json.loads(advisor_context), rt_data.get("roles", [])
                )
            result_id = history_store.save_result(
                query=query,
                experts=rt_data.get("roles", []),
                responses=[],
                result_type="roundtable",
                roundtable_data=rt_data,
                **context_args,
            )
            return templates.TemplateResponse(
                request,
                "partials/save_success.html",
                {
                    "result_id": result_id,
                    "query": query,
                    "result_type": "roundtable",
                    "rounds": rt_data.get("rounds", 0),
                    "num_experts": len(rt_data.get("roles", [])),
                },
            )
        elif responses:
            resp_data = json.loads(responses)
            experts = [r.get("role") for r in resp_data]
            context_args = {}
            if advisor_context:
                context_args["advisor_context"] = validate_advisor_context(
                    json.loads(advisor_context), experts
                )
            result_id = history_store.save_result(
                query=query,
                experts=experts,
                responses=resp_data,
                result_type="query",
                **context_args,
            )
            return templates.TemplateResponse(
                request,
                "partials/save_success.html",
                {
                    "result_id": result_id,
                    "query": query,
                    "result_type": "query",
                },
            )
        else:
            return templates.TemplateResponse(
                request, "partials/error.html", {"message": "No data to save."}
            )
    except Exception as e:
        logger.error(f"Error saving result: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Failed to save.", "details": str(e)},
        )


@app.get("/export/{result_id}")
async def export_result(request: Request, result_id: str) -> Response:
    """Export a saved result as markdown."""
    try:
        result = history_store.get_result_by_id(result_id)
        if not result:
            return templates.TemplateResponse(
                request,
                "404.html",
                {"message": "Saved result not found.", "result_id": result_id},
                status_code=404,
            )
        markdown = build_executive_brief_markdown(result)

        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=advisor-query-{result_id}.md"
            },
        )
    except Exception as e:
        logger.error(f"Error exporting result {result_id}: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Failed to export result.", "details": str(e)},
            status_code=500,
        )


@app.get("/export/{result_id}/brief", response_class=HTMLResponse)
async def export_result_brief(request: Request, result_id: str) -> HTMLResponse:
    """Render a saved result as an executive brief."""
    try:
        result = history_store.get_result_by_id(result_id)
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
        logger.error(f"Error rendering executive brief for {result_id}: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Failed to build executive brief.", "details": str(e)},
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=get_settings().port)
