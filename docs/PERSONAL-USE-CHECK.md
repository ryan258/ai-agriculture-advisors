# AI Advisors Personal Use and Restart Check

The remaining month of engineering work is implemented locally. This is one focused way to check whether the resulting loop works with Ryan's normal input and reading methods. It does not require thirty consecutive days or a new model discussion.

## Start or return

Run `./start.sh` from this checkout when the app is stopped, then open the local address it reports, normally `http://localhost:8123`. Keep the existing `.env`; do not replace it with the example. The current local app can be used without changing the saved-history directory.

The initial screen offers **Continue saved work** and **Saved Results**. Resume remembers the last opened or newly saved result in this browser. It opens the existing result without asking advisors again. When browser storage is unavailable, use Saved Results instead.

## One focused personal pass

Use an existing saved result. Trial `28a760c4` is one recorded example if it remains available; another familiar saved task is equally suitable. No new provider call is needed for these steps.

1. Open the result. For results with captured Decision Checks or structured handoffs, read **Start here** before opening the full discussion. Confirm that the next action is understandable. Older text remains available even when no compact summary can be extracted.
2. Try **Copy reusable starter**, **Copy task packet**, or **Copy next step** where available. If clipboard access is denied, the text stays visible and is selected. Note whether this works with the normal input method; do not assume a voice command was installed.
3. In **Your personal notes**, optionally give the result a recognizable title, choose a decision status, and dictate one next action. Save personal notes. A generated checkpoint is advice; it becomes your saved stopping point only when you record it here.
4. Use **Find saved work** to search for that title or a remembered phrase. Try Clear search. Open the item again and confirm your note survived.
5. Pause normally. On returning, use Continue saved work. Check whether the saved next action and any blocker are enough to proceed without rereading the chat. A cold-return observation requires a real break; do not manufacture one by immediately reloading.
6. If the task was tried, add one short outcome. Leaving it blank is valid. **Tried** records your status, rather than a claim that the recommendation succeeded.

One short observation is enough: `Usable / Needed correction / Not useful | Friction: [one thing] | On return: [what I still had to reconstruct]`. The agent can record that for Ryan; no separate daily journal is required.

Browser and HTMX behavior, dictation, keyboard use, assistive technology, zoom, and actual effort are personal observations. The local headless tests do not establish those outcomes. Agree on one focused agent-controlled browser pass before starting one.

## Ask another question when needed

The existing panel examples now include **Bound a handoff**, **Shrink repeated input**, and **Test one claim**. These are editable drafting aids; their placeholders are not configured commands. Choose one when the question field is empty. A nonempty question is preserved until it is deliberately cleared.

Question text is retained in local browser storage where available. Reload restores it without submitting it. Clear draft removes that retained text. Submitted questions remain in the field for revision; restoration is not proof that a question was never sent.

The result status reports waiting, completion, failure, and actual elapsed browser-request time. It does not estimate provider progress. A partial roundtable retains completed answers and offers the existing scoped retry; a countdown is a minimum wait. Retry and new discussions send input to the configured hosted provider and require an intentional request with appropriate input.

## Where personal information lives

- Starters remain in `lib/experts/definitions/panels.json`.
- Saved generated content remains in the existing `query_history` collection under configured `CHROMADB_PATH` (default `.chromadb`).
- Your optional annotations live in the separate `personal_annotations` collection in that same directory. Saving notes does not rewrite advisor answers, captured definitions, or exports.
- Draft text, panel preferences, and the last result ID remain browser-local conveniences. They are not a substitute for Save Result and Save personal notes.

## Recover the implementation

A stopped-app private backup was created at `.local-backups/month-20261016-171319` before storage activation. It is Git-ignored and contains the history directory, private configuration, source HEAD archive, and the working diff at snapshot time.

Stop the app before restoring. Preserve a separate copy of the current history and configuration first. Restore source, configuration, and history together from the appropriate snapshot; do not overlay only selected database files. Keep newer saved results and exports if evaluating a downgrade. The backup `.env` contains secrets and stays private. Annotations are additive; no migration or history reset is required to use this implementation.

## Current evidence and verified test suite

On October 16, 2026, the implementation passed 144 targeted Python tests, 12 dependency-free headless JavaScript tests, and the full locked test suite (`uv run --locked pytest -q`, 182 passed in 4.14s). Independent source review closed the integration findings. These checks use isolated fixtures and mocked model boundaries; no new live model discussion or browser acceptance pass was run.

The app was restarted on localhost:8123 and its page, history, Resume, and API schema passed read-only HTTP checks. The GitNexus knowledge graph was reindexed (977 nodes, 2,271 edges, 49 clusters, 73 flows); its scan classified the breadth across shared routes and storage. Personal browser, dictation, and cold-return acceptance remain the next open step.
