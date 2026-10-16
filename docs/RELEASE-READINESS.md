# AI Advisors 2.1.0 candidate

## October 16 local implementation

The remaining month of engineering work is implemented locally: captured summaries before the full discussion, copy controls, draft recovery, truthful request feedback, metadata search across all history, separate personal annotations/outcomes, and saved return points. Personal notes use a lazy `personal_annotations` collection; original `query_history` documents and exports are unchanged. There is no migration or history reset.

**Personal acceptance verified.** On October 16, 2026, Ryan verified the local personal-use loop (saving notes, search, and cold-return resumption via Continue saved work; verdict: "I think it looks good"). The current implementation passed **144 targeted Python tests in 4.07s**, **12 headless JavaScript tests**, and the full locked automated suite (**182 passed in 4.14s**). Independent source review found no remaining concrete defects after correcting in-flight note edit loss, hidden independent-advisor errors, and Resume failure wording. JavaScript syntax checks passed. The older automated and live results below retain their original dates and scope.

The targeted gate was:

```bash
CHROMADB_PATH=/private/tmp/advisors-month-gate-01a14680 ./.venv/bin/python -m pytest -q tests/test_history_store.py tests/test_personal_history.py tests/test_workspace_routes.py tests/test_result_view.py tests/test_routes.py tests/test_decision_panels.py tests/test_roundtable_retry.py tests/test_panels.py tests/test_briefing_service.py
node --test tests/test_workspace_controls.cjs
```

These checks cover old-record discovery, stable paging, metadata-only reads, separate note persistence, unchanged source bytes and exports, rejected or failed note saves retaining input, summary fallbacks, scoped recovery, request controls, clipboard fallback, and return-point handling. They do not establish personal effort savings or live model adherence.

The updated local app started successfully on port 8123. Read-only checks of `/`, `/history`, `/resume`, and `/openapi.json` passed; the schema exposes the personal-notes route. These HTTP checks did not submit a discussion or save notes and do not exercise browser JavaScript.

The full locked test suite (`uv run --locked pytest -q`) verified all 182 tests passed in 4.14s on October 16, 2026. GitNexus reindexed successfully (977 nodes, 2,271 edges, 49 clusters, 73 flows); its scan classified the combined tracked diff as breadth across shared routes and storage. Source review and targeted tests supplement it. Ryan's personal acceptance remains the next open step; this is not a release approval.

The private stopped-app snapshot is `.local-backups/month-20261016-171319`. The [personal use and restart check](PERSONAL-USE-CHECK.md) records its contents, restore precautions, one consolidated personal trial, and the verified test suite evidence. The [month plan](MONTH-PLAN.md) keeps unobserved personal tasks unchecked.

## October 15 candidate evidence

Prepared on 2026-10-15 for local personal use. The candidate is based on `main` at `c2c97f8` with local changes; it is not a published release or an immutable release artifact.

**Shipping status: HOLD.** Corrections for all three trial findings are implemented in source. Targeted regressions (**97 passed in 2.47s**) and the full locked automated suite (**151 passed in 3.18s**) have been verified on 2026-10-15. No second live roundtable was run, and saved trial `953adc1d` remains unchanged. Personal dictation/resumption acceptance is still unverified.

## What this version should improve

The purpose is useful advice with less reading and reconstruction. Compact decision-panel roundtables ask each advisor for a distinct contribution and later turns for new information only. The moderator owns one final Decision Check. AI Workflow & Delegation returns the assignment, checks, resume record, and a way to compare human effort. Accessibility & Effort returns the actual starter, checkpoint, dictation fallback, and a small trial. See the [demo walkthrough](DEMO-WALKTHROUGH.md) for observable quality criteria.

Successful advisor answers remain intact through retry. Reopening or exporting a saved result makes no model calls. New code does not rewrite an already saved answer. The existing Agriculture and Software formats remain available.

## Evidence and remaining checks

