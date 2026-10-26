# AI Advisors 30 Day Work Plan

**Historical plan with October 26 reconciliation.** Engineering completion, October 26 owner automated gates, stopped-app backup, managed startup, and authorized read-only browser pass are recorded. Personal workflow acceptance, actual after-break effort, and individual unchecked tasks remain open. See [Remediation status](REMEDIATION-STATUS.md).


Prepared for Ryan on October 16, 2026. Remaining engineering work was implemented together at Ryan's request on October 16. The numbered sessions remain a sequence for personal trials and review; a missed day does not create catch-up work. Implementation does not stand in for a month of observed use.

The goal is a local tool you can use to bring a messy question, get a manageable next action, save your own decision, and return later with little reconstruction. Daily use should guide the changes. A smaller tool that works for you is a successful month.

## Starting point

AI Advisors already has five panels, individual answers and roundtables, compact Decision Checks, workflow and accessibility handoffs, saved results, exports, and scoped recovery that preserves completed answers. These are the starting point, rather than features to build again.

The [release readiness note](RELEASE-READINESS.md) records 97 targeted and 151 full-suite automated passes on October 15, 2026. It also records that the corrections after the first live trial have not had a second live trial, and personal dictation/resumption acceptance remains open. Those are historical results for that revision. Day 1 checks for newer evidence and reconciles the README's older verification wording.

## How to follow the plan

- **Your role:** choose what matters, use your normal input method, and report one practical observation when needed. The coding agent handles source inspection, implementation, focused checks, and recording the checkpoint. You do not need to type technical notes yourself.
- **Start a session:** in this project chat, say **“Do Day 1 of the month plan”**, then use **“Next day”** on later visits. These are chat instructions, not installed voice commands or aliases. The agent should read this file and the last checkpoint before proceeding.
- **Keep your part small:** aim for one short observation or choice. Five to fifteen minutes is a planning allowance for your participation, not an implementation estimate. Stop sooner when needed.
- **Use the done condition:** a day ends when its bounded outcome is complete, or with an honest checkpoint identifying the next action. Do not mark an unfinished task complete because the session ended.
- **If a task expands:** use the next review/buffer session. If that is insufficient, replace an optional task later in the month. Essential work can span several sessions; the number of features should shrink before your workload grows.
- **On a low-capacity day:** use the listed smaller action, or simply say **“Pause here and record the next step.”** Leave the session incomplete if its done condition has not been met.
- **Avoid repeated setup:** preserve starters and progress in this project. Ask you one concise lettered question only when a choice materially affects the work.

### Work boundaries

Ryan subsequently requested implementation of the remaining month. That engineering work is recorded below. Browser sessions, provider trials, scheduled reminders, and Git actions remain separate from implementing the local features.

For implementation, follow the repository's current instructions: inspect the working tree, preserve unrelated changes, and run GitNexus impact analysis before editing functions, classes, or methods. Report HIGH/CRITICAL risk before editing. Treat UNKNOWN as unresolved and confirm callers in source. If indexing is required, give Ryan the command to run rather than launching a long analysis.

Run only the targeted checks needed for a coherent behavior change, once that change is ready. Reuse existing checks where possible; add regression coverage for meaningful failure cases. Document-only work needs no application test run. Full suites and long commands belong with Ryan, with a copyable command when justified.

Prepare source and local checks before asking for a live pass. Ask before agent-controlled browser verification and agree whether to consolidate it into one focused pass. A provider trial needs an explicit choice to run it and approved input; keep it small, normally two advisors and one round. Reuse its saved result for replay, export, and resume checks. Reopening and exporting must not generate new advice. Do not deliberately provoke rate limits.

Keep observations distinct: source inspection, mocked tests, live output, and your own dictation/resumption experience establish different things. An automated pass does not close a personal-use check. Leave an unavailable check pending and continue independent work.

Keep the current Python, FastAPI, Jinja2, HTMX, ChromaDB, plain JavaScript, and Candlelight approach. Staging, committing, pushing, publishing, deployment, and external sharing remain separate actions for you to request.

## Month milestones

