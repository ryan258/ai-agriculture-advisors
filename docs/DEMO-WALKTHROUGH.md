# AI Advisors demo walkthrough

This guided tour shows where different advisor perspectives change a decision in the 2.1.0 candidate. It uses one-round discussions so a two-advisor demo normally makes two advisor requests and one synthesis request; structured-output fallback or shared-pool failover can add a synthesis request. Select only the two named advisors, set **Roundtable Rounds** to **1**, and click **Round Table**. The matching examples are also available as buttons in each panel. Each live run sends its supplied text to the configured provider; use the fictional examples or approved/redacted context.

## 1. Agriculture: check before changing inputs

Select **Soil Health Specialist** and **Irrigation & Water Management Specialist**.

> A small rain-fed tomato plot sits in heavy clay. After two weeks of wet weather, lower leaves are yellowing. I have not measured soil moisture or pH, and I have not confirmed pests. Compare drainage, nutrient, and pest explanations using only these facts. Give me three low-risk observations to make before changing inputs, and say what location or field evidence is needed before recommending a treatment.

**Look for:** a separation between symptoms and diagnosis; checks that distinguish the explanations; and clear limits on advice that needs local field conditions, testing, or a confirmed pest.

## 2. Software: define a safe slice

Select **Software Architecture Advisor** and **Software Testing Advisor**.

> In a single-user FastAPI tool, I want to save a partially completed roundtable and resume only the failed call. The existing database can store successful answers, but I have not shared the route or storage code. Propose the smallest useful change, the state that must be saved, and acceptance checks proving successful answers are not repeated. Identify what you cannot determine without seeing the code.

**Look for:** a bounded implementation, explicit state and failure cases, and checks tied to the requirement. The advisors do not inspect this repository unless you supply the relevant code.

## 3. AI Workflow & Delegation: make the handoff recoverable

Select **Workflow Designer** and **Failure & Recovery Reviewer**.

> I want a remote AI coding agent to draft release notes from a diff I supply. It may read that diff and write one draft to an approved scratch location, but it cannot edit the repository or commit, push, merge, or publish. Give me the actual compact task packet, not advice to create one. Include three checks that trace each material claim to a changed hunk; mark them pending if no diff is present. Add a resume checkpoint with the input reference or hash only if available, exact instructions, draft location, status, and next step. Compare total human setup, review, correction, and recovery time with similar manual drafting; do not claim savings without a measured baseline. Distinguish prompt rules from enforceable tool permissions, and require approval or redaction before sending the diff to the hosted model.

**Look for:** an actual bounded packet, checks tied to diff evidence, a resumable record that never invents a hash or path, and a measured time comparison. Prompt instructions alone do not enforce tool access, and the hosted model receives the submitted diff.

## 4. Accessibility & Effort: reduce repeated input

Select **Voice-First Workflow Designer** and **Effort Reduction Advisor**.

> I use dictation and short work sessions. A recurring task currently means re-entering the same background and remembering several steps. Redesign it around one reusable, voice-friendly starter, the fewest practical interactions, and a saved checkpoint I can resume after an interruption. Ask at most one essential question. Include a fallback if dictation fails and keep the final choice with me.

**Look for:** a ready-to-use starter rather than advice to build one, a short checkpoint with a clear next step, a dictation recovery that does not require retyping the background, and one small trial you can compare with the current routine. The moderator should leave at most one decision for you and avoid naming tools whose capabilities were not supplied or checked.

For example, a useful starter can be as small as “Start [task]. Use background at [saved reference]. Today: [one outcome]. Next: [one action].” A checkpoint can be “RESUME: [task/reference] | Done: [last step] | Next: [one action] | Waiting on: [blocker or none].” These are illustrative templates, not a claim that anything has been saved or configured. A fallback should preserve that record and recover only a garbled field; if dictation is unavailable and no existing alternative entry point is known, it should allow a safe pause rather than require typing.

## 5. Evidence & Judgment: test a persuasive claim

Select **Claim Examiner** and **Uncertainty Reviewer**.

> A small AI coding pilot is said to cut review effort by 50% because its changes received fewer review comments. There is no human-only baseline, review time was not tracked, and the changes varied in size. Separate what the evidence supports from what it does not. Give one plausible alternative explanation and the smallest fair measurement that could change the conclusion. Do not treat agreement among AI advisors as evidence.

**Look for:** a distinction between fewer comments and less effort, a plausible confounder, and a measurement that could prove the claim wrong as well as right.

## What makes this a useful demo

After each result, ask: **What did the second advisor add? Which uncertainty changed the recommendation? What is the smallest next action?** If the advisors agree, that agreement is still generated by AI personas; it is not independent verification. Advisors work only from the question and text you provide. They do not browse for current facts, inspect files, or verify the scenarios.

The concise format has failed its purpose if later turns repeat the same closing points, the synthesis merely tells you to create the requested artifact, or it invents a tool capability, saved location, measurement, or required decision. Record the specific sentence that failed; shorter output alone is not evidence of better judgment. Turn brevity and the one-question rule are prompt instructions, so assess the actual result.

For a live task, replace the fictional scenario with a short, redacted description of your own. Add only the context needed to distinguish options. Save the result if you want to reopen the captured advisor instructions later. If a provider limit interrupts a roundtable, completed answers remain available; retry only the missing advisor or synthesis.

For the candidate's final acceptance trial, use just the Accessibility & Effort example, save/reopen it, and compare its Markdown and HTML exports with the on-screen handoff. Follow the [release readiness note](RELEASE-READINESS.md) to record what passed and what remains unknown.
