# AI Advisors

A local tool for asking a question from several AI perspectives. Choose an advisor panel, get individual answers or a roundtable discussion, and save results for later reference.

**2.1.0 release candidate:** compact handoffs, less repeated roundtable advice, and recovery that keeps completed answers. See the [changelog](CHANGELOG.md) and [release readiness and upgrade notes](docs/RELEASE-READINESS.md) for the current evidence and remaining checks.

The October 16 local implementation adds summaries before full discussions, copy controls, recoverable drafts, saved-work search, separate personal notes and outcomes, a Resume entry point, and truthful request feedback. Its focused gate passed **144 Python tests and 12 headless JavaScript tests**, and the full locked test suite (**182 passed in 4.14s** on 2026-10-16). Personal browser, dictation, and return-after-a-break acceptance remain open. Follow the [personal use and restart check](docs/PERSONAL-USE-CHECK.md) for one focused trial; the [month plan](docs/MONTH-PLAN.md) distinguishes implemented work from pending personal observations.

The first live candidate trial verified saving, reopening, and both export contents, but found capability-grounding and save/replay UI issues. Corrections for all three findings are implemented; targeted regressions passed (97 passed) and the full locked suite passed (151 passed) on 2026-10-15, while live model adherence and personal dictation/resumption acceptance remain unverified. Shipping acceptance remains on hold. The original saved trial is preserved unchanged.

Built-in panels:

- **Agriculture:** the original ten advisors covering crops, climate, commodities, agricultural technology, supply chains, soil, pests, irrigation, organic farming, and farm economics.
- **Software:** five advisors covering architecture, implementation, testing, security, and accessibility.
- **AI Workflow & Delegation:** workflow design, bounded assignments, privacy, and recovery.
- **Accessibility & Effort:** voice-first workflows, clear interactions, effort reduction, and resumption.
- **Evidence & Judgment:** claims, source quality, alternative explanations, and uncertainty.

FastAPI + Jinja2 + HTMX + ChromaDB, with plain JavaScript and the Candlelight dark theme. No frontend build step or user accounts.

## Run locally

Requires Python 3.12+, uv, and an OpenRouter API key and model configured in `.env`.

From this checkout:

```bash
uv sync --locked
test -f .env || cp .env.example .env
# Set OPENROUTER_API_KEY and OPENROUTER_MODEL in .env.
./start.sh
```

