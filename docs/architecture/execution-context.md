# Execution Context & Pragmatic Paranoia

- **Defensive Routing**: Every FastAPI route MUST wrap core logic in `try/except` blocks to prevent unhandled 500 exceptions from reaching the user.
- **Graceful Degradation**: On failure, routes must return a polite, pre-rendered HTML partial (e.g., `partials/error.html`), never raw stack traces.
- **Rate Limiting**: Applied strictly at the edge via `slowapi` to protect LLM endpoints and external APIs from abuse or infinite loops.
- **Lifespan Management**: External connections (like LLM clients) must be managed defensively within application lifespan contexts to prevent leaks.
- **CSRF Protection**: Tokens must be dynamically generated and validated on every state-mutating POST request before executing any core logic.
- **Provider Resilience & Failover**: When structured synthesis triggers an upstream provider-pool 429 exhaustion on OpenRouter, a bounded single failover to same-model JSON mode is allowed. Other limits honor `Retry-After` countdowns with preserved state and no blind loops.