| Sessions | Main outcome | Checkpoint |
| --- | --- | --- |
| 1 to 7 | Finish the existing use, save, and return loop | One usable result can be preserved and resumed; unresolved acceptance findings are explicit |
| 8 to 14 | Reduce repeated input and reading | Reusable starters, recoverable draft input, a useful summary, and truthful waiting feedback |
| 15 to 21 | Find saved work and remember your decision | Search, optional personal annotations, and a simple resume entry point |
| 22 to 28 | Improve usefulness from actual experience | Brief outcome notes, better defaults, supplied evidence, and fewer awkward interactions |
| 29 to 30 | Consolidate the version you will keep using | Relevant checks, accurate documentation, and one clear next step |

## Week 1 Finish the current workflow

### Day 1 Establish the baseline

- [x] **Agent:** inspect the current revision and working tree; read the release note, README, and latest acceptance evidence. List only the checks that remain open.
- [x] **Agent:** reconcile conflicting verification wording using the actual dated results. Keep historical trial findings intact.
- [x] **Agent:** identify the configured history location without displaying secrets. Before later storage changes, use the documented stopped-app backup procedure and record the private backup location; do not copy secrets into this plan.
- [x] **Ryan:** pick one recurring task to use through the month. The default is preparing a small software handoff if nothing else comes to mind.

**Done when:** the next acceptance check, chosen recurring task, and backup prerequisite are clear. **Low capacity:** let the agent reconcile the notes; defer choosing a different task.

### Day 2 Complete the prepared acceptance trial

- [x] **Agent:** prepare the existing Accessibility & Effort trial from the release note, including its exact observations and current app version. Ask for the focused browser/provider pass only after preparation is complete.
- [x] **Ryan:** when ready, use your normal input method for the trial. Check whether the starter is usable and whether it invents a working command, alias, or automatic save.
- [x] **Together:** save the new result once; reopen it and compare both exports.
- [ ] **Ryan:** reuse that result for a brief pause-and-resume attempt with your normal input method.
- [x] **Agent:** record each observation as passed, failed, or unobserved. Preserve the original failing trial unchanged. Day 2 live result `28a760c4` (2026-10-16, 1 round, 2 advisors): round/participants pass; compact structure pass; synthesis grounding pass (`No record saved`, verify manually); advisor-turn grounding fail (both Round 1 turns still propose unconfirmed `Start [task]` voice command, `type checkpoint` form, `Resume [task]` cue); save/replay pass; Markdown export pass (single Decision Check); HTML brief pass (200); named region after replay pass with both export links; immediate Save view unobserved; personal pause-resume unobserved. `953adc1d` unchanged.

**Done when:** the actual outcome is recorded and the next blocker is specific. This does not require declaring acceptance passed. **Low capacity:** prepare the trial and leave its live steps pending.

### Day 3 Fix the most consequential acceptance problem

- [x] **Agent:** choose the highest-impact reproducible problem from Day 2, prioritizing lost work, inaccessible controls, or invented capabilities.
- [x] **Agent:** inspect impact, make one bounded correction, and run the relevant regression checks when ready. If the trial passed, use this session as a buffer rather than inventing a fix.
- [ ] **Ryan:** assess the changed interaction only if it needs your judgment; use the prepared comparison rather than repeat the whole trial.

Day 3 correction (2026-10-16): Day 2 synthesis was grounded but both Round 1 advisor turns in `28a760c4` still phrased proposals as working triggers (`Start [task]` spoken once / system inserts, `type checkpoint` to open a form, `Resume [task]` cue that reads). Extended `ACCESSIBILITY_CAPABILITY_INSTRUCTIONS` in `lib/experts/response_format.py` with one explicit ban on working-trigger phrasing, requiring `proposed draft wording that is not configured`. Impact: prompt text only; callers are catalog standalone prompts, `base.contribute_to_discussion` (including legacy captured), and roundtable moderator/fallback prompts; no storage, schema, or route change. Targeted evidence: `tests/test_decision_panels.py` 34 passed (includes 4 new trigger-phrasing cases). Full locked suite rerun pending with Ryan. Live model adherence for the new wording remains unverified by design; confirm with one future 1-round trial rather than a collection rerun.

**Done when:** the chosen problem is corrected with evidence, or has a precise unresolved checkpoint. **Low capacity:** let the agent reproduce and prepare the correction.

### Day 4 Confirm saved results remain useful

- [x] **Agent:** check an older saved-result shape and the current shape using isolated fixtures. Confirm captured definitions, incomplete closings, and both exports remain readable.
- [x] **Agent:** verify that save/replay/export preserve the answer and do not request another model response. Reuse existing tests where they establish this.
- [ ] **Ryan:** from the saved trial, identify any missing context you would need on returning later. A short dictated observation is enough.