Open [localhost:8123](http://localhost:8123). The checkout directory can keep its existing `ai-agriculture-advisors` name; the application and Python project are named **AI Advisors**.

For an existing installation, keep your current `.env` and saved-history directory. Follow the [upgrade and recovery steps](docs/RELEASE-READINESS.md#upgrade-and-recovery) before replacing the checkout.

## Use

For a guided demonstration of all five panels, use the [AI Advisors demo walkthrough](docs/DEMO-WALKTHROUGH.md). Its scenarios show how to surface useful disagreement, decision-relevant unknowns, and a practical next check without treating AI agreement as proof.

1. Choose a panel in the Advisor Panel selector.
2. Select advisors and enter a question, or choose an example.
3. Choose **Submit Query** for separate answers or **Round Table** for a discussion with at least two distinct advisors.
4. Choose **Save Result**, then reopen it from Saved Results or export it as Markdown or an executive brief.

The browser remembers the last panel and its advisor selections separately for each panel. Switching panels keeps the current question and displayed results. If browser storage is unavailable, panel selection still works for the current page.

New results capture the panel name, advisor names, and advisor definition prompts before provider calls. Expand **Advisor definitions used** to inspect them. These are profile snapshots, not a record of the complete provider request: roundtable turns remove the standalone closing instruction and add discussion-specific guidance at execution time. Saved history and both export formats use the captured definitions even if the catalog changes later. Older results remain readable and explicitly say that their advisor definitions were not captured.

Advisors are AI personas using the configured model. Agreement between them does not establish independent verification. The moderator is instructed to preserve disagreements and missing evidence. These prompt instructions do not guarantee model behavior.

Standalone answers in the three decision-support panels ask each advisor to finish with a compact **Decision Check**:

1. **Recommended next step** — the smallest useful action.
2. **Strongest objection** — the most important reason to question it.
3. **What remains unknown** — the missing evidence or unresolved condition that matters.
4. **What needs your decision** — one choice that belongs to you, or “No decision needed yet.”

In their roundtables, advisor turns stay concise and omit individual Decision Checks; the moderator requests the same four points as structured data and renders one closing check after the synthesis. A missing or invalid closing object uses the existing plain-text fallback with the same instructions. Saved results retain the points, and exports include captured Decision Checks from structured roundtables or correctly formatted individual/fallback answers. No new advice is generated during export. Agriculture and Software keep their existing response formats.

AI Workflow & Delegation roundtables use a compact handoff synthesis: the task packet itself, a review checklist tied to supplied evidence, a resumable checkpoint, and a measured comparison with manual work. The moderator separates prompt requests from enforceable tool permissions and calls out that hosted models receive submitted input.

Accessibility & Effort roundtables return a reusable voice-friendly starter, a short resume record, a concrete dictation fallback, and one small trial with an observable effort check. In both panels, roundtable contributions stay brief and the moderator leaves at most one Decision Check for the end; standalone advisor answers keep their individual closing check.

The roundtable synthesis model can be set separately with `OPENROUTER_SYNTHESIS_MODEL`; advisor responses continue to use `OPENROUTER_MODEL`. This is useful when the synthesis model is temporarily unavailable or needs broader provider routing.

## Resume a partial roundtable

If a provider call fails, completed advisor answers stay visible. **Retry failed advisors & synthesis** requests only failed or unfinished contributions and then refreshes the synthesis. If all advisor answers completed, **Retry synthesis** requests only the synthesis. Recovery is manual except for one bounded synthesis failover described below.

A confirmed OpenRouter upstream shared-pool 429 during structured synthesis triggers one attempt through another provider of the same configured model. That attempt uses JSON mode with the original schema in the instructions because strict schema support can restrict routing to the saturated provider. Account/key limits do not trigger this failover. If it fails, further calls pause and a countdown uses the provider's retry guidance, with a 60-second default when none is supplied. The countdown is a minimum wait, not a guarantee that capacity will recover. Retry uses the original question, round order, and captured advisor definitions rather than the current sidebar selections; the current application's discussion and synthesis rules still apply. Successful contributions remain as written; they are not regenerated to incorporate a newly recovered earlier contribution. Synthesis uses successful contributions only and notes any gaps. Empty text synthesis remains a failure that can be retried.

You can save a partial result, reopen it, and retry later. Save again after retry to keep the revised result as a new saved version. Older saved failures are supported. Exports identify incomplete synthesis instead of presenting provider error text as advice.

## Find and resume your work

**Saved Results** searches all saved metadata and personal notes, including older results beyond the recent list. Search is case-insensitive; pages show ten matching records at a time. Older records without a captured panel label remain readable and searchable by their question or your own notes.

Open a saved result to add an optional title, your decision status, next step, last completed step, blocker, and outcome. **Save personal notes** persists those fields in a separate Chroma collection. They never rewrite the advisor transcript, captured prompts, or existing exports, and never send a model request. Blank status is unset; only your explicit Undecided or Waiting items appear in the unfinished list.

**Continue saved work** remembers the most recently opened or saved result in this browser. Resume opens it without retrying advisors. Draft edits are explicitly unsaved until you choose Save personal notes. Captured generated checkpoints remain suggestions rather than proof that anything was saved or configured. Browser storage is optional; ordinary saved history remains available without it.

The current question is retained locally when browser storage is available. Clear draft deliberately removes it. Result requests show waiting, completion/failure, and actual elapsed browser-request time; they do not estimate provider progress. New discussions and scoped retries still require an intentional request.

## Customize advisors and panels

Edit two plain JSON files and restart the application:

- `lib/experts/definitions/advisors.json`: advisor definitions.
- `lib/experts/definitions/panels.json`: panel membership, defaults, descriptions, and example questions.

An advisor needs a stable, globally unique `role`, a `label`, a `system_prompt`, and `limitations`. The optional `response_format` accepts `"compact_decision"` for the shared Decision Check or `"workflow_handoff"` for delegation-specific guidance plus the same closing. Omitting it keeps the original format. The built-in panel determines the specialized synthesis layout; a custom panel uses the general moderator even when it includes workflow advisors.

```json
{
  "role": "story_editor",
  "label": "Story Editor",
  "system_prompt": "Help examine structure, character choices, and pacing in the supplied draft.",
  "limitations": "Use only the supplied material. State missing context and do not invent author intent."
}
```

A panel references existing roles, so a custom panel can combine advisors from different subjects:

```json
{
  "id": "creative",
  "label": "Creative",
  "description": "Perspectives on writing and revision.",
  "roles": ["story_editor"],
  "default_roles": ["story_editor"],
  "suggested_queries": [
    {"label": "Review a draft", "query": "Help me find the structural problem in this draft."}
  ]
}
```

Append these objects to their respective JSON arrays. IDs begin with a lowercase letter and contain lowercase letters, digits, underscores, or hyphens. Keep IDs stable to make references understandable. Invalid or duplicate IDs, blank instructions, unknown panel members, and invalid defaults produce clear startup errors. A single-advisor panel supports individual answers; roundtables require at least two distinct advisors.

The original agricultural role keys are preserved. The old prompt-only Python subclasses have been replaced by one configurable implementation; new advisors do not need Python code.

## Project structure

- `main.py`: HTTP routes and HTML responses.
- `lib/experts/`: catalog validation, generic advisor implementation, and lookup.
- `lib/engine/`: provider client and environment configuration.
- `lib/services/`: individual queries, discussions, and brief rendering.
- `lib/storage/`: ChromaDB history, retaining the existing `.chromadb` location and `query_history` collection.
- `templates/` and `static/`: Jinja2, HTMX, plain JavaScript, and CSS.
- `tests/`: focused behavioral checks.

`lib/` does not import FastAPI or `main.py`.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | Provider API key | Required |
| `OPENROUTER_API_URL` | Provider chat-completions endpoint | Set in `.env` |
| `OPENROUTER_MODEL` | Model identifier | Set in `.env` |
| `OPENROUTER_SYNTHESIS_MODEL` | Optional model used only for roundtable synthesis | `OPENROUTER_MODEL` |
| `PORT` | Local server port | `8123` |
| `CHROMADB_PATH` | Saved results directory | `.chromadb` |
| `ALLOW_MISSING_API_KEY` | Allow startup without a key for local checks | `false` |

## Development checks

Use the project environment for checks; a global `python -m pytest` can select a different Python without FastAPI or the async test plugin. `uv sync --locked` includes the development dependencies.

For the trial-correction regression gate (decision panels, routes, experts, and retry behavior):

```bash
uv run --locked pytest -q tests/test_decision_panels.py tests/test_routes.py tests/test_experts.py tests/test_roundtable_retry.py
```

**97 passed in 2.47s** for those four files (`tests/test_decision_panels.py tests/test_routes.py tests/test_experts.py tests/test_roundtable_retry.py`) (and **151 passed in 3.18s** across the full locked suite) on 2026-10-15. Provider calls are mocked in these tests. The [release readiness note](docs/RELEASE-READINESS.md) gives the remaining regression command and a small live acceptance trial; browser, assistive technology, and live model behavior remain separate checks.

See [API.md](API.md), [happy-path.md](happy-path.md), and `docs/architecture/` for request fields and architectural boundaries.
