# API Documentation

HTML/HTMX endpoints for the AI Advisors 2.1.0 candidate. Requests and responses use the existing routes; handoff formats are carried inside the saved roundtable payload.

## Base URL

```
http://localhost:8123
```

## Authentication

No authentication is required.

## CSRF Protection

POST requests require a CSRF token. The app uses a double-submit cookie:

1. `GET /` sets a `csrf_token` cookie.
2. Include `csrf_token` as a form field in each POST.

The browser UI handles this automatically.

## Rate Limiting

- **/query:** 30 requests per minute
- **/roundtable:** 10 requests per minute

## Content Types

- **GET responses:** `text/html`
- **POST requests:** `application/x-www-form-urlencoded`

## Error Responses

Errors return an HTML partial (`partials/error.html`) with a human-readable message.

---

## Endpoints

### 1) Index

**GET** `/`

Returns the main HTML UI.

---

### 2) Multi-Expert Query

**POST** `/query`

**Form Fields:**

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | User question |
| `roles` | string (multi) | Yes | Distinct advisor role keys from the chosen panel |
| `panel_id` | string | No | Panel ID, defaults to `agriculture`; see the panel tables below |
| `csrf_token` | string | Yes | CSRF token from cookie |

**Response:** HTML partial (`partials/responses.html`)

---

### 3) Roundtable Discussion

**POST** `/roundtable`

**Form Fields:**

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Discussion topic |
| `roles` | string (multi) | Yes | Distinct advisor role keys from the chosen panel (min 2) |
| `panel_id` | string | No | Panel ID, defaults to `agriculture`; see the panel tables below |
| `rounds` | int | No | Discussion rounds (default 3) |
| `csrf_token` | string | Yes | CSRF token from cookie |

**Response:** HTML partial (`partials/roundtable.html`)

---

### 4) Save Result

**POST** `/save`

**Form Fields:**

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Original query |
| `result_type` | string | Yes | `query` or `roundtable` |
| `responses` | JSON string | Cond. | Required when `result_type=query` |
| `roundtable_data` | JSON string | Cond. | Required when `result_type=roundtable` |
| `advisor_context` | JSON string | No | Captured panel `{id,label}` and ordered `advisors` definitions `{role,label,system_prompt,limitations}` from the generated result; omitted for legacy results |
| `csrf_token` | string | Yes | CSRF token from cookie |

**Response:** HTML partial (`partials/save_success.html`)

---

### 5) History

**GET** `/history`

Returns a list of recent saved results as an HTML partial.

---

### 6) Result by ID

**GET** `/result/{result_id}`

Returns a saved result as an HTML partial (`responses` or `roundtable`).

---

### 7) Export Result

**GET** `/export/{result_id}`

Returns a Markdown file download.

---

### 8) Export Executive Brief

**GET** `/export/{result_id}/brief`

Returns an HTML executive brief rendered locally by `lib/services/briefing_service.py` and its Jinja2 template. Markdown and HTML exports use saved data and captured prompts; neither invokes a provider.

---

## Expert Roles

| Key | Expert Title |
|-----|-------------|
| `agriculture` | Agricultural Science Expert |
| `climate` | Climate Change Impact Analyst |
| `commodities` | Commodities Trading Specialist |
| `agritech` | AgriTech Innovation Researcher |
| `supplychain` | Food Supply Chain Analyst |
| `soil` | Soil Health Specialist |
| `pest` | Pest & Disease Management Expert |
| `irrigation` | Irrigation & Water Management Specialist |
| `organic` | Organic Farming Consultant |
| `economics` | Agricultural Economics Advisor |

---

## curl Example (Advanced)

The UI is the intended interface. If you want to POST manually:

```bash
curl -c cookies.txt http://localhost:8123/ >/dev/null
CSRF_TOKEN=$(awk '/csrf_token/ {print $7}' cookies.txt)

curl -b cookies.txt -X POST http://localhost:8123/query \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "query=What are the best practices for soil conservation?" \
  --data-urlencode "roles=agriculture" \
  --data-urlencode "csrf_token=$CSRF_TOKEN"
```

