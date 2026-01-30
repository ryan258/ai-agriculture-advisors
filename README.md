# AI Agriculture Advisors

A Python/FastAPI application that leverages OpenRouter-hosted Large Language Models (LLMs) to provide expert agricultural advice. The system simulates a team of 10 specialized AI-driven agricultural experts, each with domain-specific knowledge and expertise.

## Features

### Expert Team (10 Specialized Advisors)

**Core Experts:**
- **Agricultural Science Expert** - Crop science, soil management, farming practices, genetic modifications
- **Climate Change Impact Analyst** - Weather patterns, climate adaptation, regional impacts
- **Commodities Trading Specialist** - Market dynamics, supply/demand analysis, price forecasting
- **AgriTech Innovation Researcher** - AI, IoT, robotics, precision agriculture technologies
- **Food Supply Chain Analyst** - Distribution networks, sustainability, traceability

**Specialized Experts:**
- **Soil Health Specialist** - Soil composition, nutrient management, regenerative agriculture
- **Pest & Disease Management Expert** - IPM, biological control, crop disease identification
- **Irrigation & Water Management Specialist** - Water conservation, irrigation systems, efficiency
- **Organic Farming Consultant** - Certification standards, non-GMO practices, holistic management
- **Agricultural Economics Advisor** - Farm budgeting, risk assessment, financial planning

### Core Functionality

- **Multi-Expert Consultation** - Query multiple experts simultaneously (parallel execution)
- **Roundtable Discussions** - Collaborative multi-round expert debates for complex topics
- **Persistent History** - Save results to ChromaDB, survives server restarts
- **Markdown Export** - Download any saved result as a .md file
- **HTMX-Powered UI** - Fast, modern interface without JavaScript frameworks
- **Dark Theme** - Candlelight dark theme for comfortable viewing

### Architecture

- **FastAPI** - Modern async Python web framework
- **Jinja2 + HTMX** - Server-rendered templates with dynamic updates
- **ChromaDB** - Vector database for persistent storage
- **httpx** - Async HTTP client for LLM API calls
- **Rate Limiting** - Built-in protection with slowapi

## Prerequisites

- **Python 3.12** or later
- **uv** - Fast Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **OpenRouter API Key** - Get one free at [https://openrouter.ai/keys](https://openrouter.ai/keys)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-agriculture-advisors.git
cd ai-agriculture-advisors
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
PORT=8123
CHROMADB_PATH=.chromadb
ALLOW_MISSING_API_KEY=false
```

### 4. Start the Application

**Using the start script:**
```bash
./start.sh
```

**Or directly with uv:**
```bash
uv run uvicorn main:app --reload --port 8123
```

Navigate to `http://localhost:8123`

## Usage

### Web Interface

1. Select one or more experts from the sidebar
2. Enter your agricultural query
3. Choose between:
   - **Submit Query** - Get parallel responses from each selected expert
   - **Round Table** - Initiate a multi-round discussion (requires 2+ experts)
4. **Save** results for persistent storage
5. **Export** saved results as markdown files

### Expert Role Keys

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

## Documentation

- `happy-path.md` for a quick start walkthrough
- `API.md` for endpoint details and CSRF requirements

## Project Structure

```
ai-agriculture-advisors/
├── main.py                     # FastAPI routes (thin layer)
├── lib/
│   ├── engine/                 # Core LLM client and config
│   │   ├── config.py
│   │   └── llm_client.py
│   ├── experts/                # 10 domain experts
│   │   ├── base.py             # Abstract Expert class
│   │   ├── registry.py         # Expert mapping
│   │   └── *.py                # Individual experts
│   ├── services/               # Business logic
│   │   ├── query_service.py    # Parallel expert queries
│   │   └── roundtable_service.py
│   ├── storage/                # Persistence
│   │   └── history_store.py    # ChromaDB integration
│   └── utils/
│       └── logger.py
├── templates/                  # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   └── partials/               # HTMX partials
├── static/css/                 # Candlelight dark theme
├── tests/                      # pytest tests
├── requirements.txt
├── pyproject.toml              # black/mypy config
├── start.sh
└── .env.example
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
```

### Type Checking

```bash
uv run mypy .
```

### Adding New Experts

1. Create a new expert in `lib/experts/`:

```python
from .base import Expert

class NewExpert(Expert):
    @property
    def role(self) -> str:
        return "newrole"

    @property
    def label(self) -> str:
        return "New Expert Title"

    @property
    def system_prompt(self) -> str:
        return """You are a [Role]. Your expertise covers..."""
```

2. Register in `lib/experts/registry.py`:

```python
from .new_expert import NewExpert

_new = NewExpert()

expert_registry = {
    # ... existing experts
    "newrole": _new,
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | *Required* |
| `OPENROUTER_API_URL` | OpenRouter API endpoint | `https://openrouter.ai/api/v1/chat/completions` |
| `OPENROUTER_MODEL` | LLM model to use | `mistralai/mistral-7b-instruct:free` |
| `PORT` | Server port | `8123` |
| `CHROMADB_PATH` | ChromaDB persistence path | `.chromadb` |
| `ALLOW_MISSING_API_KEY` | Allow startup without API key (tests/dev) | `false` |

### Supported Models

OpenRouter provides access to 100+ models. Popular options:

- `mistralai/mistral-7b-instruct:free` (default, free)
- `meta-llama/llama-3.1-8b-instruct:free` (free)
- `google/gemini-flash-1.5`
- `anthropic/claude-3-sonnet`
- `openai/gpt-4-turbo`

See the full list at [https://openrouter.ai/models](https://openrouter.ai/models)

## Troubleshooting

### OpenRouter API Issues

**Error:** `OPENROUTER_API_KEY environment variable is required`

- Create a `.env` file (copy from `.env.example`)
- Add your API key from https://openrouter.ai/keys
- Restart the server after updating `.env`

**Error:** `Invalid CSRF token`

- Refresh the page to regenerate the CSRF cookie and retry
- Ensure your browser accepts cookies for localhost

**Error:** API request failures

- Verify your API key is valid at https://openrouter.ai/keys
- Check your credit balance at https://openrouter.ai/account
- Try switching to a free model

### Rate Limits

The application implements rate limiting:
- `/query`: 30 requests per minute
- `/roundtable`: 10 requests per minute

## Security

- **Rate Limiting** - Prevents API abuse via slowapi
- **CSRF Protection** - Double-submit cookie token for POST requests
- **Markdown Sanitization** - DOMPurify sanitizes rendered markdown from LLM output
- **Form Validation** - Server-side validation for required inputs

For production deployment, additionally consider:
- HTTPS enforcement
- Authentication/authorization
- Secrets management

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest`
4. Format code: `black .`
5. Check types: `mypy .`
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[OpenRouter](https://openrouter.ai/)** - Unified LLM API access
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[HTMX](https://htmx.org/)** - HTML over the wire
- **[ChromaDB](https://www.trychroma.com/)** - Vector database
- **[marked.js](https://marked.js.org/)** - Markdown rendering

---

**Built with care for sustainable agriculture**