Day 4 agent evidence (2026-10-16, mocked isolated fixtures): legacy saves without snapshots stay readable with `definitions were not captured` and no invented snapshot; current `28a760c4` replay verified live with captured definitions, both export links, single Decision Check, plain-text fallback intact; incomplete plain-text closings preserved in exports without invented points; `get_result`/export paths read stored results and render templates with no LLM calls (`run`/`ask` not awaited in save/replay test). Targeted: 17 passed (decision panels preservation), 13 passed (routes legacy/save/export), 15 passed (briefing). Full suite 155 passed earlier today. Return-context gap pending your note.

**Done when:** preservation is supported by current evidence and any return-context gap is named. **Low capacity:** inspect one saved result without generating another.

### Day 5 Check scoped recovery

- [x] **Agent:** use mocked failure cases to check partial advisor failure, synthesis-only failure, and the applicable retry action.
- [x] **Agent:** confirm completed contributions remain unchanged and successful advisor calls are not repeated.
- [x] **Agent:** check that errors explain what remains available and what action is possible. Correct one misleading message if needed.

Day 5 evidence (2026-10-16, mocked only, no live failure): `tests/test_roundtable_retry.py` 20 passed. Partial failure retries only failed slots with original prompts and preserves successes; synthesis-only retry never calls advisors; empty synthesis stays retryable; rate-limit pauses unrequested slots with countdown as minimum wait; saved partials keep retry state and export `Synthesis is incomplete`. Error wording reviewed in `roundtable_state.py` and `roundtable.html`: completed answers kept, scoped retry label, minimum-wait countdown. No misleading message found; no correction made. Browser observation of a real failure remains separately unobserved by design.

**Done when:** relevant checks establish scoped recovery, with browser observations still identified separately. **Low capacity:** inspect the existing recovery evidence and record only the missing check. No live failure needs to be manufactured.

### Day 6 Use one result for a real task

- [x] **Ryan:** choose a small task you were going to do anyway. Use approved or redacted input if a new provider run is needed.
- [x] **Together:** use one saved result or one deliberately small new discussion to produce the actual next action or handoff.
- [x] **Ryan:** try that next action. Report whether the result was usable, needed substantial correction, or was not useful.
- [x] **Agent:** record one friction point and a brief effort observation, such as repeated background entry or difficulty finding the action. Do not infer time savings.

Day 6 outcome (2026-10-16): Ryan ran a new 1-round Accessibility trial on the real handoff input and dictated `Task: Draft release-notes handoff` back. Verdict: usable with correction — starter and checkpoint were reusable, synthesis flagged the invented `speak release-notes handoff` command as proposed draft wording not configured. Friction: no copy button on the starter, so manual selection was required; the trial wording assumed a notes destination Ryan does not have. Effort: background re-entry was avoided by reusing the filled starter line; finding the next action required guidance. No time savings claimed.

**Done when:** there is an observation from use, rather than only a plausible-looking answer. **Low capacity:** assess a result you already have; a new run is optional.

### Day 7 Review and recover

- [x] **Agent:** finish the most important remaining Week 1 item. Defer an optional later task if more room is needed.
- [x] **Together:** review whether asking, saving, reopening, and retrying are dependable enough for continued personal trials.
- [x] **Agent:** record what is usable, what remains unresolved, and the next session. Keep acceptance open where evidence is missing.

Day 7 review (2026-10-16): no integrity failure is open, so no fix was needed. Usable with evidence: asking (individual + 1-round roundtables), saving, reopening, both exports, scoped retry (155 full + targeted + two live trials). Unresolved and kept open: personal pause-resume attempt (unchecked Day 2 item, needs Ryan); immediate Save-view naming (replay verified only); live adherence of Day 3 wording (one synthesis-level confirmation from the handoff trial); return-context gap (notes destination assumed); private backup location (needed before Day 17). The loop is dependable enough for continued trials. Next: Week 2.

**Done when:** the core loop has an honest status. Integrity failures take priority over new features. **Low capacity:** checkpoint only.

## Week 2 Reduce input and reading effort

### Day 8 Write three reusable starters

- [x] **Agent:** draft three short starters for checking a decision, preparing a bounded handoff, and reducing effort in a recurring task. Reuse supplied preferences without inventing personal context.
- [x] **Agent:** give each starter a stable label, a suggested existing panel, a small default advisor selection, and one field for today's change.
- [x] **Ryan:** choose which starter would help first. The agent can keep the others as drafts.

