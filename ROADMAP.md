# AI Agriculture Advisors — Roadmap

Post-review snapshot.

**Last Updated:** 2025-11-29  
**Current Version:** 1.0.0  
**Status:** Working prototype (docs drifting from implementation)

> See `CHANGELOG.md` for release notes; several items there need alignment with reality.

---

## 🎯 Now (Fix drift & harden core)
- **Docs and release accuracy**: Sync README/CHANGELOG with the actual codebase (no MongoDB wiring, no streaming, package version still 1.0.0). Call out the Node.js 18+ requirement for native fetch and remove fictional performance metrics.
- **Provider coverage**: Either implement the Anthropic provider or drop the toggle; add config validation at boot and tests for provider selection/error paths.
- **API correctness tests**: Add integration tests for `/api/query` and `/api/roundtable` using a stub LLM provider; cover validation failures and transcript/summary shapes.
- **Data & placeholder cleanup**: Decide on `dataCollectionService.js`, `insightGenerationService.js`, `llamaHelper.js`, `dataPreprocessor.js`, and empty JSON files under `data/`; either implement minimal logic or remove references in docs.
- **Logging hygiene**: Stop writing logs to the repo root in dev/test; move to `./logs` or disable file transports under test to avoid dirty working trees.

---

## 🔧 Next (Product improvements)
- **Streaming responses**: SSE endpoint and UI rendering during generation to cut perceived latency.
- **Response caching**: In-memory cache keyed by normalized query + experts; surface cache hits to the UI to save API calls.
- **Data enrichment**: Optional weather/commodity lookups with location input; inject structured context into prompts.
- **Model selection UX**: Frontend selector for OpenRouter models with cost/speed hints; persist choice.
- **Roundtable polish**: Let users choose summary model/role and cap transcript length to avoid prompt bloat.

---

## 💾 Later (Platformization)
- **Persistence decision**: Add a real store (SQLite/Mongo) for query history/analytics or formally keep it stateless and update docs accordingly.
- **Auth & quotas**: Optional API keys per user plus rate-limit headers if exposed publicly.
- **Observability**: Request/LLM timing metrics and structured error codes for client handling.

---

## 🗂️ Cleanup
- **Unused code removal**: Drop dead references in README/CHANGELOG (database models, migrations, nonexistent middleware).
- **Config consolidation**: Single config module for rate limits, CORS origins, and logging paths; remove ad-hoc constants.
- **Type safety**: Consider TS or JSDoc annotations for controllers/providers to reduce prompt-shaping bugs.

---

## 📈 Current Stats

**What works:**
- Multi-expert `/api/query` and roundtable `/api/roundtable`
- OpenRouter provider with prompt templating per expert
- Frontend with markdown rendering, history, dark mode, export
- Helmet, CORS (default allow-all), rate limiting, basic validation/logging

**Gaps/risks:**
- Anthropic provider unimplemented; provider toggle can break startup
- Docs/CHANGELOG claim MongoDB, metrics, and features not present
- Empty services (`dataCollectionService.js`, etc.) and data files
- Limited automated tests (no route/controller coverage)
- Logs written to repo root during tests
