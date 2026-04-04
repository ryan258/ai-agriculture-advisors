# AI Agriculture Advisors

A multi-expert agricultural advisory system powered by LLMs. Ten specialized AI advisors answer questions independently or debate them in roundtable discussions — all through a fast, accessible HTMX interface.

**v2.0.0** — FastAPI + Jinja2 + HTMX + ChromaDB. No React. No Docker. No user accounts. Just bare-metal Python.

## Features

### Ten Domain Experts

| Key | Expert | Covers |
|-----|--------|--------|
| `agriculture` | Agricultural Science Expert | Crop science, soil management, farming practices, genetic modifications |
| `climate` | Climate Change Impact Analyst | Weather patterns, climate adaptation, regional impacts |
| `commodities` | Commodities Trading Specialist | Market dynamics, supply/demand analysis, price forecasting |
| `agritech` | AgriTech Innovation Researcher | AI, IoT, robotics, precision agriculture |
| `supplychain` | Food Supply Chain Analyst | Distribution networks, sustainability, traceability |
| `soil` | Soil Health Specialist | Soil composition, nutrient management, regenerative agriculture |
| `pest` | Pest & Disease Management Expert | IPM, biological control, crop disease identification |
| `irrigation` | Irrigation & Water Management Specialist | Water conservation, irrigation systems, efficiency |
| `organic` | Organic Farming Consultant | Certification standards, non-GMO practices, holistic management |
| `economics` | Agricultural Economics Advisor | Farm budgeting, risk assessment, financial planning |

### What You Can Do

- **Multi-Expert Query** — Select any combination of experts and get independent parallel responses
- **Roundtable Discussion** — Pick 2+ experts for a multi-round collaborative debate with a synthesized consensus (configurable 1-5 rounds)
- **Save & Export** — Persist results to ChromaDB, export Markdown, or open a rendered executive brief for any saved result
- **History** — Browse and reload previously saved results from the sidebar

### What's Under the Hood

- **Defensive routing** — Every route has try/except wrapping; errors degrade to styled partials, never raw tracebacks
- **CSRF protection** — Double-submit cookie tokens validated on every POST
- **Rate limiting** — slowapi guards on `/query` (30/min) and `/roundtable` (10/min)
- **Accessibility** — Skip link, ARIA landmarks, focus-visible outlines, keyboard-navigable history, screen-reader-friendly status regions
- **Candlelight theme** — Dark UI with consistent CSS variables, no build step

## Quick Start

### Prerequisites

