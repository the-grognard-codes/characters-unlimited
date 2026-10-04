# 19B1 validation: Heroes Human Mutant first advancement

Implemented the reviewed first advancement contract in `docs/heroes-first-advancement-contract.md`. Levels 1–2 are supported; levels 3–15, later maneuvers, other power categories and the full supplied corpus remain open.

- Both independent review axes approve. Repairs addressed inactive cached power-die display, actual combat level and stale level-one-only guidance. Final display delta also approved.
- Final local suite: 360 tests in 201.042 seconds, passing with one frozen-only skip. Required mypy checks 115 files. Compilation, all JavaScript syntax and whitespace checks pass.
- Eight public workflow regressions cover XP boundaries, all four training styles, untrained combat, independent check rates, learned levels, starting level two, ordinary/power HP timing, fixed/adjusted resources, exact portable pins, tampering, undo/replay, upgrade guards, stale writes and HTTP authorization.
- Frozen Windows workflow now advances, exports, undoes, replays and reopens its Heroes Physical character. Windows PR checks pending.

## Browser and PDF evidence

A High School Human Mutant with Acrobatics, Gymnastics, Climbing, Basic training and Secondary Prowl starts at HP44. At 2,051 XP the recorded ordinary D6=4 and endurance D4=4 produce HP52. P.E.24, S.D.C.202 and P.P.E.24 stay unchanged. Parry/dodge rise to2; Climbing/Rappelling72/62 and Prowl42. Independent shared checks are balance69, high wire70, rope79, back flip79 and bars70.

Removing the endurance power produces HP32, P.E.15 and S.D.C.42, with its level-two die retained but inactive. Reselection restores HP52 using the original acquisition and level-two rolls. Undo restores the pre-level character and creates a separate level-two recovery; replay uses the same 4/4 dice. Autosave reopening preserves the results.

[Browser evidence](19b1-browser.png), [editable sample](19b1-advancement-sample.pdf), [first page](19b1-original-page-1.png).

All five PDF pages were rendered with form appearances and visually inspected: no clipping or lost continuation content. Level, resources, skill percentages, combat, XP and learned levels match the projections. Every populated widget value and appearance was checked. The Name field was edited, saved, reopened and rendered successfully. No claim is made about every third-party PDF editor.

Immutable legacy packs remain unchanged. Existing characters retain exact pins; progression is pinned explicitly when first used. Undo preserves the original pre-level values and selections plus the progression pin needed to validate replay. Recorded progression-definition changes are rejected pending a migration contract.
