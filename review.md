# Code Review: AI Advisors

**Review Date:** 2026-10-26  
**Version:** 2.1.0 candidate  
**Reference Register:** [Remediation status](docs/REMEDIATION-STATUS.md) | [Baseline review](docs/PROJECT-REVIEW-2026-10-25.md)

**MECHANIC'S VERDICT**: PASS ✅

**INSPECTION LOG**

- [x] **No-Bloat**: Pure Python + Jinja2 + HTMX bare-metal stack. Zero package.json, zero Dockerfile, zero containers, zero frontend frameworks. Vendored local assets (HTMX, Marked, DOMPurify) with verified SHA-256 manifest.
- [x] **Arsenal**: Decoupled modules in `lib/` (`contracts.py`, `operations.py`, `engine/`, `services/`, `storage/`, `experts/`). `main.py` is strictly a routing dispatcher mapping HTTP/HTMX requests to portable library calls.
- [x] **Types**: Explicit Pydantic and dataclass models throughout. `mypy` verified across 11 source files with 0 errors.
- [x] **Candlelight**: Strictly compliant. Dark palette centralized in `static/css/theme.css` (`#121212`, `#1A1A1A`, `#242424`, text `#EBD2BE`, `--text-2: #A6ACCD`, accents `#A6ACCD`, `#98C379`, `#E06C75`, `#F59E0B`). Lighter secondary text for readability, ink-friendly print styling.

## Architecture Snapshot

- **Runtime**: FastAPI + Jinja2 + HTMX running locally on bare metal (loopback `127.0.0.1:8123`).
- **Engine & Execution**: `lib/engine/llm_client.py` and `lib/engine/execution.py` manage bounded provider requests, strict input/output validation, pre-dispatch receipts, and uncertain-transport handling.
- **Persistence & Working State**: `lib/storage/history_store.py` manages immutable versioned results in ChromaDB `query_history_v3` (inert embeddings) and separate `personal_annotations`. `lib/storage/workspace_store.py` manages working runs, journal checkpoints, and reusable assets in stdlib SQLite (`workbench.sqlite3`).
- **Services & Operations**: `lib/services/` encapsulates roundtable discussions, brief generation, consensus extraction, and runs. `lib/operations.py` handles doctor checks, stopped-app private backups, and verified-manifest restore into new directories.
- **UI & Accessibility**: Server-rendered HTMX partials, vanilla CSS variables, local draft recovery in `static/js/note-drafts.js`, and discoverable keyboard navigation.

## What Is Solid

- **Strict boundaries**: No framework imports inside portable `lib/` modules.
- **Fault-tolerant recovery**: Interrupted provider calls checkpoint to SQLite journal; manual resume acknowledges in-flight state without duplicated successful calls.
- **Zero-embedding persistence**: New saves require no local embedding model; legacy collections remain read-only without destructive migration.
- **Private local operations**: Root-anchored `./advisors` script with isolated stopped-app backups and tamper-evident restore rehearsal.
- **Verified quality**: Targeted regression tests passed, 11-file Mypy passed, 17/17 headless JS checks passed, and read-only browser navigation confirmed clean DOM and console.

## Tradeoffs and Known Limits

- Live provider output quality and semantic alignment remain subject to human judgment.
- Browser drafts are convenience recovery and are excluded from backup archives.
- Search operates on metadata and personal notes rather than full vector/semantic similarity.
- Restore rehearsal requires a fresh directory and never overwrites live data in place.

## Mechanic's Summary

The codebase strictly adheres to the Arsenal Strategy and No-Bloat law. Logic is portable, dependencies are lean, and error paths are resilient. It holds up cleanly.
