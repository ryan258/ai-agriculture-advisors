# Architectural Boundaries (Design by Contract)

- **The Seam**: `main.py` is the edge. It simply maps HTTP requests to `lib/` functions and returns HTML responses.
- **Strict Separation**: `lib/` modules MUST NOT import `main.py` under any circumstance.
- **Portable Logic (The Arsenal Test)**: Code in `lib/` must be drag-and-drop portable to entirely different projects. Do not allow domain logic to bleed into routes.
- **Framework Agnostic**: `lib/` MUST NOT import `fastapi` (except for Pydantic models when required for type validation).
- **Template Logic**: Keep Jinja templates dumb. Prepare all data within `lib/` before passing it to the UI map.
- **Contract Enforcement**: Use strict Python type hints for all cross-module function arguments and return types to explicitly define seams.
- **Historical Context Isolation**: Advisor prompts and panel metadata are captured immutably at execution time. Saved history and briefing exports render using the historical snapshot rather than the live catalog, preventing prompt drift from altering historical records.
- **Execution Instructions**: Advisor snapshots identify the saved profile, not the full provider request. Compact discussion rules and moderator instructions are assembled by the current service. Replaying/exporting a save never regenerates its answers; retry retains successful answers and requests only missing contributions and/or synthesis.
