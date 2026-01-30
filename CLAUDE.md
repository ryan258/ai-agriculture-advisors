# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## MISSION BRIEFING: AI Agriculture Advisors

A Python framework for multi-expert agricultural advisory using LLMs.
**Stack**: FastAPI + Jinja2 + HTMX + ChromaDB. **NO React. NO Docker. NO Redis. NO User Accounts.**

---

## Commands

**Run Server**: `./start.sh` or `uv run uvicorn main:app --reload --port 8123`

- Test: `uv run pytest`
- Format: `uv run black .`
- Type Check: `uv run mypy .`

**Setup:**

1. `uv sync`
2. Copy `.env.example` to `.env`

---

## Architecture: The Anti-Gravity Standard

### Core Components

- **Arsenal (`lib/`)**: Pure Python modules. Independent. Copy-paste ready.
  - `engine/`: **The Core**. LLM client, config management.
  - `experts/`: **Domain Experts**. 10 specialized agricultural advisors.
  - `services/`: **Orchestration**. Query and roundtable services.
  - `storage/`: **Persistence**. ChromaDB history store.
  - `utils/`: **Shared**. Logging utilities.
- **Frontend (`templates/`)**: Jinja2 pages with HTMX for interactivity.
- **Entry (`main.py`)**: Thin routing layer.

### Data Flow

1. **Input**: User submits form (HTMX POST).
2. **Process**: Backend `lib/` modules execute logic.
3. **Update**: Server returns HTML partials (HTMX swap).

---

## Critical Patterns (Mission Control Intel)

### Pattern 1: The "Arsenal" Test

- BEFORE writing code, ask: "Can I move `lib/my_module.py` to another project and use it instantly?"
- If NO -> Refactor. Dependencies usually flow `main.py` -> `lib/`. NEVER `lib/` -> `main.py`.

### Pattern 2: Candlelight UI

- Use `static/css/style.css` (CSS Variables).
- **Bg**: `#121212`, **Bg-2**: `#1A1A1A`, **Bg-3**: `#242424`.
- **Text**: `#EBD2BE`, **Text-2**: `#A6ACCD`, **Text-Muted**: `#6B7280`.
- **Accent**: `#A6ACCD`, **Success**: `#98C379`, **Error**: `#E06C75`, **Warning**: `#F59E0B`.
- NO CSS frameworks (Tailwind allowed ONLY via CDN if absolutely necessary, prefer vanilla).

### Pattern 3: No-Bloat

- **Forbidden**: `npm`, `node_modules`, `Dockerfile`, `docker-compose.yml`.
- **Reason**: We run on bare metal. We own the stack.

---

## Code Review Protocol

**FINAL VERDICT:** [SHIP IT] or [HOLD]

- **Bloat Check**: Any React/Vue? Any Docker? -> **HOLD**.
- **Arsenal Check**: Logic in `routes` instead of `lib`? -> **HOLD**.
- **Visuals**: Not Candlelight? -> **HOLD**.

---

## File Map

**Backend:**

- `lib/` - The Core (Arsenal).
  - `engine/` - LLM client, config.
  - `experts/` - Domain expert classes.
  - `services/` - Query and roundtable orchestration.
  - `storage/` - ChromaDB persistence.
  - `utils/` - Logging.
- `main.py` - FastAPI routes.
- `templates/` - Jinja2/HTMX.
- `static/` - CSS (minimal).
