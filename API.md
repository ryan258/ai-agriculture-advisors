# API Documentation

HTML/HTMX endpoints for AI Agriculture Advisors.

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
| `roles` | string (multi) | Yes | Expert role keys |
| `csrf_token` | string | Yes | CSRF token from cookie |

**Response:** HTML partial (`partials/responses.html`)

---

### 3) Roundtable Discussion

**POST** `/roundtable`

**Form Fields:**

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Discussion topic |
| `roles` | string (multi) | Yes | Expert role keys (min 2) |
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
