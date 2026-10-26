# AI Advisors

A local, single-user workbench for examining a question from several AI perspectives, preserving the evidence and decision, and returning with little repeated input. Professional quality here means reliable personal work: deliberate provider calls, recoverable progress, complete records, and accessible controls.

**Current state — October 26, 2026:** the 2.1.0 candidate includes a broad repair and workflow patch. **Owner verification passed:** the targeted save/import regression, typing across 11 source files, all 17 headless JavaScript checks, configuration/dependency diagnostics, stopped-app backup, managed startup at localhost:8123, and a one-request live provider connectivity diagnostic. An authorized read-only browser pass also verified page loading, saved-history search/reopen, reload return points, keyboard navigation, and clean console output after four small UI corrections. Actual write/recovery, synthesis-model and answer quality, dictation/print, and broader personal acceptance remain pending. The authoritative correction/enhancement and verification register is [Remediation status](docs/REMEDIATION-STATUS.md). The [original review](docs/PROJECT-REVIEW-2026-10-25.md) is a dated baseline; its earlier passing checks do not validate this patch.

## Start or resume locally

Requires Python 3.12+ and uv. Provider use requires your chosen chat-completions endpoint, API key, and available model ID. Keep an existing `.env` and history directory.

```bash
uv sync --locked
test -f .env || cp .env.example .env
# Configure the provider fields in .env, keeping your existing private values.
./advisors doctor
./advisors start
```

