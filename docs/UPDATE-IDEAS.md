# UPDATE-IDEAS — Turning AI Agriculture Advisors into a Professional-Grade Tool

**Date:** 2026-07-10 · **Against version:** 2.0.0
**Scope constraint:** Everything below stays inside the locked stack (FastAPI + Jinja2 + HTMX + ChromaDB, bare metal, no build step, no user accounts — see `docs/architecture/tech-stack.md`). Nothing here requires breaking an architectural contract.

---

## Review Summary — Where the Project Stands

**What's genuinely good:**

- Clean seam: `main.py` is a thin routing layer; all logic lives in `lib/` and passes the Arsenal test.
- Defensive routing, CSRF double-submit, slowapi rate limits, sanitized markdown — the security basics are real, not aspirational.
- Structured consensus (`generate_json` + JSON schema with plain-text fallback) is ahead of most hobby LLM apps.
- 51 passing tests, mypy strict-ish, accessible UI.

**The five structural weaknesses that block "professional tool" status:**

1. **Everything is a blind spinner.** A 3-round roundtable with 4 experts is **13 serial LLM calls** (12 contributions + consensus). At ~10s each on a free model, the user stares at a loader for 2+ minutes with zero feedback. This is the single biggest UX gap.
2. **No grounding.** Experts answer from model weights alone — no citations, no documents, no way to verify. Professionals can't act on unverifiable advice. Ironically, a vector database is already installed and its embeddings are **completely unused** (ChromaDB is used as a JSON key-value store).
3. **Unbounded transcript growth.** `roundtable_service.py` re-sends the full transcript to every expert every round — token cost grows O(rounds² × experts), and a 5-round × 10-expert session will overflow a 7B model's context and silently degrade.
4. **No resilience or cost awareness.** `llm_client.py` has no retry/backoff (free OpenRouter models 429/503 constantly), no token accounting, no per-call timing. One flaky call poisons a whole roundtable round with an `Error: ...` transcript entry.
5. **Save/history flow is client-trusted and unmanageable.** `/save` round-trips the entire result JSON through a hidden form field (tamper-able, heavy); `get_history()` loads **every record** then sorts in Python (`history_store.py:111`); there is no delete, search, or pagination.

Everything below is ranked. Tier 1 items compound — do them first; most Tier 2/3 items get cheaper after them.

---

## Tier 1 — Foundation (do these first)

### 1.1 Streaming roundtable progress (SSE)

- **Problem:** 13+ serial LLM calls behind one spinner (`main.py:191`, `roundtable_service.py:105`).
- **Proposal:** Convert `/roundtable` to Server-Sent Events. `run_roundtable` becomes an async generator yielding one event per contribution; the route wraps it in `StreamingResponse(media_type="text/event-stream")`. Frontend uses the **htmx SSE extension** (CDN script, no build step) to append each contribution card as it arrives, then swap in the consensus at the end. Keep the current non-streaming path as fallback for saved-result replay (`/result/{id}` already renders complete transcripts).
- **Where:** `lib/services/roundtable_service.py` (yield instead of accumulate), `main.py` (new `/roundtable/stream` route), `templates/partials/roundtable.html` (per-contribution partial already exists as a pattern in `response_card.html`).
- **Effort:** M · **Impact:** Highest of any item. Also do `/query`: fire each expert's card individually via `hx-swap="beforeend"` per completed task instead of `asyncio.gather`-then-render.

### 1.2 Retry with backoff + per-call metadata in `LLMClient`

- **Problem:** No retry on 429/503/timeouts; no token or latency data captured even though OpenRouter returns `usage` in every response (`llm_client.py:86` discards it).
- **Proposal:** In `generate`/`generate_json`: retry up to 3× on 429/5xx/`httpx.RequestError` with exponential backoff + jitter (stdlib `asyncio.sleep` + `random` — no tenacity dependency needed). Return a small `LLMResult` dataclass (`text`, `prompt_tokens`, `completion_tokens`, `model`, `latency_ms`) instead of a bare string; callers that only want text use `.text`.
- **Where:** `lib/engine/llm_client.py`; touch `Expert.query`, `contribute_to_discussion`, `_generate_consensus`.
- **Effort:** S–M · **Impact:** Reliability + unlocks 1.3, 2.4, 4.2.

### 1.3 Transcript windowing for roundtables

