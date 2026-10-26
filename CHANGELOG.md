# Changelog

Notable changes to AI Advisors. Entries below 2.1.0 retain the project's earlier name and history.

## [Unreleased] — October 25 repair and local workflow expansion (verified October 26, 2026)

Owner verification completed for targeted regressions, Mypy typing across 11 files, 17 headless JavaScript checks, configuration/dependency diagnostics, stopped-app backup, managed startup, live connectivity diagnostic, and an authorized read-only browser pass (with 4 UI/focus fixes). Broader personal workflow acceptance and real-data restore rehearsal remain pending. See [current remediation status](docs/REMEDIATION-STATUS.md).

- Fix result-preserving Save errors, invalid provider content, strict saved-record/import boundaries and complete archival exports.
- Add bounded durable working runs, pre-dispatch receipts, manual pause/recovery, idempotency and explicit retry lineage.
- Remove embedding-model dependency from new saves using a separate collection; keep legacy records read-only and notes separate.
- Add selected task/source context, reusable text, linked follow-ups, options/disagreement views, organization, comparison, reports, archive preview/import, a measured-minutes calculator and fictional quality cases.
- Add root-anchored loopback operations, private stopped-app backup/new-location restore, offline diagnostics and owner-invoked verification.
- Vendor browser dependencies with licenses, improve Candlelight text/targets/tables/milestone feedback/note-draft recovery, and reconcile architecture/contribution/status documentation.
- Keep Python runtime dependencies and lockfile unchanged. The agent did not open or migrate existing production history. Browser/local/provider/restore acceptance remains separate.

## Historical — 2.1.0 candidate through October 16

Release evidence and remaining acceptance checks are recorded in [release readiness](docs/RELEASE-READINESS.md). This candidate has not been published.

October 16 local personal-use implementation: captured summaries before full responses, copy controls with selectable fallback, recoverable draft input, truthful scoped request status and elapsed time, full-history metadata search with pagination, separate optional personal annotations/outcomes, and saved-work resumption. The supplied-evidence starter distinguishes pasted passages from unopened links; Accessibility guidance no longer assumes a notes destination exists. No dependencies or data migration were added. Focused checks passed **144 Python / 12 headless JavaScript**, and the full locked suite passed **182 tests in 4.14s** on 2026-10-16; independent source review completed. Browser, HTMX, dictation, cold-return, and live model adherence remain separate checks for this revision.

Automated acceptance before the trial corrections on 2026-10-15: 139 cases passed in the full run, followed by 3 passing route cases after a test-only snapshot-assertion correction. Targeted results for the subsequent corrections below passed (97 targeted in 2.47s; 151 full suite in 3.18s on 2026-10-15). Live output and personal acceptance are recorded separately in the readiness note.

Live trial `953adc1d` completed save/reopen and both exports on 2.1.0. It exposed assumed voice/alias capabilities, a lost accessible region name after Save, and a missing Executive Brief control after replay. All three corrections are implemented in source; the saved trial remains unchanged. At the October 15 checkpoint no further live roundtable had run. Subsequent October 16 notes/search/immediate reload observations are recorded in the month plan; they do not establish every input method or a measured after-break return.

### Added

- Configurable advisor panels: Agriculture retains its original ten role IDs; Software adds five advisors.
- AI Workflow & Delegation, Accessibility & Effort, and Evidence & Judgment, each with four advisors and practical examples.
- AI Workflow roundtables return the actual task packet, evidence-based review checklist, resume checkpoint, and a comparison with manual effort.
- Accessibility roundtables return a reusable starter, compact checkpoint, dictation fallback, and a small trial to measure repeated input and interactions.
- Saved panel metadata and advisor prompts, retained through replay, Markdown, and HTML briefs.
- Scoped retries for failed advisors and synthesis, including saved partial roundtables.
- Optional `OPENROUTER_SYNTHESIS_MODEL` and one same-model JSON-mode failover for a confirmed OpenRouter upstream shared-pool 429.

### Changed