| Check | Evidence and limit |
|---|---|
| Compact synthesis, exports, saved results, retry | Ryan ran `uv run pytest -q tests/test_decision_panels.py tests/test_briefing_service.py tests/test_roundtable_retry.py`: **55 passed in 1.71s** on 2026-10-15. Provider calls were mocked. |
| Final review corrections | Added preservation of incomplete plain-text Decision Checks and rejection of empty text synthesis. All three additional regression cases passed in the full run below. The earlier 55-pass result predates these corrections and version-metadata changes. |
| Source review | Reviewed the changed catalog/prompt, roundtable, route, and export paths. No new runtime dependencies, frontend build, accounts, or storage migration were introduced. Business logic remains in `lib/`; the new handoff template uses Jinja escaping and the existing Candlelight styles. |
| Static file checks | Eight changed Python files parsed without imports; catalog JSON and project/lock TOML parsed; package, root lock entry, and FastAPI metadata all identify 2.1.0; local links resolved across nine changed/new Markdown documents. These checks do not execute the application. |
| Full automated release run | Ryan ran `uv run --locked pytest -q` on 2026-10-15: **139 passed, 3 failed in 4.62s**. The failures were route assertions expecting the older call without `advisor_context`, not failed application responses. The locked environment was accepted. |
| Test-only follow-up | Ryan ran the focused command below on 2026-10-15: **3 passed in 1.57s**. The assertions now require the exact captured Agriculture context. At that point, only assertions had changed since the full run; the combined evidence closed the automated gate for that revision. The trial corrections below came afterward. |
| Live output and saved/export flow | Trial `953adc1d` completed on the running 2.1.0 candidate on 2026-10-15. Save/reopen and both export contents passed; output grounding and two UI checks failed as detailed below. |
| Trial corrections | Capability grounding now uses the original user query, with the same rule for all four Accessibility advisors, captured discussion retries, structured synthesis, and text fallback. Save preserves heading IDs; Save and replay share both export controls for queries and roundtables. Targeted regressions passed (**97 passed in 2.47s** on 2026-10-15); full locked test suite passed (**151 passed in 3.18s**). These prompt changes do not prove future model adherence. |
| Correction static checks | Six edited Python sources parsed without application imports; four Jinja templates parsed and their template references resolved; `git diff --check` passed. These checks did not run tests, the application, or provider requests. |
| Personal dictation/resumption acceptance | Not performed by this browser trial. Actual input-method reliability, effort savings, and Ryan's ability to resume remain unverified; the content failure prevents treating the suggested commands as an implemented workflow. |

The full release-gate command is:

```bash
uv run --locked pytest -q
```

That full run is recorded above. Its three remaining failures were closed by the focused test-only rerun:

```bash
uv run --locked pytest -q tests/test_routes.py::test_roundtable_success tests/test_routes.py::test_roundtable_clamps_rounds_to_supported_bounds
```

`--locked` also refuses to silently update an out-of-date lockfile. Use the project environment; a global Python can lack FastAPI and `pytest-asyncio`. Report failures before repeating the command. GitNexus indexing is navigation evidence, not a substitute for this command or the live trial.

The focused rerun closed the earlier automated gate using both pieces of evidence; this is not a claim that a separate 142-pass full run occurred. Do not carry a passing count forward across later behavior changes. For the subsequent trial corrections, the targeted command was executed on 2026-10-15:

```bash
uv run --locked pytest -q tests/test_decision_panels.py tests/test_routes.py tests/test_experts.py tests/test_roundtable_retry.py
```

Evidence: **97 passed in 2.47s**. Additionally, the full automated suite was rerun with `uv run --locked pytest -q` resulting in **151 passed in 3.18s**.

The new cases check advisor and moderator request grounding (including text fallback and a captured profile), plus matching heading IDs and both export links after Save and replay. They mock provider calls and use isolated test storage. They do not establish live model compliance, browser accessibility, or personal effort savings.

## One focused live trial

