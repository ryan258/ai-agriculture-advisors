# Code Review: AI Agriculture Advisors

**Review Date:** 2026-04-01  
**Version:** 2.0.0

**MECHANIC'S VERDICT**: PASS ✅

**INSPECTION LOG**

- [x] **No-Bloat**: Pure Python stack. No Docker, Node.js, React, or microservices.
- [x] **Arsenal**: Core logic lives in `lib/`. `main.py` stays a routing layer over services, experts, engine, and storage.
- [x] **Types**: Typed Python modules with `mypy` configured and explicit interfaces on the portable layers.
- [x] **Candlelight**: UI matches the Candlelight palette with the expected dark surfaces and muted accent colors.

## Architecture Snapshot

- **Runtime**: FastAPI + Jinja2 + HTMX on bare metal.
- **Inference**: `lib/engine/llm_client.py` wraps OpenRouter calls through `httpx`.
- **Domain model**: `lib/experts/` defines 10 specialized advisors with a registry-based lookup.
- **Orchestration**: `lib/services/` handles parallel expert queries and multi-round roundtable discussions.
- **Persistence**: `lib/storage/history_store.py` stores saved results in ChromaDB and exports markdown.

## What Is Solid

- Thin route layer with business logic pushed into `lib/`.
- No framework leakage from `lib/` back into `main.py`.
- Clean HTMX workflow for query, roundtable, save, history, and export.
- CSRF protection and rate limiting are both implemented and now covered by tests.
- History storage, retrieval, and markdown export now have direct test coverage.

## Known Tradeoffs

- Streaming responses are still not implemented.
- Query/result caching is still not implemented.
- History remains append-only; deletion/reset is a future decision.
- GitNexus indexing requires a local Node toolchain to refresh when the graph goes stale.

## Shipping Notes

This repo is in good shape for personal-use release. The stack is simple, the module boundaries are intact, and the remaining work is product enhancement rather than cleanup debt.