- Decision-panel roundtable turns request at most two short, distinct bullets. Later rounds request only new information; the moderator owns the single final Decision Check.
- Standalone decision-panel answers retain their individual four-point Decision Checks.
- Accessibility guidance favors reusable text and existing entry points, avoids unsupported tool claims, and asks a question only when a choice blocks the first trial.
- Replaced prompt-only subclasses with a validated JSON catalog. Panel examples and separately remembered selections preserve the current draft when switching panels.
- Aligned package, lockfile root package, and FastAPI metadata at 2.1.0. Setup examples use configurable model IDs and preserve an existing `.env`.

### Fixed

- Accessibility advisor and synthesis instructions now accept only the original user's confirmed setup as evidence of working capabilities. Advisor proposals cannot establish voice commands, aliases, automatic saving, or restoration. Unknown setup uses plain text and safe-pause guidance, including on text fallback and captured discussion retries; live adherence remains unverified.
- Save preserves the query/roundtable heading IDs used by named regions. Saved query and roundtable headers share Executive Brief and Markdown controls immediately after Save and after replay.
- Successful advisor answers are retained through recovery; synthesis-only retry does not rerun advisors.
- Structured and plain-text handoffs survive HTML/Markdown export, with the Decision Check rendered once.
- Incomplete plain-text closing points remain visible in exports, and empty fallback synthesis is retained as a retryable failure rather than a success.
- Account/key limits and unrelated provider errors do not trigger shared-pool failover. Retry countdowns describe a minimum wait rather than a recovery promise.

### Compatibility

- No history migration or reset is required. The default `.chromadb` directory and `query_history` collection are retained.
- Previously saved answers keep their original wording and captured prompts; older saves without snapshots remain readable with that limitation identified.
- Agriculture and Software retain their response formats. Export never makes provider calls or generates new advice.

## [2.0.1] - 2026-01-30

### Changed
- Docs: aligned README, API docs, happy path, and roadmap with the current FastAPI/HTMX implementation and environment variables.

## [2.0.0] - 2026-01-30

### Changed
- **Complete rewrite from Node.js to Python** following the Anti-Gravity Standard architecture
- Replaced Express.js with FastAPI for async-first backend
- Replaced vanilla JavaScript frontend with Jinja2 templates + HTMX
- Replaced localStorage history with ChromaDB persistent storage
- New Candlelight dark theme per CLAUDE.md specifications
- Restructured codebase into `lib/` Arsenal pattern (engine, experts, services, storage, utils)

### Added
- **Persistent history**: Query results saved to ChromaDB, survives server restarts
- **Markdown export**: Download any saved result as a .md file
- **Save functionality**: Button to persist query results
- Async LLM client with httpx
- Abstract `Expert` base class for all domain experts
- Parallel query execution with `asyncio.gather()`
- Rate limiting via slowapi
- pytest test suite with async support
- black/mypy configuration in pyproject.toml
- Type hints throughout the codebase

### Removed
- All Node.js dependencies and tooling
- Express.js, Helmet, Winston, Mongoose
- Jest test framework
- Vanilla JavaScript frontend (public/)
- Empty data/ placeholder files

---

## [1.0.0] - 2025-04-22

### Added

#### Core Features
- **Multi-Expert Consultation**: Query multiple agricultural experts simultaneously via `/api/query` endpoint
- **Roundtable Discussion**: Collaborative multi-round expert debates via `/api/roundtable` endpoint
- **Markdown Rendering**: Client-side markdown parsing with marked.js for formatted responses
- **Logging**: Winston-backed logging with console output in development
- **Web Interface**: Single-page application for interacting with agricultural experts

#### Expert System
- 10 specialized agricultural advisors covering crop science, climate, commodities, agritech, supply chain, soil health, pest/disease, irrigation, organic farming, and agricultural economics.

### Technical Infrastructure
- **Express.js Server** with Helmet, CORS, rate limiting, request validation, and centralized error handling
- **OpenRouter Integration**
- **Static Data Files** as placeholders for crop, climate, and market data

---

## [0.1.0] - 2024-08-05

### Added
- Initial project setup with logging, README, and basic project structure
