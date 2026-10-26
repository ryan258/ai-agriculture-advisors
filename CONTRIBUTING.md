# Contributing to AI Advisors

This is Ryan's local personal accessibility tool. Preserve reliable saves, interruption recovery, minimal input, existing short entrypoints, and the Candlelight theme. Professional output does not imply hosted accounts, billing, roles, or a frontend rebuild.

Read [AGENTS.md](AGENTS.md), [current remediation status](docs/REMEDIATION-STATUS.md), and [architectural boundaries](docs/architecture/boundaries.md) before changes. Follow the current human instruction over generated guidance. Staging, commits, pushes, deployment, publication, and cross-project sync each require explicit delegation.

## Environment

```bash
uv sync --locked
test -f .env || cp .env.example .env
./advisors doctor
```

Keep existing configuration and history. Never source `.env` from shell, print key fragments, or use private saved work as a fixture. Use fictional inputs, temporary stores, and mocked provider responses.

## Change boundaries

- `main.py` owns HTTP/form handling and HTML responses; portable behavior lives in `lib/` without FastAPI or `main` imports.
- Versioned persisted-input validation lives in `lib/contracts.py`; structured synthesis contracts and legacy presentation parsing have separate modules.
- Query/roundtable/run services orchestrate bounded work. Checkpoints and receipts preserve completed contributions. A retry is deliberate and retains successful results.
- New saved results use the no-embedding Chroma collection; legacy history stays read-only. Personal notes remain separate. The SQLite journal, organization, and reusable assets live inside the configured data directory.
- Advisor/panel JSON edits must retain stable role IDs and explicit capability limits. Test snapshot compatibility. Do not add advisors merely to increase the count.
- Use existing plain JS and vendored browser libraries. There is no npm application build. Node/GitNexus can be used as development tools within Ryan's verification instructions.

Before changing an existing symbol, use GitNexus impact and read its actual imports, callers, templates, routes, and focused tests. HIGH/CRITICAL risk must be reported. UNKNOWN/empty graph results require source confirmation; they are not an unused-code verdict. Do not run `analyze` for Ryan when he has asked to run it himself. A fresh index becomes stale as source changes accumulate.

## Verification

For the October 25 accumulated patch, provide Ryan the following command and let him return results:

```bash
./advisors check
```

It runs the full Python regression suite because this patch spans execution, storage, routes, templates, exports, and operations; then focused mypy checks and headless JS controls/draft checks. It isolates storage and provider settings. It does not execute a browser, live model trial, real-data restore, Git operation, or GitNexus analysis. Passing it establishes only its stated automated scope.

After an owner run isolates a Python failure, `./advisors check --target PATH_OR_PYTEST_NODE` limits the Python gate to that file or test and still runs the typing and JavaScript gates. Keep the previous full-suite result and the targeted continuation as separate evidence.

For later bounded changes, propose only the relevant owner-run selection. Example:

```bash
uv run --locked pytest -q tests/test_harmony.py tests/test_harmony_routes.py
node --test tests/test_workspace_controls.cjs tests/test_note_drafts.cjs tests/test_retry_countdown.cjs
```

Use Black for Python formatting. Add behavior regressions for consequential fixes; avoid tests that merely duplicate implementation. Keep owner-returned output dated and tied to the exact revision. Ask before browser verification and keep any authorized pass focused near completion. Live cases are separately deliberate and budgeted; see [quality pack](docs/QUALITY-PACK.md).
