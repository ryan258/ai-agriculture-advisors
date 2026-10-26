# Remediation status — October 25, 2026

**Updated October 26, 2026. State: owner automated continuation, local doctor, stopped-app backup, managed startup, live connectivity diagnostic, and an authorized read-only browser pass completed; broader personal acceptance pending.** This register supersedes the baseline review's proposed sequence. Ryan requested all identified repairs and next actions, with test execution and GitNexus reindexing left to him. The agent performed source review, formatting, read-only graph impact, and the explicitly authorized read-only browser pass below. No tests, mypy run, application startup, live model trial, real-history migration, production restore, or saved-record edits were performed by the agent.

The original branch was `main` at `6e2a033`. Original owner edits to the Source change checks sections in AGENTS.md and CLAUDE.md are preserved. No staging, commit, push, deployment, publication, account change, or cross-project sync is part of this work. The agent did not open or migrate existing production history.

## Next action

The app reported successful managed startup at [AI Advisors](http://localhost:8123). The authorized read-only browser pass and owner-run provider-connectivity diagnostic are complete. No further terminal verification command is needed for this returned result. Refresh an existing browser tab to pick up the markup and focus corrections if needed.

The next useful observation is one small personal workflow using a question Ryan can assess, or one fictional case from the [quality pack](QUALITY-PACK.md). Start with one advisor and Submit Query, review the visible work plan before any deliberate provider request, assess the answer, save a new result and a next-step note, then reload and reopen it. This tests usefulness and the real save/return loop through owner-controlled use. The agent's browser authorization remains read-only; it does not authorize this generation or record mutation.

Provider answer quality, the separately configured synthesis model, write/restart recovery, real-data restore rehearsal, and personal input-method observations remain separate work. No extra automated test run, live diagnostic repeat, or GitNexus reindex is requested for this documentation update.

## Owner-returned verification

Ryan's supplied `./advisors check` transcript reports **1 failed, 221 passed in 3.62s** on the accumulated uncommitted repair patch. The only failure was `test_source_ids_and_disagreements_resolve_only_to_captured_evidence`: the test expected the word `completed`, while the validator correctly rejected an unavailable contribution with `A disagreement cited a contribution that did not complete`.

The assertion now matches `contribution that did not complete`; application validation is unchanged. The check helper accepts `--target` to rerun a selected test before continuing through the typing and JavaScript gates.

Ryan's subsequent targeted continuation reports **1 passed in 0.54s** for that corrected evidence-reference test. Mypy then checked 11 source files and reported two argument-type errors at the save and import `Collection.add` calls in `lib/storage/history_store.py`. The JavaScript gate was not reached. Both embedding batches were then given Chroma's declared `PyEmbeddings` annotation; the actual `[[0.0]]` values and persistence behavior are unchanged.

Ryan's latest `./advisors check --target tests/test_harmony.py::test_archive_round_trip_and_conflict_are_additive` run passed all three gates: **1 Python test passed in 0.65s**, **Mypy found no issues in 11 source files**, and **17 headless JavaScript tests passed with zero failures, skips, cancellations, or todos**. This verifies the save/import typing repair and the targeted automated continuation. The initial full Python run and subsequent targeted runs are separate evidence; no new full-suite execution is claimed. Subsequent browser and connectivity observations are recorded separately below.

Ryan also refreshed GitNexus: the analyzer reported successful indexing with 1,317 nodes, 3,496 edges, 61 clusters, and 109 flows, alongside a truncation warning. Read-only CLI inventory binds that index to this checkout and commit `6e2a033`. Impact for `HistoryStore.save_result` and `HistoryStore.import_record` still returned UNKNOWN; save impact explicitly reports five unresolved receiver call sites. Direct source inspection confirmed both methods are reached through the route storage dispatcher and by save/import fixtures. No zero-caller result is treated as an all-clear.

**October 26 owner diagnostic:** `./advisors doctor` returned `Configuration: valid` and found FastAPI 0.128.0, ChromaDB 1.4.1, HTTPX 0.28.1, and Jinja2 3.1.6. It explicitly reported no provider request. No diagnostic issue requires a source correction. This establishes local configuration/dependency availability, not startup, provider connectivity, or answer quality.

Ryan's October 26 analyzer transcripts report successful indexing with **1,320 nodes, 3,503 edges, 61 clusters, and 110 flows**. The final run reports zero changed, added, or deleted files and 115 unchanged file rows preserved. An earlier run in the supplied output contains a truncation warning; successful indexing does not resolve the previously recorded graph coverage limits or establish application acceptance.

**October 26 owner backup/startup:** `./advisors backup && ./advisors start` reported a private stopped-app snapshot at `.local-backups/advisors-20261026T145305Z-928b9a`, followed by confirmed managed startup at `http://localhost:8123`. This is owner-returned evidence of command completion and startup identity confirmation; backup contents, restore integrity, rendered pages, saved-work behavior, and provider quality were not independently checked by the agent. The snapshot can contain credentials; browser drafts are excluded. The latest supplied analyzer run reports **1,320 nodes, 3,504 edges, 61 clusters, and 110 flows**, again with a truncation warning.

**October 26 owner live diagnostic:** `./advisors doctor --live` returned valid configuration, the same four installed dependency versions, and `One live request returned usable text; answer quality is not established.` This confirms a usable response on that configured provider/model path. It does not verify the separately configured synthesis model, roundtable/structured-output behavior, actual answer quality, or the save/recovery loop. The agent made no provider request and did not repeat the diagnostic.

The latest owner analyzer transcript reports successful indexing with **1,321 nodes, 3,505 edges, 61 clusters, and 110 flows**. Its warning explicitly reports `truncated: true`, `entryPointCandidatesDropped: 0`, and `entryPointsUnexplored: 11`. Indexing completed, but flow coverage remains partial. No further analyzer run is requested for the documentation-only evidence update.

The stopped-app backup prerequisite was completed for this activation. For later snapshots, stop the app first; a prior direct uvicorn process needs Ctrl-C in its terminal, and managed stop only signals a verified managed instance. Follow [recovery](RECOVERY.md). A broader dictation/print or write/recovery trial requires separately bounded authorization. A live quality trial is a separately deliberate small-budget action.

## Authorized read-only browser pass — October 26

Ryan explicitly authorized page loading, saved-history search/reopen, keyboard navigation, and console inspection, with no saved-record edits or provider requests. The pass used an isolated browser context on the owner-started app at localhost:8123 and a desktop viewport of 1200 by 593 CSS pixels. Browser convenience state stayed in that isolated context. No application server was started or restarted by the agent.

Observed working behavior:

- The main page, local CSS/JavaScript libraries, history, resume, working-run list, and reusable-library requests returned HTTP 200. HTMX, Marked, and DOMPurify were available locally; computed page colors matched Candlelight.
- History search narrowed existing results and reopened an existing legacy roundtable with its question, saved marker, analysis, and notes form. Reload restored its return point without submitting work; Alt+R reopened it.
- Alt+F focused history search; Tab/Enter activated a saved result with a visible focus outline; Alt+Q focused the question; the skip link moved focus to main content; reopening moved focus into the result.
- All observed application requests were GETs. No save, annotation, reusable-item mutation, import, new run, retry, or provider request was made.

Four corrections were implemented and verified on a fresh load:

| Finding | Correction and browser evidence |
| --- | --- |
| Saved Results used an unattached `<label>`. | Use an `<h2>` while retaining its ID and styling. The live DOM now has the heading and zero unattached labels. |
| The two reusable-item `name` fields triggered person-name autofill warnings. | Explicit `autocomplete="off"` on starter/background names. Both attributes are present in the rendered page. |
| Implicit `/favicon.ico` returned 404. | Add a small local Candlelight SVG and explicit icon link; `/static/favicon.svg` returned HTTP 200. |
| Reopening a long result focused its region but scrolled into the middle of its notes. | Focus without implicit scrolling, then align the result region to the viewport start. The heading moved from about 1249 pixels above the viewport to its top. Existing working-run polling remains excluded from this focus/scroll branch. |

After correction and reopening, the browser reported no console errors, warnings, or issues. The inspected page had no duplicate IDs, no unattached labels, and no horizontal document overflow at the observed viewport. Template graph impacts returned UNKNOWN; direct source tracing confirmed the root/index/base rendering path, the `/library` partial, its element-ID consumers, and the result-swap focus handler before edits.

This was a focused browser check, not a full accessibility or device audit. Actual notes/save failure behavior, write/restart recovery, real dictation/assistive technology, printing, provider quality, and real-data restore remain unverified for this patch. Prior owner automated results predate these template/static corrections; no automated suite was rerun by the agent. The corrections were checked in the running browser and `git diff --check` passed.

## Corrections F01–F24

“Prepared” means source and relevant regression fixtures exist, not that they passed. Acceptance remains pending where execution or personal observation is required.

| ID | Implemented solution | Evidence to obtain / material limit |
| --- | --- | --- |
| F01 | Save errors retarget only `#save-status`; the named result header and Save action remain. Success replaces the header and emits `resultSaved`. | Server protocol regression plus focused actual HTMX failure/retry observation. |
| F02 | Reject null/blank/unsupported provider content and withheld/truncated finishes; accept supported text blocks. Validate nested JSON schema and current consensus types instead of coercing nulls. | MockTransport/schema fixtures; no current live adherence claim. |
| F03 | Shared versioned result boundary validates Save, replay, and import before mutation; corrupt records return a distinct invalid-record error. Normal UI Save reads its server-owned journal checkpoint. | Malformed transcript/nested-field fixtures and save/replay tests. Legacy supported records stay readable without rewriting them. |
| F04 | Default Markdown export preserves exact question, full responses/transcript, qualifications, code, links, structured synthesis, sources, profiles, and metadata. Abridged briefs are explicitly separate. | Complete-content sentinels and archive round trip. |
| F05 | SQLite journal writes pre-dispatch receipts and per-contribution checkpoints; background work survives page navigation. Interrupted/uncertain calls require manual acknowledgement on resume. | Cancellation/reopen fixtures; real process restart observation pending. No promise to cancel remote work. |
| F06 | Per-result browser note drafts restore across swaps/navigation. Only confirmed matching saved snapshots clear drafts; newer dictation survives an older save. Unsafe navigation is blocked when durable draft storage fails. | Pure recovery tests plus existing note-control tests; actual browser storage/navigation observation pending. |
| F07 | Cap calls, output tokens, prompt characters, deadline, and manual attempts. Preflight reports planned work; pause stops new calls; provider waits are honored. Fallback dispatches count against the same lifetime run budget. | Bounds/attempt/pause fixtures. Monetary cost is unknown; dispatched calls can still incur charges after a local interruption. |
| F08 | New `query_history_v3` collection has no embedding function and every write supplies an inert embedding. Old `query_history` is read without migration or dimension changes. | Explicit no-embedding write and legacy byte/vector preservation fixtures. |
| F09 | Capture model IDs, request fingerprint/rule version, timestamps/duration, HTTP/finish status, and returned provider/model/usage when available. Preserve selected models at run creation. | Pre-dispatch and uncertain-transport receipt fixtures. Receipts are not a full HTTP envelope; provider metadata can be missing. |
| F10 | Label generated participants separately from actual supplied sources. Source cards retain exact passages/reference/date/ID. Reject unavailable generated source IDs in answers and synthesis. | Source-reference boundary fixtures. Valid IDs do not prove semantic support. |
| F11 | Pin and vendor HTMX, Marked, DOMPurify and licenses locally; record SHA-256 inventory; show visible dependency failure and raw-text fallback. | Local assets returned 200 and all three libraries initialized in the authorized browser pass. Network-disconnected and dependency-failure observations remain pending; no vulnerability-free claim. |
| F12 | Form/CSRF/validation/limit/storage failures return truthful HTML 400/403/422/429/503 responses with preservation targets. Note failures retain their submitted form values. | Route/error/swap protocol regressions; real HTMX integration pending. |
| F13 | Managed, compatibility, and direct launch paths bind loopback; local Host allowlist. | Source reviewed; owner managed startup reported success at localhost October 26. Compatibility/direct launch observations remain separate. |
| F14 | Root-anchored paths and locked launcher; dotenv is loaded as data. Validate required provider settings, URL/model/port and bounds. | Owner local doctor and managed startup passed October 26; launch from another directory remains pending. Existing explicit history path is retained. |
| F15 | Offload blocking Chroma/SQLite route operations to worker threads. Cache complete metadata rows with save/annotation invalidation and count tracking; keep older metadata searchable. | Existing bounded-batch history fixtures. Cold scans still cover all metadata; no measured latency/scaling claim. An owner-sized performance observation remains open if actual history is slow. |
| F16 | Full UUID/content-derived IDs, accepted legacy IDs, submission keys, Save idempotency, disabled duplicate controls, and parent-result lineage for deliberate recovery. | Duplicate submission/Save and lost-response fixtures. A changed checkpoint is a new version. |
| F17 | Agriculture roles explicitly lack live feeds, measurements and action tools; current facts/diagnoses/rates/compliance require supplied evidence and relevant context. | Fictional quality cases and prompt inspection; live factual/domain quality remains unverified. |
| F18 | README/current register/API/contribution/recovery/architecture docs reconciled; historical reports are labeled; October 16 owner observation narrowed to recorded save/search/reload scope. | Source/document review; no fresh release acceptance inferred from old results. |
| F19 | Private stopped-app backup with inventory/hashes/config/source/version metadata; restore into a new destination after integrity/path checks; no overlay. | Owner stopped-app backup reported completion October 26. Real-data restore rehearsal is pending. Browser drafts are excluded. |
| F20 | Central result contract, execution context/run service, workspace store, record export, consensus extension schemas, presentation models, and isolated legacy brief parser. Existing callable reexports retained. | Owner focused typing passed across 11 source files; automated evidence is recorded above. Main routes remain the framework edge; no new service process. |
| F21 | Content-free/classified operational logs; safe UI operation references; offline doctor default, explicit one-request live option with cleanup/nonzero failure. Access logs disabled in supported launchers. | Owner local and one-request live diagnostics passed October 26. Provider quality and broader execution behavior remain separate. |
| F22 | Shared Candlelight variables; lighter meaningful small text; semantic Markdown tables; larger full checkbox rows; elapsed seconds removed from live announcements; restore focus after note save. | Focused desktop keyboard navigation and Candlelight rendering observed; result reopening scroll corrected. Real dictation, contrast audit, print, note-save focus, and assistive-technology acceptance remain pending. |
| F23 | Add deterministic server-side Save failure/swap/import/error fixtures and headless draft-recovery tests alongside existing controls. | A real HTMX read-only search/reopen/reload pass completed. Actual Save/notes failure swapping remains outside its scope. |
| F24 | Align agent/contribution policies with current catalog, JS convenience state, development-only Node and owner-run gates. Deduplicate response cards; centralize theme variables; preserve owner source-check paragraph/generated graph block. | Source review; rendered layout and regression gate pending. |

## Enhancements E01–E18

The implemented scope stays local and single-user. None of these features automatically contacts a model merely by opening a saved item, preparing a case, or inspecting an export.

| ID | Implemented entrypoint / solution | Limit / next observation |
| --- | --- | --- |
| E01 | Optional compact task brief in question form, snapshotted into run/result. | Free text stays usable; context limits are enforced. |
| E02 | Named local reusable background snippets with explicit selection into visible input. | No personal note is included automatically. Editing a snippet does not change history. |
| E03 | Stable source ledger with exact supplied excerpts, dates/references, and validated IDs. | No autonomous retrieval or opened-link claim. |
| E04 | Structured options view against supplied alternatives/criteria, with pros/cons/unknowns/source IDs. | No unexplained numeric score; model interpretation still requires review. |
| E05 | Unresolved differences with attributed viewpoints, completed turn IDs, and distinguishing checks. | A valid turn reference does not prove a faithful paraphrase. |
| E06 | Linked follow-up preview with selected context/prior analysis/outcome; missing-answer retries reuse successes. | New provider work is explicit; the parent is immutable. Retry uses captured profiles and current execution rules. |
| E07 | User-managed question starters with panel/role choices and current-question capture button. | Built-in catalog/examples remain separate. |
| E08 | Decision-report download with explicit personal-note inclusion choice and separately labeled user outcome. | Review private content before sharing; default exports omit notes. |
| E09 | Complete versioned JSON/Markdown, duplicate/conflict preview and bounded additive import with recoverable note writes. | Conflicting IDs get new records. Existing local notes take precedence on identical records. |
| E10 | Status/panel/date/tag filters, pinning and reversible archive. | Permanent deletion and semantic search remain outside this patch. |
| E11 | Two saved-run comparison with questions, context/profiles, receipts, outputs and recorded evaluation. | No automatic rerun, scoring, or fair-benchmark/independence claim. Choices show the latest 100 saved items. |
| E12 | Optional outcome category and reason; selected past outcome can inform a linked follow-up. | The user assesses usefulness; generated advice never marks itself successful. |
| E13 | Deterministic Decimal calculator compares entered manual minutes with setup+review+correction+recovery. | Narrow personal-effort use; no speculative domain calculators or quality inference. |
| E14 | UTF-8 `.txt`/`.md` preview up to 100 KB; selected excerpt limited before adding a source card. | No PDF/OCR/office ingestion platform. Quoted instructions remain untrusted input. |
| E15 | Display configured/per-run selected models and work plan; bounded overrides; receipts show returned usage if available. | Pricing remains unknown; model availability is provider-dependent. |
| E16 | `./advisors` start/status/stop/doctor/backup/restore/check, compatibility launcher and discoverable Alt shortcuts. | No global alias or voice command was installed. Actual input-method suitability remains open. |
| E17 | Six fictional selectable quality cases and separate support/usefulness/disagreement/uncertainty/effort/recovery rubric. | Structural fixtures prepared; no automatic live case bank execution. |
| E18 | Stable `/work/RESULT_ID` and validated index parameter reopen saved work. | Local bookmark depends on the local server and retained data. |

## Evidence boundaries and risks

The original pre-edit graph reported **CRITICAL** impact for `LLMClient.generate` and **HIGH** for `generate_json`, roundtable normalization, consensus normalization/rendering and brief construction. Callers span advisor queries/discussion, synthesis/fallback, persistence-facing routes, and exports. Profile/brief model moves and service calls were also traced. Framework/test entrypoints often returned UNKNOWN; route decorators, template references, imports and fixtures were inspected directly. Ryan's subsequent index refresh is recorded above; its unresolved receiver boundaries remain explicit. No commit or pre-commit graph clearance is claimed.

The owner automated continuation, local doctor, stopped-app backup, managed startup, one-request live connectivity diagnostic, and focused read-only browser pass completed with the scope recorded above. Remaining observations concern integration across the journal and real browser save/retry loop, the synthesis model and actual provider semantic quality, dictation/assistive-technology behavior, cold-return effort, rendered print, and production restore. Neither a graph score nor passing mocked tests closes those observations.

### Historical evidence retained

- October 16 repository record: 182 full Python tests passed; a bounded owner save-notes/search/immediate reload-resume observation was recorded. It does not establish a measured break or all input methods.
- October 25 baseline review: 58 focused Python tests, 12 headless JS tests, and five-file typing passed before these changes. Its probes demonstrated the defects addressed above.
- October 25 implementation: no executed test result, browser/live result, or real-data recovery result is claimed. Formatting and source review are not behavior verification.