1. Restart the app with `./start.sh`. Open the local page, choose **Accessibility & Effort**, keep its two default advisors, choose **Reduce repeated dictation**, and set **1 round**. Use only fictional or approved context. This normally makes two advisor requests and one synthesis request; fallback can add requests.
2. Inspect the actual output: short distinct advisor contributions, a usable starter, an exact checkpoint, a dictation fallback, a small effort comparison, and one closing Decision Check. No platform choice should be required just to try the template. Record any repeated or invented sentence rather than accepting output merely because it is short.
3. Save the result, reopen it, and compare Markdown and HTML exports. The handoff and closing points should remain readable without duplication. An incomplete closing must remain visible as saved text rather than disappear. Reopening/exporting should not start another discussion.
4. Use the starter for one small personal task, pause at its checkpoint, and resume from it using the usual input method. Note repeated background entries and practical interactions compared with the current routine. This is personal acceptance of this workflow, not a claim of assistive-technology conformance or measured medical benefit.

Do not manufacture a live rate limit: mocked tests cover scoped recovery. If a real provider failure occurs, keep completed answers, use the available scoped retry after its countdown, and save the recovered result as a new version. Changing the synthesis model affects a future synthesis request, not stored advisor answers.

### Observed trial — 2026-10-15

The previously running server reported 2.0.0 with hot reload disabled. It was restarted from this checkout, and `/openapi.json` confirmed version 2.1.0 before submission. The fictional **Reduce repeated dictation** example used Voice-First Workflow Designer and Effort Reduction Advisor for one round. Configured advisor model: `nvidia/nemotron-3-super-120b-a12b`; synthesis model: `qwen/qwen3.5-35b-a3b`. These identify this run, not a recommendation or claim of future model availability.

The result was saved as **`953adc1d`** and reopened through Saved Results. The transcript and synthesis's displayed text matched the pre-save text exactly. The server observed one `/roundtable` submission, followed by Save, history/replay, and export requests; no retry or regenerated advisor response was requested.

| Observed check | Result |
|---|---|
| Round/participants | Pass: one round, two completed advisor contributions, completed synthesis. |
| Compact structure | Pass: two bullets per advisor; four handoff sections and one final Decision Check; no repeated individual closing or platform-selection question. |
| Output grounding | **Fail:** the starter says “Save progress by saying 'save checkpoint'”; fallback says to invoke an existing alias. The original scenario supplies neither a configured voice command nor an alias. Advisor turns likewise propose automatic bookmarking/auto-save without established capabilities. The text checkpoint is useful, but the claimed execution/recovery path is unverified. |
| Save and replay | Functional pass: the result is stored and both advisor answers plus synthesis remain unchanged after reopening. |
| Markdown export | Pass: downloaded `/export/953adc1d`; all four handoff fields and closing points match the saved output, with one Decision Check section. |
| HTML brief | Pass: `/export/953adc1d/brief` renders, retaining the same handoff fields and closing points, with one Decision Check heading. |
| Named region immediately after Save | **Fail:** the roundtable region loses its accessible name. `save_success.html` replaces the header without the `roundtable-title` ID referenced by the parent region's `aria-labelledby`. Reopening restores the original named region. |
| Brief access after reopening | **Fail:** the saved-result roundtable header offers only Export Markdown. The Executive Brief link appears immediately after Save but is missing after replay; its observed URL still works. |

No provider failure occurred in this run, so it does not add live rate-limit recovery evidence. Both exports faithfully retain the unsupported claims; export fidelity is not evidence that the advice is sound. No extra model run was made to replace this evidence.

### Corrections implemented after the trial

1. **Capability grounding:** all four Accessibility advisors and both synthesis paths now distinguish the user's confirmed setup from requested features and advisor proposals. The discussion cannot establish a working command, alias, macro, automatic save, or restoration capability. Unknown setup defaults to reusable text and an explicit safe pause; generating a checkpoint is not saving one. The same discussion rule applies to a legacy captured advisor at request time without rewriting its snapshot.
2. **Named region after Save:** the replacement header now retains the correct query/roundtable class and heading ID referenced by the parent region.
3. **Exports after replay:** a shared saved-actions partial supplies Executive Brief and Markdown controls both immediately after Save and on reopening, for queries and roundtables.

