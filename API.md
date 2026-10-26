# Local API and HTML contracts

Current source: October 25 repair patch, 2.1.0 candidate; owner verification pending. This is a single-user loopback app at `http://localhost:8123`. No authentication/accounts are provided. Supported launchers bind `127.0.0.1` and allow local Host names.

## Request/error boundary

`GET /` sets an HTTP-only SameSite=Lax `csrf_token` cookie. Every mutating POST also requires its matching `csrf_token` form field. Requests normally use form encoding; file previews use multipart. Opening saved history, exports, comparison, library, or run status makes no model call.

Interactive validation and failures return HTML with truthful status: 400 invalid domain input, 403 CSRF, 404 unavailable record, 422 form/schema/corrupt saved record, 429 request rate limit, and 503 operation/storage failure. General errors carry `data-operation-error`, `HX-Retarget: #operation-status`, and `HX-Reswap: innerHTML`; Save errors target `#save-status`, legacy retry errors target `#roundtable-retry-status`. The client opts these fragments into error swapping while keeping existing results and input. Personal-note errors return their own preserved-value form (400/403/404/503) for outerHTML swap. Unexpected errors display a safe operation reference; no raw traceback/provider content is sent to the UI. Older read-route failures can return safe 500 fragments.

`429` includes `Retry-After: 60` for the local request-rate gate. `/query` allows 30/minute; roundtable/retry/follow-up/resume dispatch routes allow 10/minute. Provider limits and retry times are distinct and recorded with partial work. Polling does not reset provider work or spending bounds.

## Generate and recover

| Method/path | Inputs / behavior |
| --- | --- |
| `GET /` | Full page; optional validated `result_id` opens saved work. |
| `POST /query` | `query`, repeated `roles`, `panel_id`, CSRF; create individual answers. |
| `POST /roundtable` | Same plus `rounds` (1–5, clamped); needs at least two distinct roles. |
| `POST /roundtable/retry` | Legacy JSON `state` plus CSRF and uncertain-work acknowledgement when needed; starts a durable recovery run retaining successes. |
| `GET /runs` | Latest 20 working runs, no dispatch. |
| `GET /runs/{id}` | Checkpoint/status partial; browser polls active runs every two seconds. |
| `POST /runs/{id}/pause` | CSRF; prevents new calls after already dispatched work. |
| `POST /runs/{id}/resume` | CSRF and `acknowledge=true` when earlier work is uncertain; manual bounded attempt. |
| `GET /followup/{result_id}` | Preview selected context, bounded prior-result excerpt and optional outcome. |
| `POST /followup/{result_id}` | New `query`; booleans `include_context`, `include_result`, `include_outcome`; editable `prior_excerpt`; CSRF. Starts linked background work. |
| `POST /result/{id}/retry` | CSRF and `acknowledge=true` for uncertain prior remote work; creates a linked recovery version with completed answers reused. |

Generation accepts JSON-encoded `task_brief` (optional string fields: goal, decision, constraints, location_date, deliverable, background) and `sources` (list of label, passage, reference, date). A maximum of eight sources, 12,000 characters per passage, and 24,000 combined passage characters applies. Source IDs are assigned in captured order; present archive IDs must match that order. A reference is not fetched. Task fields allow 4,000 characters each; question allows 24,000. Model overrides `advisor_model` and `synthesis_model` are optional valid provider IDs; chosen models are captured at run creation. `parent_result_id` records deliberate lineage.

`background=true` returns a working-run fragment immediately; the UI uses it. API compatibility defaults to waiting for the bounded attempt. Optional `submission_key` deduplicates the same submitted state. A new key deliberately creates a new run. Normal generation requires roles from the selected validated panel; current plans cap roles at ten and reserve bounded synthesis-fallback capacity.

Defaults: 32 provider dispatches over the run including retries/fallback, 600 seconds per attempt, three manual attempts, 1,800 output tokens per call, and 120,000 prompt characters. Installation limits are documented in `.env.example`. Pause cannot revoke remote work. A pre-dispatch receipt, crash, or transport uncertainty is not proof of provider completion; manual resume acknowledgement protects against silent duplicate work.

## Save, annotate, find and organize

