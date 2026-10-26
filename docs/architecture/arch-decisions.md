# Core Architectural Decisions (ETC)

- **Modular Monolith**: Over-engineering is banned. We keep everything in one repository, strictly separated by `lib/` folder structure.
- **The Arsenal Strategy**: Every piece of logic is built as an independent weapon. It makes the system Easier to Change (ETC) by ensuring components are replaceable.
- **Data-Driven Advisor Catalog**: Advisor personas and panel configurations are defined in declarative JSON (`lib/experts/definitions/`) rather than code, allowing new domains and panels to be added without modifying Python code.
- **Resilient Execution & Scoped Recovery**: Long-running operations like roundtables preserve partial progress in a local SQLite journal and immutable saved history. Failures isolate to the exact failed turn or synthesis, allowing targeted retries without repeating completed work.
- **Candlelight Theme**: Visual standardization across all UI eliminates CSS bloat, configuration drift, and decision fatigue.
- **HTML over the Wire**: HTMX renders authoritative server results; small plain-JS controllers retain explicit browser drafts and input preferences. Server contracts still validate every effect.
- **No Build Steps**: No npm, webpack, or transpiling. Any change to CSS or JS is immediately reflected, maximizing developer velocity and ETC.

- **Complete versus abridged:** archival exports preserve exact generated text; executive briefs remain labeled presentation summaries. Participant agreement is not independent evidence.
- **Working versus saved:** journal checkpoints can evolve during a bounded run; a saved result is immutable, notes are separate, and retries create explicit linked versions.
- **Owner evidence:** current user instructions reserve tests/reindex/browser/live acceptance; prepared source and historical passes are not a new acceptance result.
