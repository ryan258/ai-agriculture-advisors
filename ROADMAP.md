# AI Advisors — Roadmap

**Last Updated:** 2026-10-15  
**Current Version:** 2.0.0  
**Status:** Modular Monolith (FastAPI + Jinja2 + HTMX + ChromaDB)

---

## Current Status & Capabilities

**What works:**
- **Multi-panel advisor catalog**: 5 built-in panels (Agriculture, Software, AI Workflow & Delegation, Accessibility & Effort, Evidence & Judgment) loaded dynamically from JSON definitions (`lib/experts/definitions/`).
- **Parallel queries & discussions**: Multi-expert parallel execution (`/query`) and multi-turn roundtable deliberation (`/roundtable`) with selectable rounds (1–5).
- **Practical decision support**: Shared 4-point Decision Check (`compact_decision`) providing concrete next steps, strongest objections, unknowns, and required user decisions across individual queries and roundtable syntheses.
- **Roundtable recovery & retry**: Resilient resume flow (`/roundtable/retry`) preserving completed contributions, tracking provider rate limits with countdown timers, and providing bounded same-model JSON failover on OpenRouter shared pool exhaustion.
- **Executive briefing service**: Rendered decision-ready HTML reports (`/export/{id}/brief`) and Markdown exports (`/export/{id}`) preserving captured advisor definitions and decision checks.
- **Historical context preservation**: Saved history in ChromaDB captures and validates exact advisor system prompt snapshots at runtime, ensuring legacy results remain intact even if catalog prompts evolve.
- **Defensive execution**: CSRF double-submit protection, edge rate limiting via slowapi, DOMPurify markdown sanitization, and structured error partials.
- **133 passing automated tests**: Comprehensive unit, integration, route, service, and recovery test coverage with 100% mocked provider boundaries.

---

## Now (Immediate Priorities)
- **Observability & telemetry**: Structured latency and provider cost/token metrics logging.
- **History management**: Implement optional deletion/archive actions for saved ChromaDB entries.
- **Response caching**: Cache identical query + role combinations to reduce redundant upstream calls.

---

## Next (Product Improvements)
- **Streaming responses**: SSE (Server-Sent Events) integration for real-time streaming of advisor responses and synthesis into HTMX targets.
- **Dynamic model selection**: UI controls for selecting OpenRouter models with speed and pricing indicators.
- **Panel customization validation CLI**: CLI command to lint and validate custom advisor and panel JSON files.

---

## Later (Platformization)
- **Multi-tenant storage**: Optional SQLite or external database adapters for history persistence.
- **Granular API auth**: Optional API key authentication and usage quotas for public deployment.