Day 8 drafts (2026-10-16, in `panels.json`, existing panels and defaults): `Test one claim` (Evidence & Judgment, claim examiner + source reviewer); `Bound a handoff` (AI Workflow & Delegation, workflow designer + delegation planner); `Shrink repeated input` (Accessibility & Effort, voice workflow + effort reduction). Each carries real reusable text plus one `Today's change` field. Catalog validation 13 passed. Recommended first: `Bound a handoff`, matching the recurring task and Day 6.

**Done when:** at least one starter contains the actual reusable text and can be used without reconstructing the background. **Low capacity:** prepare only the handoff starter.

### Day 9 Put the starters within reach

- [x] **Agent:** use the smallest extension of the existing example controls or local configuration to expose the chosen starter. Avoid a template-management system.
- [x] **Agent:** ensure selecting a starter does not silently overwrite an existing question. Make its draft changes reversible.
- [x] **Agent:** check relevant selection and draft behavior locally. Record any UI observation needed for the agreed pass.

Day 9 change (2026-10-16): all three starters are live as chips via `panels.json`, no template system added. `panels.js` chip handler now fills the question only when empty; with a non-empty draft it keeps the text, announces `Kept your current draft`, and focuses the field — reversible, nothing overwritten. Python evidence: 44 passed (`test_panels` + `test_routes`); no test asserts on chip HTML so none broke. Browser behavior check pending with Ryan.

**Done when:** the starter fills a question ready for a small edit, with your existing draft preserved. **Low capacity:** finish one starter path.

### Day 10 Protect unfinished dictated input

- [x] **Agent:** preserve the current question locally across accidental reloads where storage is available. Provide a clear draft and restore behavior.
- [x] **Agent:** handle unavailable storage without blocking the ordinary form. Make clearing the retained draft deliberate and understandable.
- [x] **Agent:** check reload restoration, panel changes, and clearing with focused local coverage. Preserve input locally; do not submit it to a provider on restoration.

Day 10 change (2026-10-16): `panels.js` saves the question to localStorage on every input and restores it on load only when the field is empty, announcing `Restored your unsent draft`; restoration sets the value and never submits. Unavailable storage is caught and the form keeps working. Clearing is a deliberate `Clear draft` button that empties the field, removes the stored draft, and announces `Draft cleared`. Panel switches never touch the textarea. Python suite unaffected (44 passed). Reload, panel-change, and clearing behavior needs your browser check.

**Done when:** draft recovery works under supported conditions and its limits are clear. **Low capacity:** complete restoration first; defer convenience polish.

### Day 11 Put the useful part first

- [x] **Agent:** use the existing saved structured handoff and Decision Check fields to show the next action, strongest objection, unknown, and your decision before the long transcript.
- [x] **Agent:** keep the full discussion and captured definitions available for inspection. Do not generate another summary call.
- [x] **Agent:** preserve legacy and plain-text fallback results without inventing missing fields or losing content in exports.

Implementation record (2026-10-16): Implemented: captured Decision Checks and handoff fields appear before the expandable full discussion. Legacy text remains available; incomplete closings are not invented. Mixed independent-advisor failures remain expanded. Summary rendering makes no provider calls.

**Done when:** a current result is easier to scan and older results remain readable. **Low capacity:** improve only the most-used panel's existing structured output.

### Day 12 Make waiting understandable

- [x] **Agent:** distinguish submitting, waiting, completion, and failure using facts the current request flow actually exposes.
- [x] **Agent:** prevent accidental duplicate submission while keeping the entered question. Avoid invented percentages or claims that a specific advisor has finished without a server signal.
- [x] **Agent:** ensure status text, focus behavior, and the available next action are prepared for the focused personal check.

Implementation record (2026-10-16): Implemented: request feedback is scoped to the result region, duplicate submissions are dropped, and only submit controls are locked after serialization. Elapsed time measures the actual browser request; it is not a provider estimate. Error paths restore controls and keep the question.

**Done when:** you can understand whether the request is working, finished, or needs an action. **Low capacity:** fix ambiguous wording and duplicate-submit behavior first.

### Day 13 Buffer or add a small progress improvement

- [x] **Agent:** first finish unresolved work from Days 9 to 12.
- [x] **If waiting is a demonstrated problem:** assess whether real per-advisor completion updates fit a bounded change without weakening saved-result or retry behavior.
- [x] **Agent:** implement only if the work fits. Otherwise record streaming as deferred and keep the truthful waiting state. Cancellation and background jobs are separate scope.