| Method/path | Contract |
| --- | --- |
| `POST /save` | Preferred: `run_id` and CSRF. Reads the authoritative journal, refuses active state, validates before writing. Optional `save_key` supports compatibility idempotency. |
| `POST /save` (legacy) | `query`, `result_type=query` and JSON `responses`, or `result_type=roundtable` and JSON `roundtable_data`; optional JSON `advisor_context`; CSRF. Validated imported client content is not authenticated generation provenance. |
| `GET /history` | `q`, nonnegative `offset`; filters `panel` (captured label), `status`, `tag`, ISO date `after`/`before`, `archived=true`. Searches all metadata and notes, not answer bodies. Ten-row UI pages, pinned first. |
| `GET /result/{id}` | Saved fragment with separate notes, captured evidence and controls; missing=404, corrupt=422. |
| `GET /work/{id}` | Full-page local return link, no provider call. |
| `GET /resume` | Optional `result_id`, otherwise unfinished-item choices; no provider call. |
| `POST /result/{id}/notes` | `title`, `status`, `next_step`, `last_step`, `blocker`, `outcome`, `outcome_rating`, CSRF. Source content stays immutable. |
| `POST /result/{id}/organize` | Comma-separated `tags` (12 max, 40 characters each), booleans `pinned`/`archived`, CSRF. Archive is reversible. |

Save success replaces only the named `.responses-header` or `.roundtable-header` via outerHTML and emits `resultSaved`. Save errors preserve that header/button and answer content. New IDs use full UUIDs or content-derived Save IDs; old short IDs remain valid. Repeat Save of the same keyed checkpoint returns the same logical record; changed checkpoint content is a separate version.

Note status is blank, undecided, decided, waiting, or tried. Outcome rating is blank, helped, needed_correction, not_useful, or not_tried. Limits: title 200; next/last step and blocker 2,000 each; outcome 4,000. Notes are not automatically submitted to providers or included in ordinary exports.

## Reuse and deterministic tools

| Method/path | Contract |
| --- | --- |
| `GET /library` | Reusable local starters/context, latest 100 comparison choices, quality cases and local tools; no dispatch. |
| `POST /library/{starter|context}` | `name`, `content`, CSRF; starters also use panel/role selections. Copies are selected into visible input deliberately. |
| `POST /source/excerpt` | Multipart `file` (`.txt`/`.md`, UTF-8, up to 100 KB), CSRF. Preview only; user chooses a bounded excerpt to add. |
| `GET /compare` | Required saved IDs `left`/`right`; compare inputs, profiles, receipts, outputs, personal evaluation. No automatic model rerun or score. |
| `POST /calculate/effort` | Enter minutes `manual`, `setup`, `review`, `correction`, `recovery`, CSRF. Decimal arithmetic; no quality/medical-benefit inference. |
| `GET /local-status` | Application/version/PID/managed instance nonce for loopback launcher identity. |

## Exports and additive import

| Method/path | Output |
| --- | --- |
| `GET /export/{id}` | Complete Markdown: exact question, full answers/transcript/synthesis, sources, profiles, recovery metadata. Notes excluded. |
| `GET /export/{id}/brief` | HTML executive brief, explicitly abridged. |
| `GET /export/{id}/brief.md` | Abridged Markdown brief. |
| `GET /export/{id}/json` | Versioned complete JSON archive; optional `include_notes=true` deliberately adds annotations. |
| `GET /export/{id}/report` | Complete decision report; optional `include_notes=true` adds separately labeled user notes/outcome. |
| `POST /archive/preview` | Multipart JSON `file` up to 5 MB, CSRF. Validate all rows before making a local preview; no saved-history mutation. |
| `POST /archive/import/{preview_id}` | CSRF; confirm additive import. Existing matching content/notes retained; conflicting IDs receive a new ID. Retry is safe for completed rows. |

Archive envelope: `{"archive_format":"ai-advisors","archive_version":1,"records":[{"result":{...},"annotations":{...}}]}`. One to 1,000 rows; annotations optional. Saved result schema is version 3; bounded readable versions 1/2 remain supported. Unsupported versions fail with an actionable error. Captured profiles, actual supplied source cards, optional structured synthesis and execution receipts remain distinct. A complete record can contain private content; no credentials are intentionally included. Backups containing `.env` are a separate private operation.

See [recovery](docs/RECOVERY.md) and [remediation evidence](docs/REMEDIATION-STATUS.md). These contracts describe prepared source, not a claim that the owner gate or real browser/provider acceptance has passed.