- **Problem:** Full transcript re-sent every call; O(n²) token blowup, context overflow on small models (`base.py:61`, `roundtable_service.py:119`).
- **Proposal:** Cap the context passed to `contribute_to_discussion`: always include round-1 opening statements + the last N contributions (N ≈ 2 × expert count), with a one-line `[earlier discussion omitted]` marker. Pure string slicing in `roundtable_service.py` — no summarization LLM call needed yet. Add a summarize-the-middle step only if quality measurably drops.
- **Where:** `lib/services/roundtable_service.py` (build windowed `transcript_text`).
- **Effort:** S · **Impact:** Makes 5-round × many-expert sessions actually work; cuts cost 3–5×.

### 1.4 Server-side save (kill the hidden-field round-trip)

- **Problem:** `/save` trusts client-posted JSON (`main.py:318` `json.loads(roundtable_data)`) — heavy hidden fields, tamper-able, and `save_success` template logic depends on it.
- **Proposal:** Persist every result server-side at generation time with `history_store.save_result(...)` inside the `/query` and `/roundtable` handlers, passing the returned `result_id` into the response template. "Save" button becomes `POST /save/{result_id}` that just flips a `saved: true` flag in metadata (or simpler: auto-save everything and rename the button "Pin"). Unpinned results older than N days can be pruned later.
- **Where:** `main.py` (both handlers), `lib/storage/history_store.py` (add `mark_saved`), templates (drop hidden JSON fields).
- **Effort:** M · **Impact:** Removes an integrity hole, shrinks pages, and makes "export this result" work on unsaved results too.

### 1.5 History store hygiene: sorted fetch, delete, full UUIDs

- **Problem:** `get_history()` fetches all records then sorts in Python (`history_store.py:111`); no delete; `result_id = uuid[:8]` invites eventual collisions.
- **Proposal:**
  - Store a numeric `ts` (epoch float) in metadata; fetch with `collection.get(limit=…)` and keep sort, but add a `where` filter path once tagging lands. (Chroma's `get` has no order-by — the in-Python sort is fine; the fix is not loading *documents*, which it already avoids, plus honest pagination via `limit`/`offset`.)
  - `delete_result(result_id)` → `collection.delete(ids=[…])`, exposed as `DELETE /result/{id}` (HTMX `hx-delete` + `hx-confirm`, CSRF via header) with a trash icon in `history_list.html`.
  - Use full `uuid4()` hex as ID; keep showing the first 8 chars in the UI only.
- **Where:** `lib/storage/history_store.py`, `main.py`, `templates/partials/history_list.html`.
- **Effort:** S · **Impact:** Closes the top item on ROADMAP "Now" list.

---

## Tier 2 — The Professional-Grade AI Upgrades

### 2.1 RAG knowledge base — make ChromaDB earn its keep

- **Problem:** Advice is ungrounded; professionals need citations. A vector DB is installed and its core feature (embeddings) is unused.
- **Proposal:** Add a `knowledge_base` collection in `lib/storage/`:
  1. `POST /documents` route accepting PDF/markdown/txt upload (`python-multipart` already installed; use `pypdf` for extraction — one small dependency, or start markdown/txt-only with zero new deps).
  2. Chunk (~800 tokens, stdlib splitting), embed with Chroma's default local embedding function (no API cost), store with source metadata (filename, page).
  3. At query time, retrieve top-k chunks for the query and inject into `Expert.build_prompt` as a `Reference material:` block with source tags; instruct experts to cite `[source: filename p.X]`.
  4. Render citations as a collapsible "Sources" footer on each response card.
- **Where:** new `lib/storage/knowledge_store.py`, `lib/experts/base.py` (`build_prompt` gains optional `context` param), `main.py` (upload + list routes), sidebar section in `index.html`.
- **Effort:** L · **Impact:** This is the feature that turns "toy" into "tool." Users load their own agronomy manuals, extension bulletins, farm records — answers become verifiable and farm-specific.

### 2.2 Model routing: per-expert model + user-facing model picker

- **Problem:** One global `OPENROUTER_MODEL` for every expert and the moderator. Consensus synthesis deserves a stronger model than a round-2 pest comment; users can't trade cost vs. quality.
- **Proposal:**
  - `Expert` gains an optional `model` property (default `None` → global setting); `LLMClient.generate` accepts `model=` override.
  - A `<select>` in the sidebar listing 4–6 curated OpenRouter models with cost/speed hints (static tuple in `main.py`, same pattern as `SUGGESTED_QUERIES`), posted with the form, validated against the allowlist server-side.
  - `MODERATOR_MODEL` env var so consensus can run on a stronger model.
- **Where:** `lib/engine/llm_client.py`, `lib/engine/config.py`, `lib/experts/base.py`, `main.py`, `index.html`.
- **Effort:** S–M · **Impact:** Direct ROADMAP "Next" item; pairs with 2.4's cost display.

### 2.3 Response caching

- **Problem:** Identical query + expert set = full re-spend on LLM calls.
- **Proposal:** Cache key = SHA-256 of `(normalized_query, sorted(roles), model)` — normalization already exists in `lib/services/_text_utils.py`. Store in a dict with TTL via a ~15-line stdlib helper (`dict` + monotonic timestamps), keyed per-process; it's a single-process bare-metal app, so no Redis. Bypass cache for roundtables (they're conversational, low hit-rate) — `/query` only. Show a subtle "cached" badge on hits.
- **Where:** `lib/services/query_service.py`.
- **Effort:** S · **Impact:** Free-tier survival; instant repeat demos.