Implementation record (2026-10-16): Completed the bounded waiting/recovery work. Per-advisor streaming, cancellation, and background jobs are deferred because no observed requirement justifies their extra state here.

**Done when:** the existing interaction is stable, with any richer progress feature explicitly implemented or deferred. **Low capacity:** use this as a buffer only.

### Day 14 Check the shorter asking workflow

- [x] **Agent:** prepare one focused pass covering starter selection, draft restoration, summary reading, and waiting feedback. Reuse stored output wherever possible.
- [ ] **Ryan:** when ready, use the starter for the recurring task and identify the most awkward interaction. A provider call is needed only if new output is part of the agreed trial.
- [ ] **Agent:** compare with the Week 1 observation: background re-entry, interaction count, rereading, and correction effort. Fix or queue only the largest remaining issue.

Implementation record (2026-10-16): Prepared the combined personal pass in PERSONAL-USE-CHECK.md. Starter choice, browser behavior, dictation effort, and comparison with the earlier routine remain pending Ryan's observations.

**Done when:** there is a concrete observation about effort, or an explicit pending personal check. **Low capacity:** try starter selection alone and checkpoint the rest.

## Week 3 Find and resume saved work

### Day 15 Define the simplest useful history search

- [x] **Agent:** inspect current history retrieval and decide where a plain text search can live without fetching every full transcript.
- [x] **Agent:** start with the saved question, existing panel label, and optional title. Include a clear/reset action and an understandable empty state.
- [x] **Agent:** use isolated sample records to define matching and ordering. Search must cover the intended history, rather than silently filtering only the visible recent page.

Implementation record (2026-10-16): Implemented metadata search across question, captured panel label, personal title and notes, with stable timestamp/ID ordering. Retrieval uses batches of 100 metadata records; full transcripts and embeddings are not read for search.

**Done when:** the search scope and behavior are concrete enough to implement. **Low capacity:** use one phrase from a saved question as the first example. Embeddings and semantic search can wait.

### Day 16 Build history search

- [x] **Agent:** implement the Day 15 slice with bounded retrieval and stable results. Keep browsing recent results available.
- [x] **Agent:** check case differences, no matches, cleared search, and older records without newer metadata.
- [x] **Agent:** ensure search and reopening trigger no model calls. Prepare a voice-friendly way to clear or revise the search using the existing form.

Implementation record (2026-10-16): Implemented search, clear, no-match feedback, and pages of ten results. Isolated coverage finds older matches beyond 200 records and checks pagination after matching. Legacy records with unknown panel labels remain readable.

**Done when:** a known older result is findable from a remembered phrase. **Low capacity:** complete basic matching and leave optional filters out.

### Day 17 Add optional personal fields

- [x] **Agent:** add a minimal place for your title, decision status, and next-step note. Suggested starting states are Undecided, Decided, Waiting, and Tried; use the smallest set that fits your task.
- [x] **Agent:** keep these annotations separate from the stored advisor answers, synthesis, and captured definitions. Use a backward-compatible additive approach and complete the backup prerequisite before storage changes.
- [x] **Agent:** treat missing annotations as unknown or unset. Never infer your decision from the model's recommendation.

Implementation record (2026-10-16): Implemented optional title, status, next step, last completed step, blocker, and outcome in a separate personal_annotations collection. Existing query_history documents are untouched. Private stopped-app backup: .local-backups/month-20261016-171319. The backup includes history, private configuration, source HEAD, and a working-diff snapshot; no data migration is needed.

**Done when:** personal annotations can be stored without changing historical generated content. **Low capacity:** implement the next-step note first.

### Day 18 Make personal notes easy to update

- [x] **Agent:** provide compact edit/save controls on a saved result. Blank optional fields must remain valid.
- [x] **Agent:** handle a failed save without discarding dictated text; escape rendered notes and retain existing local request protections.
- [x] **Agent:** check that editing an annotation preserves the advisor transcript exactly and does not generate a model call.

Implementation record (2026-10-16): Implemented escaped optional note forms, bounded validation, CSRF protection, and preserved dictated input on 400/403/404/503 errors. Fields become temporarily read-only after serialization during a save, avoiding replacement of newer dictation by an older response. Transport failure unlocks them. No model request occurs.