## Software advisor roles

Submit `panel_id=software` with any of these roles:

- `software_architecture` — Software Architecture Advisor
- `software_implementation` — Software Implementation Advisor
- `software_testing` — Software Testing Advisor
- `software_security` — Software Security Advisor
- `software_accessibility` — Software Accessibility Advisor

Unknown panels, mismatched roles, and duplicate role selections return HTTP 400 before provider calls. Agriculture retains its original keys. Panel IDs and membership come from `lib/experts/definitions/panels.json`.

Save the `advisor_context` supplied with a generated result, rather than reconstructing it from the current catalog. It is optional for backward compatibility; omitted context stays unknown. Snapshots follow the existing client-submitted result flow and are not cryptographic provenance.

## Decision-support panels

| Panel ID | Label | Roles |
|---|---|---|
| `ai_workflow` | AI Workflow & Delegation | `ai_workflow_workflow_designer`, `ai_workflow_delegation_planner`, `ai_workflow_privacy_reviewer`, `ai_workflow_recovery_reviewer` |
| `accessibility_effort` | Accessibility & Effort | `accessibility_effort_voice_workflow`, `accessibility_effort_interaction_reviewer`, `accessibility_effort_effort_reduction`, `accessibility_effort_fallback_planner` |
| `evidence_judgment` | Evidence & Judgment | `evidence_judgment_claim_examiner`, `evidence_judgment_source_reviewer`, `evidence_judgment_alternative_explanations`, `evidence_judgment_uncertainty_reviewer` |

Use these IDs in the existing `panel_id` form field. Standalone decision-panel answers request a four-bullet Decision Check. In roundtables, their contribution prompts request at most two short bullets, omit individual Decision Checks and user questions, and ask later turns to add only new information. These are model instructions, not a guarantee of output quality or exact word counts.

### Structured synthesis formats

`consensus_brief` is saved with the roundtable result. Its shape depends on the built-in panel:

| Panel | Format and required content |
|---|---|
| `ai_workflow` | `synthesis_format: "workflow_handoff"`; `task_packet`, `review_checklist`, `resume_checkpoint`, `success_measure`, `compact_ending` |
| `accessibility_effort` | `synthesis_format: "accessibility_handoff"`; `starter_template`, `resume_checkpoint`, `dictation_fallback`, `first_trial`, `compact_ending` |
| `evidence_judgment` | General consensus fields plus `compact_ending` |
| `agriculture`, `software` | General consensus fields; no required Decision Check |

The general fields are `governing_insight`, `executive_summary`, `key_findings`, `decision_implications`, `recommendations`, and `limitations`. The `synthesis_format` discriminator is added locally after a valid handoff response; it is not an extra provider-supplied field.

Workflow `review_checklist` contains 2–4 objects with nonempty `check` and `evidence_target` strings (maximum 180 characters each). Handoff text fields are bounded: the packet or starter has a 900-character maximum, and each checkpoint, success measure, fallback, or first-trial field has a 500-character maximum. `compact_ending` contains nonempty strings `recommended_next_step`, `strongest_objection`, `unknowns`, and `user_decision`; the requested schema caps each at 180 characters. Accessibility synthesis requests at most one essential user choice, only if it blocks the first trial; otherwise it requests “No decision needed yet.”

Invalid or empty structured synthesis, and provider rejection of structured output with HTTP 400/422, can use one plain-text synthesis fallback with the panel's instructions. A plain-text fallback has no structured `consensus_brief`; its `final_answer` is retained. Rate limits, connection errors, and other provider failures do not trigger that text fallback. Structured and correctly formatted plain-text Decision Checks are captured in exports. Legacy payloads remain supported; export does not rewrite older wording or invent absent closing points.

Accessibility advisor and moderator instructions use only the original user's explicit confirmation as evidence of configured, working capabilities. Requested features and advisor proposals do not establish a voice command, alias, macro, automatic save, or restoration mechanism. When setup is unknown, guidance requests plain reusable text and safe-pause steps, without assuming that generating a checkpoint saves it. This applies to structured and plain-text synthesis and to captured discussion retries; it is prompt guidance, not a factual validator or proof of model adherence.

