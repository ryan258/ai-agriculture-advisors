# One low-input local work loop

The October 25 patch's owner automated continuation passed: the save/import regression, typing across 11 source files, and 17 headless JavaScript checks. On October 26 the owner also reported a passing local doctor, completed stopped-app backup, managed startup at [localhost:8123](http://localhost:8123), and a one-request live provider connectivity diagnostic. The authorized read-only browser pass verified saved-history search/reopen, reload return points, and keyboard navigation, and corrected four small UI issues. Refresh an existing tab to pick up those corrections. Actual write/recovery, synthesis-model and answer quality, dictation/print, and broader personal acceptance remain pending; see [current evidence](docs/REMEDIATION-STATUS.md) and [Recovery](docs/RECOVERY.md).

For a configured checkout, run `./advisors start`, then open its reported loopback address. Existing `.env` and history stay in place. Setup for a new checkout is in [README](README.md); `./advisors doctor` is offline unless `--live` is deliberately selected.

1. Resume a familiar saved result or choose a panel and a small question. Optional context/source fields are visible and user-selected. Select one round to start.
2. Review planned calls and selected models. A Submit/Round Table action sends this input to the provider. Completed contributions checkpoint locally; a browser close does not cancel the run.
3. Pause if needed. Interrupted or uncertain work is visible under Working runs. Resume is manual and retains completed text; an ambiguous prior call needs acknowledgement.
4. Save the finished/partial checkpoint. A failed Save leaves the answer and retry control intact. The same saved checkpoint is idempotent.
5. Record one personal next action/outcome, then Save personal notes. A recovered browser draft is not application-saved until that action succeeds. Find the item by title/status/tag, Resume, or its stable local bookmark.
6. Download Complete record for exact content or an explicitly abridged brief for presentation. Select personal notes only when you want them in a decision report. Review private content before sharing.

Useful low-input controls: reusable question/background selection, capture current question as a starter, source excerpt preview, copy next step, and discoverable Alt+Q/F/S/R shortcuts. No global alias or voice command is installed by this patch.

A useful result identifies supplied support, assumptions, unresolved disagreement, and the next check. AI agreement does not establish independent verification. An actual after-break or dictation observation must be recorded separately from an immediate reload or automated check. See [current register](docs/REMEDIATION-STATUS.md) and [fictional quality pack](docs/QUALITY-PACK.md).