### 2.4 Token & cost meter

- **Problem:** Zero visibility into what a session costs — disqualifying for professional use and embarrassing for an AI showcase.
- **Proposal:** With `LLMResult` from 1.2, sum tokens per request; render a footer line on every response/roundtable partial: `“7 calls · 12,340 tokens in / 3,210 out · ~$0.004 · 48s”`. Price table = static dict for the curated models from 2.2 (approximate is fine; label it). Persist totals into the saved result so exports show cost too.
- **Where:** `lib/services/query_service.py`, `roundtable_service.py`, new line in `responses.html` / `roundtable.html`.
- **Effort:** S (after 1.2) · **Impact:** High trust signal, trivial once 1.2 lands.

### 2.5 Semantic history search

- **Problem:** History is a 10-item chronological list; finding "that nitrogen discussion from March" means clicking through.
- **Proposal:** When saving (1.4), also store the query text as the Chroma *document* with default embeddings (today the document is a JSON blob — keep the blob in metadata or a parallel collection). Add a search box above the history list: `GET /history/search?q=…` → `collection.query(query_texts=[q], n_results=10)` → same `history_list.html` partial via `hx-get` + `hx-trigger="keyup changed delay:400ms"`.
- **Where:** `lib/storage/history_store.py`, `main.py`, `index.html`.
- **Effort:** M · **Impact:** Second feature that finally uses the vector DB as a vector DB.

### 2.6 Follow-up questions on a result (conversation continuity)

