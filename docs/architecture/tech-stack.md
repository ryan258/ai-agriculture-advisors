# Stack and constraints

- Python 3.12+, FastAPI, Jinja2, HTTPX, python-dotenv, slowapi, uvicorn and ChromaDB as locked in `uv.lock`.
- Stdlib SQLite for working-run/reusable-input state, within the configured history directory; no extra server or runtime package.
- Vendored HTMX/Marked/DOMPurify with licenses and SHA-256 manifest. Plain JavaScript, no application Node runtime/build or frontend framework. Node is development-only for GitNexus and headless standard-library checks.
- Vanilla CSS with shared Candlelight variables. Meaningful small text uses `--text-2`; muted palette values remain available for decorative use. Print uses an explicit ink-friendly stylesheet.
- Local bare-metal loopback execution. No Docker/Kubernetes, microservices, user accounts, OAuth/JWT, billing, hosted infrastructure or speculative scaling requirements.
- Deliberate chosen model APIs are allowed; keep credentials private, context selected and requests bounded. No autonomous browsing or external actions are implemented.

The Python runtime dependencies/lockfile were not changed by the October 25 repair. New vendored browser assets are separate tracked runtime files, not fetched on page load. See their `static/vendor/README.md` and manifest. Version pins are an update responsibility, not a vulnerability-free assertion.
