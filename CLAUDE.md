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
2. For every modified function, class, or method in the diff, run:
   ```
   gitnexus_impact({target: "<symbolName>", direction: "upstream"})
   ```
3. If any symbol returns **d=1 (WILL BREAK)** dependents, verify those dependents are either:
   - Also updated in this commit, OR
   - Confirmed unaffected by the nature of the change (e.g., additive-only).
4. If any symbol returns **HIGH** or **CRITICAL** risk, flag it in the output and explain why it is or isn't safe.
5. Run `gitnexus_detect_changes({scope: "staged"})` to confirm the change scope matches your expectations.

**If GitNexus is unavailable:** Fall back to manual analysis. Grep for all imports and call sites of every modified symbol. Trace upstream consumers by reading `__init__.py` exports and `main.py` route bindings. Document your manual trace in the output.

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

## GitNexus Integration

This project is indexed by GitNexus as **ai-agriculture-advisors**. The review protocol above uses GitNexus for dependency mapping. Here is the full tool reference:

### Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `impact` | Blast radius of a symbol | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Scope check for staged/all changes | `gitnexus_detect_changes({scope: "staged"})` |
| `context` | Full caller/callee graph for a symbol | `gitnexus_context({name: "symbolName"})` |
| `query` | Find execution flows by concept | `gitnexus_query({query: "concept"})` |
| `rename` | Safe multi-file rename (dry_run first) | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

### Risk Levels

| Depth | Meaning | Review Action |
|-------|---------|---------------|
| d=1 | WILL BREAK — direct callers/importers | Must verify updated or unaffected |
| d=2 | LIKELY AFFECTED — indirect deps | Flag as warning, recommend testing |
| d=3 | MAY NEED TESTING — transitive | Note if on critical path |

### Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/ai-agriculture-advisors/context` | Index freshness check |
| `gitnexus://repo/ai-agriculture-advisors/processes` | All execution flows |
| `gitnexus://repo/ai-agriculture-advisors/process/{name}` | Step-by-step trace |

### Index Maintenance

After commits, the index goes stale. Re-analyze:

```bash
npx gitnexus analyze              # standard
npx gitnexus analyze --embeddings # if embeddings existed (check .gitnexus/meta.json)
```

> A PostToolUse hook handles this automatically after `git commit` and `git merge`.

### Skill Files

| Task | Skill |
|------|-------|
| Architecture exploration | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Impact analysis | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Debugging | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Refactoring | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tool/schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