- **Problem:** Every query is one-shot. Professionals iterate: "OK, but what if my soil pH is 5.2?"
- **Proposal:** Add a follow-up input under each rendered result. `POST /query/followup` includes the prior query + responses (server-side, fetched by `result_id` — depends on 1.4's auto-save) as context in `build_prompt`. Cap context to the immediately previous exchange — this is follow-up, not full chat; full multi-turn chat is out of scope (would drag in session state the architecture bans).
- **Where:** `lib/experts/base.py`, `lib/services/query_service.py`, `main.py`, `responses.html`.
- **Effort:** M · **Impact:** Biggest single jump in perceived intelligence per line of code.

### 2.7 Disagreement matrix / expert comparison view

- **Problem:** With 4+ expert responses the user does the synthesis manually; the roundtable consensus hides *where experts diverged*, which is exactly what a professional wants to see.
- **Proposal:** After `query_experts`, one extra `generate_json` call with a small schema: `{agreements: [str], disagreements: [{topic, positions: [{expert, stance}]}], confidence_notes: [str]}`. Render as an "Expert Alignment" card above the individual responses. Make it opt-in via a checkbox ("Analyze agreement") to avoid an always-on extra call.
- **Where:** new function in `lib/services/query_service.py` (reuse the `generate_json` pattern from `roundtable_service.py`), new partial.
- **Effort:** M · **Impact:** Differentiating feature; no comparable tool shows structured disagreement.

---

## Tier 3 — Product & Platform

### 3.1 Custom expert builder (data-driven experts)

- **Problem:** The 10 expert classes are 20-line boilerplate clones (`agriculture.py` et al.); adding an expert requires a code deploy. Professionals want "my region's viticulture consultant."
- **Proposal:** Two steps:
  1. **Refactor:** Replace the 10 classes with one `Expert` dataclass + a `experts.json`/`experts.py` data table (role, label, system_prompt). Registry builds instances from data. Deletes ~200 lines, changes zero behavior. Trace all imports and call sites of `Expert` and `expert_registry` before this widest-touching refactor.
  2. **Feature:** "Create custom advisor" form (name + expertise description → optionally LLM-expand into a full system prompt) persisted in a Chroma `custom_experts` collection, loaded into the registry at startup and on create. Custom experts get a badge in the sidebar and a delete control.
- **Where:** `lib/experts/*` (collapse), `lib/storage/`, `main.py`, `index.html`.
- **Effort:** M (refactor S, feature M) · **Impact:** Turns a fixed demo into a configurable tool; the refactor pays for itself even if the feature never ships.

### 3.2 Printable / PDF executive brief

- **Problem:** The HTML brief (`briefing_service.py`) can't be handed to a stakeholder as a file.
- **Proposal:** Add a `@media print` stylesheet to the brief template + a "Print / Save as PDF" button calling `window.print()`. Native browser PDF export — zero dependencies, no weasyprint/wkhtmltopdf on bare metal.
- **Where:** brief template/CSS in `lib/services/briefing_service.py` assets.
- **Effort:** S · **Impact:** Cheap, closes the report-delivery loop.

### 3.3 JSON API mode

- **Problem:** AI professionals will want to script against this; today every endpoint returns HTML partials.
- **Proposal:** Content negotiation on the existing routes: if `Accept: application/json` (or `?format=json`), return the service-layer dict directly (`query_experts` / `run_roundtable` already return clean dicts — the seam makes this nearly free). Document in `API.md`. Guard with a static `API_KEY` env var checked via header ("basic script only" auth is explicitly allowed by `tech-stack.md`). Skip OpenAPI-first redesign — FastAPI already auto-generates docs for these.
- **Where:** `main.py` (small branch per route), `API.md`.
- **Effort:** S–M · **Impact:** Makes the tool composable into other pipelines.

### 3.4 Observability: timing middleware + structured logs + health check

- **Problem:** `app.log` is unstructured f-strings; no request timing; no health endpoint; debugging a slow roundtable means guesswork.
- **Proposal:**
  - `GET /healthz` returning `{status, model, chromadb: ok}` (S).
  - ASGI middleware logging method/path/status/duration per request (stdlib `time.perf_counter`, ~10 lines).
  - Switch `lib/utils/logger.py` to a JSON formatter (stdlib `logging` + `json` — no structlog) with `event`, `duration_ms`, `tokens` fields fed by 1.2.
- **Where:** `lib/utils/logger.py`, `main.py`.
- **Effort:** S · **Impact:** ROADMAP "Later" item, but cheap enough to pull forward.

### 3.5 Result tagging & filtering

- **Problem:** As history grows past ~30 items, the flat list fails even with search.
- **Proposal:** Optional free-text tags on save (comma-separated input), stored in Chroma metadata; filter chips above history using `collection.get(where={"tags": {"$contains": …}})`-style filters (Chroma metadata is flat — store as `tag:<name>: true` keys or a single comma-joined string matched in Python; keep it dumb).
- **Effort:** S–M · **Impact:** Only after 2.5; skip if search proves sufficient. (YAGNI candidate — listed because "comprehensive," flagged as deferrable.)

### 3.6 Suggested follow-ups & query refinement chips

- **Problem:** Static suggestion chips never change; blank-page problem returns after the first query.
- **Proposal:** The consensus/response schema gains a `suggested_followups: [str] (maxItems: 3)` field (one schema edit, no extra LLM call); render as chips under each result that pre-fill the query box (the chip JS in `index.html` already does exactly this).
- **Effort:** S · **Impact:** Session depth for near-zero cost.

---

## Explicitly Skipped (and why)

| Idea | Why not |
|---|---|
| User accounts / OAuth | Banned by `tech-stack.md`. Static API key (3.3) covers scripting. |
| Docker / K8s deploy | Banned. `start.sh` + systemd unit note in README is the bare-metal answer. |
| React/SPA rewrite for streaming | htmx SSE extension does it with a CDN script tag. |
| Redis / external cache | Single-process app; in-memory TTL dict is correct until it isn't. |
| Full multi-turn chat sessions | Drags in server-side session state the architecture bans; follow-ups (2.6) capture 80% of the value. |
| LangChain / agent framework | The hand-rolled orchestration in `lib/services/` is smaller than the adapter code would be. |
| Fine-tuning / custom models | RAG (2.1) + model routing (2.2) dominate on cost-benefit. |

---

## Suggested Sequencing

| Phase | Items | Theme |
|---|---|---|
| 1 | 1.2 → 1.3 → 1.5 → 1.4 | Reliability & data integrity (each is small; 1.4 last since it touches templates) |
| 2 | 1.1 → 2.4 → 2.2 | Visible speed + cost transparency |
| 3 | 2.1 → 2.5 | Grounding — the "professional tool" pivot |
| 4 | 2.6 → 2.7 → 3.6 | Depth & differentiation |
| 5 | 3.1 → 3.3 → 3.4 → 3.2 | Platformization |

Per `CLAUDE.md`, every implementation phase must map imports and call sites before edits. The wide-blast items are `LLMClient.generate` (1.2, every expert call depends on it) and the `Expert` base/registry (3.1).
