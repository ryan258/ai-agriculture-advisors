# AI Agriculture Advisors — Roadmap

**Last Updated:** 2026-01-30  
**Current Version:** 2.0.0  
**Status:** Working MVP (FastAPI + Jinja2 + HTMX + ChromaDB)

---

## Now (Tighten & Align)
- **Error handling polish**: Standardize user-facing error messages and ensure server logs capture structured context.
- **History management**: Decide whether to add delete/reset actions for saved results or explicitly document immutable history.
- **Configuration clarity**: Add a single place to define rate limits, timeouts, and persistence paths (env + defaults).

---

## Next (Product Improvements)
- **Streaming responses**: Add SSE support for `/query` and `/roundtable` to reduce perceived latency.
- **Response caching**: Cache by normalized query + role set to avoid repeat LLM calls.
- **Model selection UI**: Allow choosing OpenRouter models with cost/speed hints.
- **Roundtable controls**: User-selectable rounds and summary style with guardrails on transcript length.

---

## Later (Platformization)
- **Auth & quotas**: Optional API keys per user plus rate-limit headers for public exposure.
- **Observability**: Request/LLM timing metrics and structured error codes.
- **Persistence options**: Optional SQLite export for history or multi-tenant storage.

---

## Current Stats

**What works:**
- Multi-expert `/query` and roundtable `/roundtable`
- Persistent history with ChromaDB
- Save/export flow (`/save`, `/export/{id}`, `/result/{id}`)
- HTMX UI with sanitized markdown rendering
- Rate limiting + CSRF protection
- 37 passing tests

**Gaps/risks:**
- No streaming or caching yet
- No auth or per-user quotas
- History deletion not implemented
