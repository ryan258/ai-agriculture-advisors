# AI Advisors Roadmap

Updated October 16, 2026. Local personal tool, version 2.1.0 candidate. The goal is useful advice with less repeated input, reading, and reconstruction after a break.

## Implemented

- Five configurable panels, individual queries and roundtables, captured advisor profiles, and scoped recovery preserving successful contributions.
- Captured Decision Checks and structured handoffs before the expandable full discussion, including stale-synthesis warnings and visible advisor failures.
- Copy controls with readable selected-text fallback, editable starters, retained local drafts, and deliberate clearing.
- Truthful request status, duplicate-submission protection, and actual elapsed browser-request time.
- Case-insensitive search across all saved metadata and personal notes, stable ten-item pagination, and readable legacy records.
- Optional personal title, decision status, next/last step, blocker, and outcome in separate annotation storage. Generated content and exports remain unchanged.
- A last-opened/saved Resume entry point and a short list of explicitly undecided or waiting items.
- Evidence starter fields for a supplied source label and passage, plus Accessibility guidance that does not assume a notes destination exists.

The October 16 implementation passed 144 targeted Python tests, 12 headless JavaScript tests, and the full locked test suite of 182 tests in 4.14s. Independent source review found no remaining concrete defects in the integrated scope. See [release readiness](docs/RELEASE-READINESS.md) for exact commands and evidence limits.

## Next personal checks

Use the [single personal pass](docs/PERSONAL-USE-CHECK.md) on one existing saved result. Check normal dictation and reading, copy behavior, saving a note, finding it later, and returning after a real break. These observations remain pending.

The [month plan](docs/MONTH-PLAN.md) records implementation and personal acceptance separately. The next priority should come from an actual difficulty in that pass.

## Deferred unless use justifies them

Per-advisor streaming, cancellation/background jobs, provider token/cost dashboards, model selection, semantic search, caching, additional panels, document ingestion, deletion/archive management, and cross-tool integrations remain optional. The current implementation adds no accounts, deployment workflow, new database engine, runtime dependencies, or frontend build.