- **Python 3.12+**
- **uv** — [install](https://docs.astral.sh/uv/getting-started/installation/)
- **OpenRouter API key** — free at [openrouter.ai/keys](https://openrouter.ai/keys)

### Setup

```bash
git clone https://github.com/yourusername/ai-agriculture-advisors.git
cd ai-agriculture-advisors
uv sync
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY
```

### Run

```bash
./start.sh
```

Or directly:

```bash
uv run uvicorn main:app --reload --port 8123
```

Open [http://localhost:8123](http://localhost:8123).

## Usage

1. Select one or more experts from the sidebar
2. Type your agricultural question (or click a suggestion chip)
3. Choose **Submit Query** for independent answers, or **Round Table** for a multi-round discussion (2+ experts required)
4. **Save** results for persistent storage
5. **Export** any saved result as Markdown or open the executive brief view

## Project Structure

```
ai-agriculture-advisors/
├── main.py                        # FastAPI routes (thin routing layer)
├── lib/
│   ├── engine/                    # LLM client + config
│   │   ├── config.py
│   │   └── llm_client.py
│   ├── experts/                   # 10 domain experts
│   │   ├── base.py                # Abstract Expert class
│   │   ├── registry.py            # Expert lookup
│   │   └── *.py                   # Individual expert modules
│   ├── services/                  # Business logic
│   │   ├── briefing_service.py    # Executive brief rendering from saved results
│   │   ├── query_service.py       # Parallel expert queries
│   │   └── roundtable_service.py  # Multi-round discussions
│   ├── storage/                   # Persistence
│   │   └── history_store.py       # ChromaDB integration
│   └── utils/
│       └── logger.py
├── templates/                     # Jinja2 + HTMX
│   ├── base.html
│   ├── index.html
│   ├── 404.html
│   └── partials/                  # HTMX swap targets
│       ├── error.html
│       ├── responses.html
│       ├── roundtable.html
│       ├── response_card.html
│       ├── save_success.html
│       └── history_list.html
├── static/css/style.css           # Candlelight dark theme
├── tests/                         # pytest suite
│   ├── test_routes.py
│   ├── test_history_store.py
│   ├── test_experts.py
│   ├── test_services.py
│   └── test_llm_client.py
├── docs/architecture/             # Architectural contracts
│   ├── boundaries.md
│   ├── tech-stack.md
│   ├── state.md
│   ├── execution-context.md
│   └── arch-decisions.md
├── start.sh
├── pyproject.toml
└── .env.example
```

### Architecture Rules

All business logic lives in `lib/`. `main.py` is a thin seam that maps HTTP to `lib/` calls and returns HTML. `lib/` never imports `main.py` or FastAPI. Every module in `lib/` passes the Arsenal Test — it can be dropped into a different project and used with zero changes. See `docs/architecture/` for the full contracts.

## Development

```bash
uv run pytest          # Run tests (51 tests)
uv run black .         # Format
uv run mypy .          # Type check
```

### Adding a New Expert

1. Create `lib/experts/your_expert.py`:

```python
from .base import Expert

class YourExpert(Expert):
    @property
    def role(self) -> str:
        return "yourrole"

    @property
    def label(self) -> str:
        return "Your Expert Title"

    @property
    def system_prompt(self) -> str:
        return """You are a [Role]. Your expertise covers..."""
```

2. Register in `lib/experts/registry.py`:

```python
from .your_expert import YourExpert

_your = YourExpert()

expert_registry = {
    # ... existing experts
    "yourrole": _your,
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | *required* |
| `OPENROUTER_API_URL` | OpenRouter endpoint | `https://openrouter.ai/api/v1/chat/completions` |
| `OPENROUTER_MODEL` | LLM model | `mistralai/mistral-7b-instruct:free` |
| `PORT` | Server port | `8123` |
| `CHROMADB_PATH` | Persistence directory | `.chromadb` |
| `ALLOW_MISSING_API_KEY` | Skip API key check (dev/test) | `false` |

### Models

Any model available on [OpenRouter](https://openrouter.ai/models) works. Some options:

- `mistralai/mistral-7b-instruct:free` (default, free)
- `meta-llama/llama-3.1-8b-instruct:free` (free)
- `google/gemini-flash-1.5`
- `anthropic/claude-3-sonnet`
- `openai/gpt-4-turbo`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `OPENROUTER_API_KEY environment variable is required` | Copy `.env.example` to `.env`, add your key, restart |
| `Invalid CSRF token` | Refresh the page to regenerate the cookie |
| API request failures | Verify key at [openrouter.ai/keys](https://openrouter.ai/keys), check credit balance, try a free model |
| Rate limited (429) | `/query` allows 30/min, `/roundtable` allows 10/min — wait and retry |

## Security

- **CSRF** — Double-submit cookie token on every POST
- **Rate limiting** — slowapi on LLM-facing endpoints
- **Markdown sanitization** — DOMPurify on all rendered LLM output
- **Input validation** — Server-side checks on every form submission
- **Error containment** — Exceptions render styled partials, never raw tracebacks

For production use, additionally consider HTTPS, authentication, and secrets management.

## Documentation

- `API.md` — Endpoint reference and CSRF requirements
- `happy-path.md` — Quick-start walkthrough
- `docs/architecture/` — Architectural contracts (boundaries, state, tech stack, execution context, decisions)

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) — Unified LLM API access
- [FastAPI](https://fastapi.tiangolo.com/) — Async Python web framework
- [HTMX](https://htmx.org/) — HTML over the wire
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [marked.js](https://marked.js.org/) — Markdown rendering
- [DOMPurify](https://github.com/cure53/DOMPurify) — Sanitization

---

**Built with care for sustainable agriculture.**