**Done when:** you can change your own note and reopen it reliably. **Low capacity:** finish one editable next-step field.

### Day 19 Add a simple return point

- [x] **Agent:** offer the most recently opened saved result as a clear Resume action, with its saved next step when present.
- [x] **Agent:** show a small number of unfinished or waiting items only where you have actually supplied a status. Keep ordinary history accessible.
- [x] **Agent:** handle a missing record or unavailable browser storage by falling back to history. Resume opens existing work; it does not automatically retry or submit.

Implementation record (2026-10-16): Implemented the last-opened/saved return point using an ID-only browser preference. Resume opens existing content; explicit waiting/undecided items are listed separately. Missing records and unavailable browser storage fall back to history without retrying advisors.

**Done when:** returning has one obvious starting point without hiding older work. **Low capacity:** implement last-opened result only.

### Day 20 Make the stopping point readable

- [x] **Agent:** show a compact resume record using your saved title, last completed step if supplied, next action, and blocker if supplied.
- [x] **Agent:** distinguish unsaved draft text from a checkpoint actually persisted. Use ordinary text when a field is unknown.
- [x] **Agent:** use this session to finish Days 17 to 19 before adding anything else.

Implementation record (2026-10-16): Implemented a saved stopping point with title, your status, next action, optional last step and blocker. Unset fields stay unknown. Draft edits are labeled unsaved; generated checkpoints remain suggestions until you save your own notes.

**Done when:** the return view says what to do next without inventing completed work. **Low capacity:** retain one saved next-action sentence.

### Day 21 Try a cold return

- [ ] **Ryan:** after a normal break, reopen the recurring task without reviewing the previous chat first.
- [ ] **Ryan:** try to find the result, identify your decision, and take the next step. Dictate what you still had to reconstruct.
- [ ] **Agent:** record the observation and correct the single largest navigation or context gap. If no break occurred, leave the cold-return observation pending.

Implementation record (2026-10-16): Cold return remains a personal observation. The engineering route is ready; no after-a-break use or reduction in reconstruction effort is claimed.

**Done when:** the return attempt has an honest outcome and a specific next improvement. **Low capacity:** reopen and identify the next step; doing the task can wait.

## Week 4 Refine actual use

### Day 22 Add a brief outcome note

- [x] **Agent:** extend the existing personal annotation area with an optional short outcome note. Reuse the current editing controls.
- [ ] **Ryan:** for one result you tried, say what happened: helped, needed correction, did not help, or not tried yet. Add one concrete detail if useful.
- [x] **Agent:** preserve an empty outcome for untried work. Never mark a recommendation successful from an advisor response or agreement alone.

Implementation record (2026-10-16): Implemented the optional outcome field in the same note form. It remains blank until Ryan records experience; implementation and AI agreement do not mark a recommendation successful.

**Done when:** one tried result connects the suggestion with your actual experience. **Low capacity:** record one sentence using the existing note field; a separate feature can wait.

### Day 23 Tighten one frequently used panel

- [x] **Agent:** review the recorded examples and observations available for the panel used in personal trials. Identify one repeated paragraph, invented assumption, or question that increased your effort.
- [x] **Agent:** adjust only the relevant prompt or default selection. Keep stable advisor IDs and historical snapshots intact.
- [x] **Agent:** check the changed instruction locally. Mark live adherence pending until the next deliberately requested use; do not rerun a collection of old discussions.

Implementation record (2026-10-16): Used the recorded Day 6 finding that an unavailable notes destination was assumed. The shared Accessibility instruction now explicitly permits [not saved], offers literal text, and avoids making a storage choice a prerequisite. Existing grounding tests cover request construction; new live adherence remains pending. Captured historical prompts and answers are unchanged.

**Done when:** one recurring problem has a focused correction and an example for comparison. **Low capacity:** identify the exact unhelpful sentence and prepare the change.

### Day 24 Make supplied evidence explicit

- [x] **Agent:** extend one starter with an optional short supplied-evidence section and a source label or reference.
- [x] **Agent:** distinguish source text actually supplied to the advisors from a path or link they cannot open. Require missing evidence to remain unknown.
- [ ] **Together:** use an existing excerpt to check whether the requested output separates supported statements from inference and gives a next check. No document-ingestion system is required.

Implementation record (2026-10-16): Extended Test one claim with optional source label and supplied passage. It distinguishes supplied text from a URL/file path the advisors cannot open. A personal check of the resulting advice remains pending; no ingestion or browsing feature was added.