The catalog accepts `response_format=compact_decision` or `workflow_handoff`. The latter adds delegation-specific guidance to an advisor; it does not assign a custom panel the built-in AI Workflow synthesis layout. Direct service callers without panel context can infer a handoff from a homogeneous set of workflow or accessibility roles. Web callers supply captured panel context explicitly.

## Retry a partial roundtable

**POST** `/roundtable/retry` accepts `state` (the JSON hidden field supplied with a roundtable result) and `csrf_token`. It retains the original question, advisor order, round count, captured prompts, completed contributions, and synthesis status. Only failed or unfinished contributions are requested again; synthesis is refreshed after those attempts. A synthesis-only failure retries synthesis without calling any advisor. A fully completed state is a no-op.

Set `OPENROUTER_SYNTHESIS_MODEL` to route roundtable synthesis through a separate model; advisor requests continue to use `OPENROUTER_MODEL`. The selected synthesis model is stored with the result. A confirmed OpenRouter `upstream_provider_shared_pool` HTTP 429 during structured synthesis permits one same-model JSON-mode failover, excluding the reported saturated provider and including the original schema in the system instructions. Other 429s do not trigger failover. If this attempt also fails, further calls pause, including the text-synthesis fallback. `Retry-After` seconds or an HTTP date sets `retry_at` (Unix seconds); without a usable header the pause is 60 seconds. The UI counts down and the retry service also checks the deadline. There are no other automatic provider retries; the default countdown is a minimum pause, not a provider recovery estimate. Non-rate-limit contribution failures can still yield an explicitly partial synthesis from successful contributions only.

Transcript entries now include `role` and `status` (`success`, `failed`, or `pending`), with structured `failure` details on failed entries. Top-level `synthesis_error`, `synthesis_stale`, `retry_at`, `compact_ending`, and the synthesis model used are preserved on Save. Legacy transcript errors are upgraded when reopening or retrying an older result. Captured advisor prompts are reused when available; older results without them use the current advisor definitions.

The captured prompt is the advisor profile, not the complete provider request. Current roundtable instructions and moderator rules are applied on retry; a saved snapshot does not prove the exact historical request envelope. Empty plain-text synthesis is an error and leaves the discussion retryable without regenerating successful contributions.

A retried result is shown as unsaved, so **Save Result** creates a new saved version and leaves the earlier saved record intact. The retry request uses its captured state, regardless of changes to the sidebar question or panel. Validation and CSRF errors target the retry status area so the visible answers remain intact. The endpoint has the same 10/minute app limit as the initial roundtable endpoint.


## Personal saved work

These routes return HTML fragments for the local app and never call advisors.

| Route | Behavior |
| --- | --- |
| `GET /history?q=phrase&offset=0` | Case-insensitive search across all saved metadata and personal notes, followed by stable pagination. Ten matching rows are shown. Empty search lists recent work. |
| `GET /resume?result_id=ID` | Opens the saved return-point summary and up to three explicitly waiting/undecided items. A missing result returns a marker so the browser can forget that return ID. |
| `POST /result/ID/notes` | Saves optional user annotations separately from generated content. |

The notes form submits `title`, `status`, `next_step`, `last_step`, `blocker`, `outcome`, and the existing `csrf_token`. Blank fields are valid; omitted form fields default to blank. Status accepts blank, `undecided`, `decided`, `waiting`, or `tried`. Limits are title 200 characters, next/last/blocker 2000 each, and outcome 4000.

Success returns the updated personal-notes fragment with `HX-Trigger: resultSaved`. Invalid fields return 400, a changed/missing CSRF token returns 403, a missing saved result returns 404, and storage failure returns 503. Each error fragment retains the submitted text; the browser opts in to swapping only these note fragments. The session token is renewed for a deliberate retry when needed. No error changes saved advisor content.

Generated content stays in `query_history`; annotations use the additive `personal_annotations` collection with no embedding function or documents. Existing Markdown and HTML exports continue to represent the saved generated result, without mixing in later personal notes.
