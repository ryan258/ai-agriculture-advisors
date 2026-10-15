# Changelog

Notable changes to AI Advisors. Entries below 2.1.0 retain the project's earlier name and history.

## [Unreleased] — 2.1.0 candidate

Release evidence and remaining acceptance checks are recorded in [release readiness](docs/RELEASE-READINESS.md). This candidate has not been published.

Automated acceptance before the trial corrections on 2026-10-15: 139 cases passed in the full run, followed by 3 passing route cases after a test-only snapshot-assertion correction. Targeted results for the subsequent corrections below are pending. Live output and personal acceptance are recorded separately in the readiness note.

Live trial `953adc1d` completed save/reopen and both exports on 2.1.0. It exposed assumed voice/alias capabilities, a lost accessible region name after Save, and a missing Executive Brief control after replay. All three corrections are implemented in source; the saved trial remains unchanged. Shipping acceptance is on hold pending verification; no further live roundtable was run.

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
