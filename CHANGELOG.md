# Changelog

## Unreleased — AI Advisors

- Preserved successful roundtable contributions and added scoped retries for missing advisors and synthesis, including saved-result recovery.
- Added a separate synthesis model setting and one same-model JSON-mode fallback for a confirmed OpenRouter upstream shared-pool limit, excluding the saturated provider. Other limits still pause calls and honor Retry-After; the countdown does not promise provider recovery.

- Added AI Workflow & Delegation, Accessibility & Effort, and Evidence & Judgment, each with four advisors and practical examples.
- Added a shared four-point Decision Check to those advisors and their roundtable syntheses, retaining captured closing points through saved results and exports.

- Generalized the application into configurable advisor panels, retaining Agriculture and adding Software.
- Replaced ten prompt-only subclasses with a validated JSON catalog and one advisor implementation.
- Added panel-specific examples and remembered browser selections while preserving the current question on panel changes.
- Captured advisor definitions with new saved results and included them in replay, Markdown, and HTML briefs; legacy results remain readable.
- Generalized moderator prompts and instructed synthesis to preserve unresolved disagreements and unknowns.


All notable changes to the AI Agriculture Advisors project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

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
