# 19B3 validation evidence

Base:785d50ec0b18a77f1463f553f45b0831cdd1c744. Working branch:codex/19b3-heroes-kick-choices.

## Standards

Independent review found one exact-source issue: Python equality accepted an integer locator changed to a float. Sorted finite JSON comparison and a public portable regression repair it. Focused re-review: APPROVE; no remaining documented or heuristic findings.

## Spec

Independent review: APPROVE; no actionable bounded findings. Kick eligibility, damage, retained choices, pins and source guidance match docs/heroes-kick-choice-contract.md. Broader maneuver contexts and corpus remain open.

## Verification

- TDD: first Basic selection test failed for absent public operation, then passed. Other styles/jump contexts failed before their implementation. PDF restriction test failed before continuation integration. Upgrade safety failed before the migration guard. Exact-source float regression failed before strict source comparison.
- Seven new public tests pass: all four styles, learned age, early/excess/outside choices, removal/reselection, undo, old saves, authenticated/stale HTTP saves, hostile portable edits, changed rule update rejection and editable PDF continuation.
- Final full local run:374 tests in267.351s, PASS; one frozen-only skip. Required mypy118, compileall, all browser JS syntax and whitespace checks PASS.
- Browser: level15/PS20 Martial Arts chooses Roundhouse/Wheel/Crescent/Backward Sweep; allowance4/0remaining. Karate2D4+9, Power Karate2x2D4+9, Crescent2D4+2+9, Power Crescent2x2D4+2+9; no-damage sweep remains no damage. Jump6D6+9 uses all melee attacks; Flying Jump4D6+9 uses2; no Power Jump. No-training profile removes learned kicks. Basic saves Snap separately. Switching/reloading/reopening restores Martial choices and displays inactive Basic receipt.
- Editable five-page PDF: all expected logical values and widget values agree, every populated widget has an appearance. Name edited/saved/reopened successfully. All five original pages and edited first page rendered with forms and visually reviewed: no clipping, missing overflow, overlap or stale Name appearance. No claim of validation in every PDF reader.
- Source originals printed67-69/PDF68-70 and printed71/PDF72 visually reviewed. Karate discrepancy is explicitly disclosed; specific training/prose2D4 used. Original jump paragraph restricts jump kicks to Martial Arts, separating all-actions Jump from two-action Flying Jump.
- Frozen Windows scenario now includes retained Snap choice across later advancement, undo/replay and reopen. Windows checks pending on exact committed PR head before merge.

Evidence:19b3-browser.png,19b3-kick-panel.png,19b3-kick-sample.pdf,19b3-original-page-1 through5.png,19b3-edited-page-1.png.
