# Local recovery and private backups

October 25 repair patch, updated October 26: the owner automated continuation, local diagnostic, stopped-app backup, and managed startup passed; see the exact scope and prior results in [Remediation status](REMEDIATION-STATUS.md). The owner snapshot is `.local-backups/advisors-20261026T145305Z-928b9a`. Real-data restore rehearsal remains pending; backup completion alone does not verify a successful restore.

## Before activating changed persistence code

1. Stop the existing server. `./advisors stop` controls only a process started by this launcher's recorded PID and nonce. A prior direct uvicorn process must be stopped in its terminal with Ctrl-C.
2. Run `./advisors backup` while stopped. If shutdown is still in progress, the helper refuses to copy the live data directory. It does not force-kill a process.
3. Keep the printed snapshot path private. Each snapshot has `history/`, `source.tar`, optional `private.env`, and a SHA-256 inventory with application/schema/Python metadata. Credentials may be present. Browser drafts and external dependencies are excluded.

Default snapshots live under ignored `.local-backups/`; the destination is created with private directory permissions. A custom destination must be new and outside history. Symlinked history is refused for manual inspection.

## Rehearse into a fresh location

```bash
./advisors restore /absolute/path/to/snapshot --destination /absolute/path/to/new-rehearsal
```

The helper checks the complete file inventory, hashes, source-archive member types and paths before extraction. It never overlays an existing destination. Output has `source/`, `history/`, and optional `private.env`. Inspect it before any deliberate production replacement. A checksum proves consistency with the manifest, not who created the snapshot; use a snapshot you trust.

For an isolated inspection, copy configuration deliberately into the restored source checkout and set `CHROMADB_PATH` to the restored history location. Do not run two application processes against one Chroma directory. Do not replace production data as part of a rehearsal.

## Working-run recovery

Runs are stored in `workbench.sqlite3` inside `CHROMADB_PATH`, separately from immutable saved results. A pre-dispatch receipt marks each attempted provider call; completed turns checkpoint immediately. If the process disappears, the next app instance shows the run as interrupted. Polling status and opening saved work do not dispatch providers.

Resume is manual. An in-flight call or uncertain transport may have completed remotely and requires explicit acknowledgment before another dispatch. Successful contributions are reused. Provider minimum waits, lifetime call bounds, per-attempt deadlines, and attempt caps still apply. Pause stops scheduling new calls; it cannot revoke an already dispatched request or guarantee a provider charge was canceled.

When a call/attempt cap is reached, save the partial result and prepare a smaller linked follow-up. Partial generated content stays visibly partial. Saving a later checkpoint creates a new immutable version; repeat Save of the same checkpoint returns the same logical result ID.

## Portable records versus backups

Complete JSON archives contain generated records, captured sources/profiles/receipts, and optionally personal annotations. Preview import before confirming. Import is additive and does not overwrite existing local notes; conflicting content gets a new ID. A backup also includes working runs, reusable assets, organization, and configuration; it is private and broader than a shareable record archive.

Question/task/note drafts stored in the browser are not part of backups or ordinary JSON archives. Saving personal notes and saving a generated checkpoint move that work into application storage. Clearing browser site data can remove drafts and return preferences. Browser storage is neither encrypted storage nor a substitute for a stopped-app backup.
