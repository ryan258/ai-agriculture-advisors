"""AI Agriculture Advisors - FastAPI Application."""

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
from lib.experts import get_all_experts
from lib.services import query_experts, run_roundtable
from lib.storage import history_store
from lib.utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
CSRF_COOKIE_NAME = "csrf_token"


def _get_or_create_csrf_token(request: Request) -> str:
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        token = secrets.token_urlsafe(32)
    return token


def _validate_csrf(request: Request, csrf_token: str) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    return bool(cookie_token and csrf_token and cookie_token == csrf_token)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    settings.validate()
    logger.info("AI Agriculture Advisors started successfully")
    yield
    # Shutdown (nothing to clean up)


# Initialize FastAPI
app = FastAPI(
    title="AI Agriculture Advisors",
    description="Multi-expert agricultural advisory system powered by LLMs",
    version="2.0.0",
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
    csrf_token = _get_or_create_csrf_token(request)
    experts = get_all_experts()
    response = templates.TemplateResponse(
        request, "index.html", {"experts": experts, "csrf_token": csrf_token}
    )
    if CSRF_COOKIE_NAME not in request.cookies:
        response.set_cookie(
            CSRF_COOKIE_NAME,
            csrf_token,
            samesite="lax",
            httponly=True,
        )
    return response


@app.post("/query", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def query(
    request: Request,
    query: str = Form(...),
    roles: List[str] = Form(default=[]),
    csrf_token: str = Form(...),
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
        result = await query_experts(query, roles)
        return templates.TemplateResponse(
            request,
            "partials/responses.html",
            {
                "query": query,
                "responses": result["responses"],
                "result_id": None,
                "csrf_token": csrf_token,
            },
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
        result = await run_roundtable(query, roles, rounds)
        return templates.TemplateResponse(
            request,
            "partials/roundtable.html",
            {
                "query": query,
                "roles": roles,
                "rounds": result["rounds"],
                "transcript": result["transcript"],
                "final_answer": result["final_answer"],
                "result_id": None,
                "csrf_token": csrf_token,
            },
        )
    except Exception as e:
        logger.error(f"Error in roundtable: {e}")
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "An error occurred.", "details": str(e)},
        )


@app.get("/history", response_class=HTMLResponse)
async def get_history(request: Request) -> HTMLResponse:
    """Get saved query history."""
    history = history_store.get_history(limit=10)
    return templates.TemplateResponse(
        request, "partials/history_list.html", {"history": history}
    )


@app.get("/result/{result_id}", response_class=HTMLResponse)
async def get_result(request: Request, result_id: str) -> HTMLResponse:
    """Get a saved result by ID."""
    result = history_store.get_result_by_id(result_id)
    csrf_token = _get_or_create_csrf_token(request)

    if not result:
        return templates.TemplateResponse(
            request, "partials/error.html", {"message": "Result not found."}
        )

    if result.get("result_type") == "roundtable":
        return templates.TemplateResponse(
            request,
            "partials/roundtable.html",
            {
                "query": result["query"],
                "roles": result.get("experts", []),
                "rounds": result.get("rounds", 0),
                "transcript": result.get("transcript", []),
                "final_answer": result.get("final_answer", ""),
                "result_id": result_id,
                "csrf_token": csrf_token,
            },
        )
    else:
        return templates.TemplateResponse(
            request,
            "partials/responses.html",
            {
                "query": result["query"],
                "responses": result.get("responses", []),
                "result_id": result_id,
                "csrf_token": csrf_token,
            },
        )


@app.post("/save", response_class=HTMLResponse)
async def save_result(
    request: Request,
    query: str = Form(...),
    result_type: str = Form(default="query"),
    responses: Optional[str] = Form(default=None),
    roundtable_data: Optional[str] = Form(default=None),
    csrf_token: str = Form(...),
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
            result_id = history_store.save_result(
                query=query,
                experts=rt_data.get("roles", []),
                responses=[],
                result_type="roundtable",
                roundtable_data=rt_data,
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
            result_id = history_store.save_result(
                query=query,
                experts=experts,
                responses=resp_data,
                result_type="query",
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
async def export_result(result_id: str) -> Response:
    """Export a saved result as markdown."""
    markdown = history_store.export_to_markdown(result_id)

    if not markdown:
        return Response(
            content="Result not found",
            status_code=404,
            media_type="text/plain",
        )

    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=agri-query-{result_id}.md"
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=get_settings().port)
