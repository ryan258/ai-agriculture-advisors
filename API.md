# API Documentation

HTML/HTMX endpoints for AI Advisors.

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
| `panel_id` | string | No | Panel ID, defaults to `agriculture`; use `software` for Software advisors |
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
| `panel_id` | string | No | Panel ID, defaults to `agriculture`; use `software` for Software advisors |
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

Returns a rendered HTML executive brief built from the saved result using the
`executive-reporting` component package.

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

Use these IDs in the existing `panel_id` form field. Individual advisors request a four-bullet Decision Check. Roundtables selecting an advisor with `response_format=compact_decision` request an additional `compact_ending` object in `consensus_brief`, with nonempty string fields `recommended_next_step`, `strongest_objection`, `unknowns`, and `user_decision`. It is saved with the existing roundtable payload and rendered in replay and exports. Legacy payloads remain supported.

## Retry a partial roundtable

**POST** `/roundtable/retry` accepts `state` (the JSON hidden field supplied with a roundtable result) and `csrf_token`. It retains the original question, advisor order, round count, captured prompts, completed contributions, and synthesis status. Only failed or unfinished contributions are requested again; synthesis is refreshed after those attempts. A synthesis-only failure retries synthesis without calling any advisor. A fully completed state is a no-op.

Set `OPENROUTER_SYNTHESIS_MODEL` to route roundtable synthesis through a separate model; advisor requests continue to use `OPENROUTER_MODEL`. The selected synthesis model is stored with the result. A confirmed OpenRouter `upstream_provider_shared_pool` HTTP 429 during structured synthesis permits one same-model JSON-mode failover, excluding the reported saturated provider and including the original schema in the system instructions. Other 429s do not trigger failover. If this attempt also fails, further calls pause, including the text-synthesis fallback. `Retry-After` seconds or an HTTP date sets `retry_at` (Unix seconds); without a usable header the pause is 60 seconds. The UI counts down and the retry service also checks the deadline. There are no other automatic provider retries; the default countdown is a minimum pause, not a provider recovery estimate. Non-rate-limit contribution failures can still yield an explicitly partial synthesis from successful contributions only.

Transcript entries now include `role` and `status` (`success`, `failed`, or `pending`), with structured `failure` details on failed entries. Top-level `synthesis_error`, `synthesis_stale`, `retry_at`, `compact_ending`, and the synthesis model used are preserved on Save. Legacy transcript errors are upgraded when reopening or retrying an older result. Captured advisor prompts are reused when available; older results without them use the current advisor definitions.

A retried result is shown as unsaved, so **Save Result** creates a new saved version and leaves the earlier saved record intact. The retry request uses its captured state, regardless of changes to the sidebar question or panel. Validation and CSRF errors target the retry status area so the visible answers remain intact. The endpoint has the same 10/minute app limit as the initial roundtable endpoint.
