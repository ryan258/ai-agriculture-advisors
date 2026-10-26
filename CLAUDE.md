# AI Advisors agent guide

Follow [AGENTS.md](AGENTS.md) and the current human instruction. This is a local, single-user personal accessibility workbench. Professional quality means dependable low-input work and recovery; it does not imply commercial infrastructure.

## Current architecture and operating path

- FastAPI/Jinja2/HTMX, vanilla JS/CSS, Python 3.12+, ChromaDB saved results, and a stdlib SQLite working journal. No Node application runtime or build, Docker, accounts, OAuth, or extra service process.
- `./advisors` starts the local app; subcommands are start/status/stop/doctor/backup/restore/check. `./start.sh` remains compatible. Setup is `uv sync --locked`; create `.env` from the example only when missing. Never source it as shell code or print private values.
- `main.py` is the HTTP edge. `lib/contracts.py` validates persisted data; engine/execution manages provider boundaries/receipts; services orchestrate runs and exports; storage owns Chroma/SQLite. No `lib` import of FastAPI or main.
- JSON catalog definitions are the source of truth for advisors/panels. Saved profiles are immutable historical context. Execution receipts identify configured/returned models and request digests; current service rules still apply to retries.
- HTMX swaps server-rendered results. Plain JS manages panel choices, local question/task/note drafts, explicit excerpt/starter selection, focus and recovery controls. Browser convenience state is allowed; server validation and authoritative journal Save remain the persistence boundary.
- New results use `query_history_v3` with no embedding model. Legacy `query_history` stays readable without migration. Notes remain separate; the working journal and reusable assets are backed up with the data directory.

## Change and verification discipline

Read the [current register](docs/REMEDIATION-STATUS.md) and relevant [architecture](docs/architecture/boundaries.md). Use read-only GitNexus impact before changing existing symbols; report HIGH/CRITICAL risk. UNKNOWN/empty graphs need native source confirmation, including routes, templates and tests. Keep API, validation, exports and replay consistent.

Ryan explicitly runs tests, full suites, long commands and GitNexus analysis himself. For this accumulated repair, provide `./advisors check` and leave execution pending. Do not quietly run it, a browser, a live provider request, or real-data restore. Formatting/source review is separate from behavior verification. Preserve dated historical acceptance without carrying it across changes.

Do not stage, commit, push, deploy, publish or synchronize other projects without explicit delegation. Before any later delegated commit, refresh the graph as Ryan instructs and inspect graph changes; incomplete/UNKNOWN output is unresolved.

Use the Mechanic report in AGENTS.md for reviews. A verdict must distinguish prepared source, executed checks, live output and personal acceptance. Do not declare SHIP IT because a mocked or historical gate passed.

## Source change checks

Trace affected imports, callers, routes, templates, and focused tests with native repository searches and source reads before editing. Keep unresolved references explicit and follow Ryan's current verification instructions. Staging, commits, pushes, deployment, and publication require his explicit delegation of that action.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **ai-agriculture-advisors** (969 symbols, 2263 relationships, 73 execution flows).

> Index stale? Run `node .gitnexus/run.cjs analyze --index-only` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? Bootstrap with `npx`, `bunx`, or `pnpm dlx` — e.g. `bunx gitnexus@latest analyze` (npm 11 npx crash; #1939).

## Always Do

- **MUST run impact before editing.** Use `impact({target: "symbolName", direction: "upstream"})` or `node .gitnexus/run.cjs impact "symbolName" --direction upstream --repo .`; report callers, processes, and risk. Never substitute grep for graph analysis.
- **MUST analyze graph changes before committing.** Use `detect_changes({scope: "all"})` (MCP) or `node .gitnexus/run.cjs detect-changes --scope all --repo .` (CLI fallback). `partial: true` or `truncated: true` is not a clean check — a zero means unseen, not unaffected; re-run it. For regression review: `detect_changes({scope: "compare", base_ref: "main"})` or `node .gitnexus/run.cjs detect-changes --scope compare --base-ref "main" --repo .`.
- MUST warn on HIGH/CRITICAL `risk` pre-edit; never use `riskSharedAxes` to waive a HIGH/CRITICAL `risk` warning. Compare File/symbol: MCP File omits axes; Graph-RAG expands File.
- **MUST treat `risk: UNKNOWN` as unresolved, not as low.** An empty caller set is not evidence the symbol is unused — it can also mean the callers are not resolvable by the index (plain-object property access, dynamic dispatch, cross-language calls). `impact` pairs `UNKNOWN` with a `riskNote` saying so. Confirm with a text search before treating the symbol as safe to change or delete; do not proceed on the strength of a zero.
- **MUST use `query({search_query: "concept"})` for concepts/flows, `context({name: "symbolName"})` for a named symbol, or `impact` for blast radius, on read-only callers, dependencies, imports, or execution flow.** Graph first; text search only for empty/`UNKNOWN`/literals.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method before MCP/CLI impact analysis.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis, and never read `UNKNOWN` as an all-clear — it means the walk could not answer, which is the one verdict that requires confirming by other means.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit before MCP/CLI graph change analysis.

## Resources

| Resource | Use for |
| --- | --- |
| `gitnexus://repo/ai-agriculture-advisors/context` | Codebase overview, check index freshness |
| `gitnexus://repo/ai-agriculture-advisors/clusters` | All functional areas |
| `gitnexus://repo/ai-agriculture-advisors/processes` | All execution flows |
| `gitnexus://repo/ai-agriculture-advisors/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
| --- | --- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
