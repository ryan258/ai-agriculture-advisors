# Architectural Boundaries (Design by Contract)

- **The Seam**: `main.py` is the edge. It simply maps HTTP requests to `lib/` functions and returns HTML responses.
- **Strict Separation**: `lib/` modules MUST NOT import `main.py` under any circumstance.
- **Portable Logic (The Arsenal Test)**: Code in `lib/` must be drag-and-drop portable to entirely different projects. Do not allow domain logic to bleed into routes.
- **Framework Agnostic**: `lib/` MUST NOT import `fastapi` (except for Pydantic models when required for type validation).
- **Template Logic**: Keep Jinja templates dumb. Prepare all data within `lib/` before passing it to the UI map.
- **Contract Enforcement**: Use strict Python type hints for all cross-module function arguments and return types to explicitly define seams.