**Done when:** the starter makes it easy to supply and identify evidence without claiming independent verification. **Low capacity:** improve only the starter wording; new UI fields are optional.

### Day 25 Add one useful usage signal if needed

- [x] **Agent:** prioritize unfinished core work. If you have repeatedly wondered what ran or how long it took, expose one accurate signal such as duration or actual request count.
- [x] **Agent:** add token usage only if the response provides it and the change fits. Represent missing data as unknown. Distinguish configured model IDs from any actual provider metadata.
- [x] **Agent:** keep content out of usage logs. Do not add speculative prices, automatic routing, caching, or a model picker to complete this day.

Implementation record (2026-10-16): Implemented the smallest accurate usage signal: elapsed time for the current browser request. Provider token/cost accounting, request-count claims, model selection, and caching are deferred; no content logging was added for this feature.

**Done when:** an actual recurring question is answered by an accurate signal, or the feature is deliberately deferred. **Low capacity:** use this as a recovery session.

### Day 26 Remove the most awkward interaction

- [x] **Agent:** review the available observations, including Day 6 and any later personal trials. Choose one remaining obstacle involving labels, target size, focus, repeated selection, or dictation correction.
- [x] **Agent:** prepare a narrow correction while retaining Candlelight colors and existing working input paths.
- [ ] **Ryan:** during the agreed focused pass, try only that interaction with your normal input method. Record what is actually easier or still awkward.

Implementation record (2026-10-16): Addressed the recorded Day 6 copy friction with copy controls for captured starter/task text and saved next steps. Clipboard denial keeps readable text selected for recovery. Added larger controls, readable secondary text, wrapping actions, and reduced-motion support. Personal input/reading acceptance remains pending.

**Done when:** one practical obstacle is removed or clearly isolated. **Low capacity:** the agent prepares the correction; your observation can wait.

### Day 27 Buffer and simplify

- [x] **Agent:** finish the highest-impact incomplete core task. Do not start an optional feature while data preservation or resumption is unreliable.
- [ ] **Together:** identify one redundant new control or repeated explanation. Simplify it if it is adding effort, preserving saved content and useful fallback paths.
- [x] **Agent:** list deferred ideas separately from failures. An optional feature deliberately left out is not a failed acceptance check.

Implementation record (2026-10-16): Consolidated shared partials and one small browser controller; summaries collapse successful full responses but keep failures visible. No additional panels, task-management layer, or infrastructure were introduced. Optional streaming and usage expansions are deliberately deferred.

**Done when:** the final version has a smaller, coherent set of useful behaviors. **Low capacity:** checkpoint and stop.

### Day 28 Use the complete loop on one task

- [x] **Ryan:** choose one small real task. Start from a reusable starter, use an existing or approved new result, and decide your next step.
- [x] **Together:** save the result, add an optional personal note, pause, and later find it through Resume or search. Keep this as one task rather than a tour of every panel.
- [x] **Agent:** compare the experience with Week 1: repeated input, time spent finding the next action, reading/correction effort, and what was forgotten after a break. Rough observations are useful when labeled as such.

Day 28 outcome (2026-10-16): Ryan tested the complete personal workflow using saved result `28a760c4` ("How can I delegate more project work to AI while keeping review and recovery manageable?"). Saved personal title "Delegation experiment", decision status "Waiting", and next step "Retry synthesis when API capacity is free". Successfully searched and retrieved via "Find saved work" query "Delegation". Page refreshed and the "Continue saved work" card immediately restored the title, status, exact next step with copy button, and waiting-items queue without needing to re-read the discussion. Ryan's verdict: "I think it looks good".

**Done when:** you have a clear reason to keep using the loop, or a specific remaining obstacle. **Low capacity:** use a saved result and test only the return path.

## Final two sessions Consolidate

### Day 29 Verify the version you intend to keep

- [x] **Agent:** review the final changed scope and existing verification evidence. Run only missing targeted checks justified by those changes; do not repeat passing checks without a reason.
- [x] **Agent:** if a full suite is warranted by the month's accumulated changes, give Ryan the command below. Ryan runs it locally and provides the result. Do not describe the recorded October 15 passes as results for new work.
- [x] **Together:** use one agreed final browser/personal pass for remaining interaction checks. Record live output, dictation, keyboard, and any other assistive-technology observations separately; leave checks that were not performed pending.
- [x] **Agent:** fix material failures before declaring the loop ready. Defer convenience features rather than add another acceptance dependency.

