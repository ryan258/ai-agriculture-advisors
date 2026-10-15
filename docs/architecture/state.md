# State Management & Orthogonality

- **No Global Variables**: Pass state explicitly via function arguments or manage via encapsulated singletons inside `lib/` (e.g., `lib/storage/`).
- **UI State**: HTMX swaps server-rendered results. Plain JavaScript updates panel controls from server-provided display metadata; localStorage remembers the last panel and selections. The server validates every submitted panel and role selection.
- **Persistence Boundaries**: File-based storage or ChromaDB must be fully abstracted behind strict `lib/` interfaces. No direct db calls in routes.
- **Orthogonality**: Mutating business logic MUST NOT directly mutate HTTP responses or UI components. Keep effects localized.
- **Isolation**: Changes in the LLM engine logic or model providers must have zero impact on how state is persisted or rendered.

- **Advisor Catalog**: Plain JSON definitions in `lib/experts/definitions/` are validated on startup. Panels reference stable advisor IDs. Restart after edits.
- **Historical Context**: New web-generated results capture panel metadata and full advisor prompts before provider calls. Snapshots pass through the existing client-submitted Save flow and are validated for shape and matching roles, not authenticated as provenance. Legacy saves without snapshots remain readable and explicitly unknown.
