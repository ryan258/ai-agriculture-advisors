# Changelog

All notable changes to the AI Agriculture Advisors project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Changed
- Removed the unimplemented Anthropic provider toggle; OpenRouter is now the only supported provider.
- Aligned README with the actual codebase (no MongoDB wiring, clarified Node 18+ requirement, updated structure and model options).
- Trimmed CHANGELOG to match current shipped features and version.
- Simplified LLM integration by removing `llamaService`/`llmFactory` indirection; controllers call the OpenRouter provider directly.

### Added
- Integration tests for `/api/query` and `/api/roundtable` using a stubbed LLM provider.

### Fixed
- Disabled file-based logging when `NODE_ENV=test` to avoid polluting the repo during test runs.

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
