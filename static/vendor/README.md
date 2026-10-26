# Vendored browser libraries

Core pages load these local files, with no CDN requirement or npm application build:

| Library | Pinned file | License notice |
| --- | --- | --- |
| HTMX | `htmx-1.9.12.min.js` | `HTMX-LICENSE` |
| Marked | `marked-18.0.14.umd.js` | `MARKED-LICENSE` |
| DOMPurify | `purify-3.4.17.min.js` | `DOMPURIFY-LICENSE` |

`manifest.json` records SHA-256 digests and upstream release URLs for the downloaded assets. HTMX retains its existing 1.x behavior; Marked and DOMPurify have explicit pins. The files and upstream notices are retained as downloaded. No statement that these are the latest releases or free from advisories is implied.

For an update, review primary upstream release/security/compatibility notes, replace the asset and license deliberately, update its digest, and inspect the configured sanitizer/table behavior and actual HTMX swaps in an authorized focused browser pass. Keep raw-text fallback and visible dependency failure guidance. Do not introduce a frontend package/build pipeline merely to update these files.
