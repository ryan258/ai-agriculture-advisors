# State Management & Orthogonality

- **No Global Variables**: Pass state explicitly via function arguments or manage via encapsulated singletons inside `lib/` (e.g., `lib/storage/`).
- **UI State**: Exists entirely in the DOM via HTMX. The server holds the absolute truth, the UI merely swaps partials.
- **Persistence Boundaries**: File-based storage or ChromaDB must be fully abstracted behind strict `lib/` interfaces. No direct db calls in routes.
- **Orthogonality**: Mutating business logic MUST NOT directly mutate HTTP responses or UI components. Keep effects localized.
- **Isolation**: Changes in the LLM engine logic or model providers must have zero impact on how state is persisted or rendered.
