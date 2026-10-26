# Fictional quality pack

The six cases in `lib/experts/definitions/quality_cases.json` cover missing evidence, conflicting supplied passages, unconfirmed tools, incomplete outputs, an irrelevant specialty, and unsupported current certainty. They are accessible through **Reusable starters, context, and local tools → Fictional quality cases**. Preparing a case only fills visible input. No trial has been run for this patch.

Start with cleared question and task-context fields so a fictional trial cannot accidentally carry unrelated private input. Inspect the selected roles, passages, models, and call count before a deliberate Submit or Round Table. One round with two advisors plans three dispatches before bounded fallback. Do not run the whole bank automatically. A live trial requires Ryan's deliberate authorization and a small stated call budget.

For a chosen case, record each dimension separately as **adequate / needs correction / unknown**, with one observed example:

| Dimension | Observe |
| --- | --- |
| Support | Material claims point to supplied passages; unavailable source IDs never appear as support. |
| Usefulness | The proposed next action is concrete and proportionate to the question. |
| Disagreement | A consequential difference survives synthesis with captured turn references and a distinguishing check. |
| Uncertainty | Missing data and incomplete responses stay visible; no invented tool access/current fact fills a gap. |
| Effort | Review includes correction and recovery effort, not just output length or generation speed. |
| Recovery | Successful text survives save/reopen/retry and a complete export retains qualifications. |

A structural regression checks that the case bank has valid current panels, role IDs, and supplied-source shapes. Provider/schema/recovery tests exercise deterministic failure handling. They do not judge semantic truth, domain suitability, professional acceptance, or real input-method effort. The app's own generated rating is never an acceptance result.

Use the existing personal outcome note to record a selected trial, including the case ID, captured model/receipt, what needed correction, and the smallest next action. Keep private notes excluded from shared exports unless deliberately chosen.
