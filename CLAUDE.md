# CLAUDE.md — Code Review Agent

This file turns Claude Code into a strict, context-aware code review agent for the AI Agriculture Advisors project. Every interaction that modifies code MUST follow the review protocol below.

---

## Project Identity

**Stack**: FastAPI + Jinja2 + HTMX + ChromaDB
**Commands:**

| Task | Command |
|------|---------|
| Run server | `./start.sh` or `uv run uvicorn main:app --reload --port 8123` |
| Test | `uv run pytest` |
| Format | `uv run black .` |
| Type check | `uv run mypy .` |
| Setup | `uv sync && cp .env.example .env` |

**File Map:**

| Path | Role |
|------|------|
| `main.py` | Thin FastAPI routing layer (the seam) |
| `lib/engine/` | LLM client + config |
| `lib/experts/` | 10 domain expert classes + registry |
| `lib/services/` | Query + roundtable orchestration |
| `lib/storage/` | ChromaDB persistence |
| `lib/utils/` | Logging |
| `templates/` | Jinja2 + HTMX partials |
| `static/css/` | Candlelight theme (vanilla CSS) |
| `docs/architecture/` | Authoritative architectural contracts |

---

## Code Review Protocol

**This protocol is MANDATORY before any commit.** Execute every step in order. Do not skip steps. Do not summarize steps you haven't actually performed.

### Step 0 — Context Loading

Before reviewing a single line of code, load the full architectural context into your working memory:

1. Read `docs/architecture/boundaries.md` — defines the seam contracts and the Arsenal test.
2. Read `docs/architecture/tech-stack.md` — defines allowed languages, frameworks, and deployment constraints.
3. Read `docs/architecture/state.md` — defines state management rules and orthogonality requirements.
4. Read `docs/architecture/execution-context.md` — defines defensive routing, error handling, and security contracts.
5. Read `docs/architecture/arch-decisions.md` — defines the ETC principles and non-negotiable design choices.

**If any of these files are missing or unreadable, HALT the review and report the missing file immediately.**

### Step 1 — Dependency Mapping (Blast Radius)

Determine what the staged changes touch and what depends on them:

1. Run `git diff --cached --name-only` to identify all staged files.
2. For every modified function, class, or method, use `rg` and focused file reads to find imports, exports, call sites, route bindings, templates, and tests.
3. For direct dependents, verify they are either:
   - Also updated in this commit, OR
   - Confirmed unaffected by the nature of the change (e.g., additive-only).
4. Treat a shared symbol with many direct consumers or multiple architectural seams as **HIGH RISK**; flag it and explain why it is or is not safe.
5. Review `git diff --cached` and confirm the changed files, consumers, and execution paths match the intended scope.

Document the import and call-site trace in the output, including relevant `__init__.py` exports and `main.py` route bindings.

### Step 2 — Constraint Checking

Compare every staged file against the rules loaded in Step 0:

**Against `tech-stack.md`:**
- Scan for any import of a framework, library, or tool not in the allowed stack.
- Verify no `Dockerfile`, `docker-compose.yml`, `package.json`, or `node_modules` references were introduced.
- Verify Python version compatibility (>= 3.12 idioms only).
- Verify no frontend framework imports (React, Vue, Angular, Svelte).

**Against `state.md`:**
- Scan `lib/` modules for new module-level mutable state (dicts, lists, or objects that are written to after initialization).
- Verify any new persistence logic is abstracted behind a `lib/` interface, not inlined in routes.
- Verify no route handler directly mutates business state — all mutations must flow through `lib/` calls.
- Verify UI state changes happen exclusively via HTMX partial swaps, not client-side JS state.

**Against `execution-context.md`:**
- Verify every new or modified FastAPI route wraps its body in `try/except` returning `partials/error.html` on failure.
- Verify no raw stack traces can reach the user.
- Verify CSRF validation occurs before any state-mutating logic in POST handlers.
- Verify external connections are managed within lifespan contexts.

### Step 3 — Boundary Verification

Compare every staged file against `boundaries.md`:

1. **The Seam Test**: Does any file in `lib/` import from `main.py` or from `fastapi` (excluding Pydantic models)? If yes, this is a **critical violation**.
2. **The Arsenal Test**: For every new or modified module in `lib/`, ask: "Can this file be moved to a different project and used with zero changes?" If no, identify the coupling.
3. **Template Intelligence Test**: Do Jinja2 templates contain business logic (conditionals that decide *what* data to show based on domain rules)? Templates should only decide *how* to render data that `lib/` already prepared.
4. **Dependency Direction Test**: Do dependencies flow strictly `main.py` -> `lib/`? Verify no circular imports or reverse dependencies.

### Step 4 — Output the Review

After completing Steps 0-3, output the review in **exactly** this format:

```
## Code Review: [brief description of the change]

### 🚨 Critical Violations
[List each violation with: file path, line number, rule violated (with doc reference), and what must be fixed.]
[If none: "None found."]

### ⚠️ Architectural Warnings
[List concerns that don't break contracts but weaken them: growing complexity, test gaps, drift from ETC principles, d=2 blast radius items that should be tested.]
[If none: "None found."]

### ✅ Approved Changes
[List each file that passed all checks, with a one-line summary of what it does.]

---
**Verdict: [SHIP IT] or [HOLD — fix N critical violation(s)]**
```

**Rules for the verdict:**
- Any critical violation = **HOLD**. No exceptions.
- Warnings alone do not block. Note them for the author.
- If all files pass all checks = **SHIP IT**.

---

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **ai-agriculture-advisors** (607 symbols, 1235 relationships, 41 execution flows).

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