Open the local address it reports, normally [localhost:8123](http://localhost:8123). `./advisors` defaults to start; `./start.sh` remains a compatibility launcher. The scripts anchor configuration, static files, and relative storage paths to this checkout, including when invoked by an absolute path from another directory. They load `.env` as data, never as shell code. They do not install a global alias or voice command.

```bash
./advisors status
./advisors stop
./advisors start --offline
```

Offline mode permits saved-work use without provider credentials. Sending a question still requires a functioning configured provider. Supported entrypoints bind to `127.0.0.1`; there are no user accounts. Keep the app local.

**Existing installation:** stop its current server and make a private backup before first activation of changed persistence code. If the old server was launched directly in a terminal, stop it with Ctrl-C. The managed stop command signals only its own verified process.

```bash
./advisors backup
# Restore rehearsal uses a NEW directory; it never overlays current history:
./advisors restore /absolute/path/to/snapshot --destination /absolute/path/to/new-rehearsal
```

Backups contain saved answers, personal notes, the run journal, reusable assets, source files, and a private configuration copy when present. They may contain credentials; do not share them. Browser-local drafts are excluded. See [recovery](docs/RECOVERY.md).

## A useful work loop

1. Choose a built-in panel and advisors. Enter one question or select a reusable starter. Optional task fields capture goal, decision, constraints, location/date, deliverable, and background.
2. Add only the source passages you want sent. Each gets a stable local ID such as `S1`. A URL is a reference, not opened evidence. Local `.txt`/`.md` previews require explicit excerpt selection.
3. Review the displayed models, planned calls, and limits. Submit individual answers or a roundtable. One round is the UI default. These actions send the selected input to your provider.
4. Completed contributions checkpoint to a local working-run journal. Pause prevents new calls after currently dispatched work. Closing the page does not cancel a background run. After application interruption, recovery is manual; ambiguous calls require acknowledgement because remote work may have completed.
5. Save the checkpoint when ready. Save retries are idempotent for the same run state. Reopen, bookmark, tag, pin, archive reversibly, or record a personal next step and outcome. Notes are separate from generated answers and are excluded from ordinary exports.
6. A linked follow-up previews optional carried context, a bounded prior-result excerpt, and the recorded outcome. Retrying missing answers retains successful text and creates a new saved version linked to the parent.

The five panels are Agriculture, Software, AI Workflow & Delegation, Accessibility & Effort, and Evidence & Judgment. Their validated JSON catalog is the source of truth for advisor counts, roles, and examples. The [demo](docs/DEMO-WALKTHROUGH.md) gives domain examples.

AI agreement is generated analysis, not independent verification. General roundtable synthesis can show source-linked claims, options, and unresolved disagreements tied to completed turns. Unknown references are rejected; semantic accuracy still needs review. Agriculture roles explicitly work from supplied information and identify missing location, date, units, and observations. This app has no autonomous browsing, market/weather feed, field measurements, or action tools.

## Find, reuse, and export

Saved Results searches metadata and personal notes across old and new records; answer-body search is not implemented. Filters cover captured panel label, your status, tag, date range, and archived items. Pinned matches sort first. **Continue saved work** and `/work/RESULT_ID` reopen saved work without provider calls.

**Reusable starters, context, and local tools** includes user-selected background snippets, question starters, two saved-result comparisons, a measured-minutes calculator, archive import preview, and six fictional quality cases. Preparing a case makes no model call. No calculator infers advice quality or a medical benefit.

- **Complete Markdown record:** exact question, all answer/transcript text, qualifications, code, URLs, sources, profile snapshots, and execution metadata.
- **Complete JSON archive:** versioned portable records. Notes are excluded unless deliberately selected through the notes-inclusive URL/API. Import is previewed and additive; identical existing records retain their local notes, and conflicting IDs receive a new ID.
- **Abridged Markdown / HTML executive brief:** presentation summaries, labeled abridged. Use the complete record for archival fidelity.
- **Decision report:** complete generated record plus personal decision/outcome only when its inclusion checkbox is selected.

Execution receipts distinguish configured model IDs from returned provider/model/usage fields. They include request fingerprints, rule version, timestamps, finish reasons, and transport status. They do not contain API keys or a verbatim HTTP envelope. Missing usage/cost remains unknown.

## Accessible controls

The Candlelight palette remains centralized in `static/css/theme.css`. Meaningful small text uses the lighter secondary text color. Markdown tables retain semantic table elements. Live announcements report milestones; elapsed seconds are visual only. All main actions have visible controls; shortcuts are Alt+Q (question), Alt+F (search), Alt+S (save visible notes/result), and Alt+R (resume). Browser/OS shortcuts may take priority.

Questions, selected task context, and per-result note drafts can be retained in this browser. Notes become durable application records when **Save personal notes** succeeds. Navigation restores unsaved note drafts; when browser storage is unavailable, opening another result is blocked until the unsafe draft is saved or explicitly discarded. Storage is convenience recovery, not a backup or encrypted vault. Clear controls remove local drafts deliberately. A focused keyboard/dictation/print observation for this patch remains pending.

## Configuration and limits

See [.env.example](.env.example). URL/model/port validation occurs before dispatch. Remote endpoints require HTTPS; loopback HTTP supports a deliberately configured local provider.

| Variable | Default / purpose |
| --- | --- |
| `OPENROUTER_API_KEY`, `OPENROUTER_API_URL`, `OPENROUTER_MODEL` | Chosen provider credentials, endpoint and model; `.env.example` contains placeholders |
| `OPENROUTER_SYNTHESIS_MODEL` | Optional synthesis model; otherwise advisor model |
| `PORT` | `8123` |
| `CHROMADB_PATH` | `.chromadb`, resolved from project root |
| `MAX_OUTPUT_TOKENS` | `1800` per dispatch |
| `MAX_RUN_CALLS` | `32`, including fallback and resumed dispatches |
| `MAX_RUN_SECONDS` | `600` per attempt |
| `MAX_PROMPT_CHARS` | `120000` across messages per dispatch |
| `MAX_RUN_ATTEMPTS` | `3`, with manual resume only |
| `ALLOW_MISSING_API_KEY` | `false`; offline startup override |

No price or spending guarantee is inferred from token/call limits. A transport interruption can leave remote work uncertain. No automatic repeated polling request dispatches model work.

## Verification and contribution

Ryan runs the checks for this accumulated patch. This command uses temporary storage and fictional provider settings, then runs Python regression checks, focused typing, and standard-library headless JavaScript checks. It makes no deliberate live-provider call and does not reindex GitNexus:

```bash
./advisors check
```

It stops at the first failed gate. Return the failure output for repair. Node is development tooling for headless JS checks only; the application has no Node runtime/build dependency. [CONTRIBUTING.md](CONTRIBUTING.md) describes narrower owner-run checks.

To rerun one corrected Python test and continue through the typing and JavaScript gates, use `./advisors check --target tests/test_harmony.py::test_source_ids_and_disagreements_resolve_only_to_captured_evidence`. The optional target can be a pytest file or node; omitting it runs the full Python suite.

The implementation uses FastAPI, Jinja2, vendored HTMX/Marked/DOMPurify, vanilla JS/CSS, ChromaDB for saved results, and stdlib SQLite for working state. No new Python runtime dependency was added. New history writes use `query_history_v3` with inert explicit embeddings; `query_history` remains readable without migration. See [architecture](docs/architecture/boundaries.md), [API](API.md), [recovery](docs/RECOVERY.md), and [current remediation status](docs/REMEDIATION-STATUS.md).
