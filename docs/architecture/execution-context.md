# Execution and errors

- Validate CSRF on mutating POSTs and validate result/task/source/profile shapes before persistence or dispatch.
- Use actionable HTML with truthful status and preservation targets; Save errors must not replace the answer/header/Save button. Notes errors must retain attempted values. Browser error swaps are explicitly opted in for expected fragments.
- Keep routes local by default and redact submitted content/credential fragments from logs. Supported launchers disable URL access logs. Unexpected operations use a safe local reference and exception class.
- Root-anchor dotenv/static/templates/relative history. `.env` is data, never shell code. Required provider URLs/models/ports and budgets validate before dispatch.
- Create durable working state first; checkpoint in-flight receipts before every provider request and completed turns immediately. Reuse successful answers during deliberate retry.
- Bound calls over the run, output/prompt size, per-attempt duration and manual attempts. Pause stops new scheduling; already dispatched provider work may complete remotely. Transport uncertainty is visible and requires acknowledgement before repeating work.
- A confirmed OpenRouter upstream shared-pool 429 permits one same-model JSON-mode attempt through another eligible provider. Other limits do not trigger that route. Any later fallback is still under the common call/deadline bounds; no automatic retry loop exists. Provider minimum waits remain visible and honored.
- The LLM client rejects blank/null/unsupported/truncated content and malformed current schemas. Supplied source references must resolve to captured IDs; disagreements identify completed turns. Semantic faithfulness still requires human review.
- Close background tasks and HTTP clients in lifespan cleanup. Offload blocking persistence to workers. Export/replay/status/library/calculator operations make no provider calls.

Owner-run automated gates, actual browser/assistive input observations, live quality, and production backup restore are separate evidence. Do not run them silently when Ryan has reserved execution.
