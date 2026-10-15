# Core Architectural Decisions (ETC)

- **Modular Monolith**: Over-engineering is banned. We keep everything in one repository, strictly separated by `lib/` folder structure.
- **The Arsenal Strategy**: Every piece of logic is built as an independent weapon. It makes the system Easier to Change (ETC) by ensuring components are replaceable.
- **Data-Driven Advisor Catalog**: Advisor personas and panel configurations are defined in declarative JSON (`lib/experts/definitions/`) rather than code, allowing new domains and panels to be added without modifying Python code.
- **Resilient Execution & Scoped Recovery**: Long-running operations like roundtables preserve partial progress in the DOM and persistent history. Failures isolate to the exact failed turn or synthesis, allowing targeted retries without repeating completed work.
- **Candlelight Theme**: Visual standardization across all UI eliminates CSS bloat, configuration drift, and decision fatigue.
- **HTML over the Wire**: Using HTMX eliminates the entire state synchronization problem between frontend and backend.
- **No Build Steps**: No npm, webpack, or transpiling. Any change to CSS or JS is immediately reflected, maximizing developer velocity and ETC.