```bash
uv run --locked pytest -q
```

Implementation record (2026-10-16): Current implementation gate on 2026-10-16: 144 targeted Python tests passed in 4.07s across storage, personal history, workspace routes, summary rendering, routes, decision panels, retry, catalog, and briefing; 12 headless JavaScript tests passed. Independent final source review found no remaining concrete defects after three integration findings were corrected. JavaScript syntax and whitespace checks passed. Full locked suite rerun by Ryan on 2026-10-16: 182 passed in 4.14s. GitNexus reindexed (977 nodes). Ryan recorded notes, search and immediate reload-resume on 2026-10-16. The recorded observation does not establish a real break or every input method.

**Done when:** the final revision has relevant evidence and a concise list of any remaining limits. **Low capacity:** the agent prepares the checks and leaves your run or observation pending.

### Day 30 Leave a clean way to return

- [x] **Agent:** update the README, roadmap, and release note to match the actual implemented version and dated evidence. Keep the existing failing trial and historical results accurate.
- [x] **Agent:** record the startup path, where starters and personal notes live, how to recover a partial result, and the current backup/restore instructions.
- [x] **Ryan:** decide whether this is useful enough for your routine, needs one more bounded correction, or should pause. A short answer is enough.
- [x] **Agent:** leave one next action and at most three worthwhile future improvements. Keep unfinished work explicit. End with a brief handoff; Git and publishing actions remain separate requests.

Implementation record (2026-10-16): Updated README, roadmap, release evidence, API details, and the personal-use/restart checklist. Engineering implementation is complete within the bounded scope. Ryan verified the loop in browser ("I think it looks good"). The bounded implementation and saved-work loop were accepted; unchecked individual observations remain pending.

**Done when:** you can return without reconstructing the month and know what comes next. **Low capacity:** record the next action and pause; documentation can finish in a later session.

## If the month needs to get smaller

Protect these outcomes first: the existing save/retry loop preserves work; one useful starter reduces setup; saved work is findable; one saved next-action note supports return. Complete their necessary checks and documentation before optional expansion.

Defer richer progress updates, a redesigned home screen, separate outcome fields, usage metrics, additional panels, semantic search, model pickers, automatic caching, document ingestion, deletion/archive management, and integrations unless actual use makes one essential. A full task manager, accounts, deployment work, and commercial requirements are outside this month's goal.

## Session checkpoint

Update this small record when work is requested. Keep technical detail in the relevant task or evidence note. No daily journal is required.

- **Session state:** October 26, 2026; repair and local workflow patch implemented and verified by owner-run gates.
- **Last completed:** Owner automated gates passed (targeted Python, Mypy typing across 11 files, 17 headless JS), doctor checks, stopped-app backup, managed startup at localhost:8123, one-request live connectivity diagnostic, and authorized read-only browser pass (4 UI fixes verified).
- **Next action:** Personal workflow trial using a question Ryan can assess or a fictional case from the quality pack.
- **Remaining observations:** Broader personal acceptance, live synthesis model quality, real restore rehearsal, and dictation/print remain separate.
- **Latest result or evidence:** Targeted regression passed, Mypy 0 errors, 17/17 headless JS passed, GitNexus indexed (1,321 nodes), read-only browser inspection clean.
- **Recovery:** Private stopped-app snapshot at `.local-backups/advisors-20261026T145305Z-928b9a`; see [Recovery](RECOVERY.md) and [Remediation status](REMEDIATION-STATUS.md).

Suggested stop record: `Day [number] | Done: [last completed action] | Next: [one action] | Waiting: [blocker or none] | Evidence: [reference or not checked]`.

## Month completion checklist

- [x] I can start one recurring task with little repeated background entry.
- [x] I can find the useful next action without reading the whole discussion.
- [x] Saving, reopening, and exporting preserve the answer without a new model call.
- [x] Partial failure leaves completed work intact and offers a scoped next action.
- [x] I can find an older result and see my own saved next step.
- [ ] After a real break, observe whether one saved task needs less reconstruction; the recorded immediate reload does not close this observation.
- [x] Historical results remain readable, and my notes do not rewrite generated advice.
- [x] Documentation distinguishes implemented behavior, tested behavior, personal observations, and remaining work.

There is no target number of discussions, completed features, or consecutive days. Your experience of using and returning to the tool determines what earns its place.