Keep `953adc1d` as the failing acceptance example. Its two advisor answers, synthesis, and captured definitions were not changed. Mocked regression tests passed (**97 targeted / 151 full suite**). No live roundtable, provider call, or browser trial was performed for these corrections. A future live trial requires separate authorization and must produce a new result rather than rewrite this evidence.

## Upgrade and recovery

1. Stop the running app before backing up or replacing files. Keep a private copy of the current checkout, including local uncommitted changes, plus `.env` and the directory selected by `CHROMADB_PATH` (default `.chromadb`). The configuration backup contains a secret; keep it private.
2. Preserve the existing `.env`, saved-history directory, and `query_history` collection. This version requires no history reset or migration. For a new installation only, copy `.env.example` if `.env` does not exist and replace its key/model placeholders.
3. Run `uv sync --locked`, restart with `./start.sh`, and reopen one old saved result before doing the focused trial. Missing captured definitions in a legacy save should remain explicitly unknown; do not reconstruct them as historical fact.
4. If the candidate fails, stop it and return to the retained source/configuration/storage copies together. Avoid a Git reset that discards pending work. Older code may not understand the new specialized brief format, so keep the candidate backup and exports when evaluating a downgrade.

`OPENROUTER_SYNTHESIS_MODEL` is optional and requires a restart after changing `.env`. An unset value uses `OPENROUTER_MODEL`. Choose IDs available to the configured account; this release makes no promise about provider pricing, capacity, retention settings, or recovery time.

## Mechanic's source review

**MECHANIC'S VERDICT: PASS ✅** for the bounded source/architecture review and automated regressions (151 passed). The earlier live acceptance trial failed the checks recorded above; source corrections have passed all mocked tests. Live resumption acceptance remains pending; this is not a shipping approval.

**INSPECTION LOG:**

- [x] **No-Bloat:** no application `package.json`, Docker setup, frontend build, accounts, or new runtime dependencies introduced.
- [x] **Arsenal:** orchestration and export logic stay in `lib/`; no `main.py` or FastAPI imports found in `lib/`.
- [x] **Types:** structured handoff contracts and caller data reviewed; Python/JSON/TOML parsing passed. A type checker was not run.
- [x] **Candlelight:** existing screen-theme variable blocks retain the required palette; no visual acceptance claim is made from source alone.

**REQUIRED FIXES:** completed in the candidate:

- `lib/services/briefing_service.py` — preserve incomplete Decision Check text instead of removing an uncaptured closing.
- `lib/services/roundtable_service.py` — reject blank plain-text synthesis so retry remains available.
- Setup and release docs — align version metadata, avoid overwriting `.env`, replace fixed model examples, and describe captured prompt limits accurately.

**REFACTOR SUGGESTION:** a later cleanup could share the ordered handoff field/heading lists between the on-screen Markdown and export renderers. It is not required for this release; keep schema validation and stored format identifiers stable.

## Known boundaries

- Advisor snapshots record profile definitions. The current service adds discussion instructions and builds the synthesis request; retries are not exact replays of a historical provider envelope.
- Roundtable brevity, distinct perspectives, and the one-question rule are prompt guidance. Field validation bounds structured handoffs but does not prove factual accuracy or usable advice.
- These advisors use supplied text without independent browsing, file inspection, or evidence verification. Agreement among personas is not independent corroboration.
- A whole roundtable still waits for server-side completion or failure before updating the result. Compact contributions reduce requested output; streaming progress, context windowing, and usage accounting are outside this release.
- Saved state is client-submitted and shape-validated, not signed provenance. The app remains a local tool without user accounts; this review is not approval to expose it as a public service.

Automated evidence for the trial corrections passed (**97 targeted / 151 full suite** on 2026-10-15). Live adherence to the revised grounding instructions and personal resumption acceptance remain unverified. Publishing, deployment, and Git release actions remain separate owner actions.
