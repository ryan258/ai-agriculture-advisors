# AI Advisors

A local tool for asking a question from several AI perspectives. Choose an advisor panel, get individual answers or a roundtable discussion, and save results for later reference.

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
uv sync
cp .env.example .env
# Set OPENROUTER_API_KEY and OPENROUTER_MODEL in .env.
./start.sh
```

Open [localhost:8123](http://localhost:8123). The checkout directory can keep its existing `ai-agriculture-advisors` name; the application and Python project are named **AI Advisors**.

## Use

For a guided demonstration of all five panels, use the [AI Advisors demo walkthrough](docs/DEMO-WALKTHROUGH.md). Its scenarios show how to surface useful disagreement, decision-relevant unknowns, and a practical next check without treating AI agreement as proof.

1. Choose a panel in the Advisor Panel selector.
2. Select advisors and enter a question, or choose an example.
3. Choose **Submit Query** for separate answers or **Round Table** for a discussion with at least two distinct advisors.
4. Choose **Save Result**, then reopen it from Saved Results or export it as Markdown or an executive brief.

The browser remembers the last panel and its advisor selections separately for each panel. Switching panels keeps the current question and displayed results. If browser storage is unavailable, panel selection still works for the current page.

New results capture the panel name, advisor names, and the complete system prompts used. Expand **Advisor definitions used** to inspect them. Saved history and both export formats use those captured definitions even if the catalog changes later. Older results remain readable and explicitly say that their advisor definitions were not captured.

Advisors are AI personas using the configured model. Agreement between them does not establish independent verification. The moderator is instructed to preserve disagreements and missing evidence. These prompt instructions do not guarantee model behavior.

The three decision-support panels ask each advisor to finish with a compact **Decision Check**:

1. **Recommended next step** — the smallest useful action.
2. **Strongest objection** — the most important reason to question it.
3. **What remains unknown** — the missing evidence or unresolved condition that matters.
4. **What needs your decision** — one choice that belongs to you, or “No decision needed yet.”

Their roundtable moderator requests the same four points as structured data and renders them at the end of the synthesis. A missing or invalid closing object uses the existing plain-text fallback with the same instructions. Saved results retain the points, and exports include captured Decision Checks from structured roundtables or correctly formatted individual/fallback answers. No new advice is generated during export. Agriculture and Software keep their existing response formats.

The roundtable synthesis model can be set separately with `OPENROUTER_SYNTHESIS_MODEL`; advisor responses continue to use `OPENROUTER_MODEL`. This is useful when the synthesis model is temporarily unavailable or needs broader provider routing.

## Resume a partial roundtable

If a provider call fails, completed advisor answers stay visible. **Retry failed advisors & synthesis** requests only failed or unfinished contributions and then refreshes the synthesis. If all advisor answers completed, **Retry synthesis** requests only the synthesis. Recovery is manual except for one bounded synthesis failover described below.

A confirmed OpenRouter upstream shared-pool 429 during structured synthesis triggers one attempt through another provider of the same configured model. That attempt uses JSON mode with the original schema in the instructions because strict schema support can restrict routing to the saturated provider. Account/key limits do not trigger this failover. If it fails, further calls pause and a countdown uses the provider's retry guidance, with a 60-second default when none is supplied. The countdown is a minimum wait, not a guarantee that capacity will recover. Retry uses the original question, round order, and captured advisor prompts rather than the current sidebar selections. Successful contributions remain as written; they are not regenerated to incorporate a newly recovered earlier contribution. Synthesis uses successful contributions only and notes any gaps.

You can save a partial result, reopen it, and retry later. Save again after retry to keep the revised result as a new saved version. Older saved failures are supported. Exports identify incomplete synthesis instead of presenting provider error text as advice.

## Customize advisors and panels

Edit two plain JSON files and restart the application:

- `lib/experts/definitions/advisors.json`: advisor definitions.
- `lib/experts/definitions/panels.json`: panel membership, defaults, descriptions, and example questions.

An advisor needs a stable, globally unique `role`, a `label`, a `system_prompt`, and `limitations`. The optional `response_format` can be `"compact_decision"` to request the shared Decision Check; omitting it keeps the original format:

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

For panel, history, and rendering changes:

```bash
uv run pytest -q tests/test_panels.py tests/test_experts.py tests/test_routes.py tests/test_services.py tests/test_history_store.py tests/test_briefing_service.py
```

Provider calls are mocked in these tests. Browser, assistive technology, and live model behavior need their own checks.

See [API.md](API.md), [happy-path.md](happy-path.md), and `docs/architecture/` for request fields and architectural boundaries.
