# 19B2 validation: Heroes Human Mutant later advancement

Separate immutable `heroes-higher-advancement 1.0.0` extends the first pack through level15. XP/direct progression and higher starting levels retain intermediate flat snapshots, ordinary HP dice, per-level endurance dice, learned skill/training ages and Secondary awards. Later maneuver choices remain19B3; special paths, parent19 and full corpus remain open.

- Both independent review axes approve after exact current/history pin repairs. Missing dependency pins reject cleanly rather than borrowing historical definitions or raising an unhandled exception.
- Complete local suite:367 tests in282.332 seconds, passing with one frozen-only skip. Required mypy116 files, compilation, all JavaScript syntax checks and corrected documentation whitespace check pass.
- Seven new public tests cover every XP boundary, all four numeric training profiles, untrained actions, starting higher levels, learning age/caps, endurance before/inactive/late acquisition, all-level undo/replay without resampling, portable tampering/update guards and editable PDF values. First-advancement boundaries are also tested with their historical archive.
- Frozen Windows workflow advances to15, verifies28 ordinary/power dice, PDF values, recovery at14, replay and reopening. Windows PR checks pending.

## Source evidence

Original printed17/PDF18,48/PDF49,69/PDF70,71/PDF72 and352/PDF353 were visually inspected. The current Markdown snapshot D126...35af is distinct from the immutable historical first-pack source02927...7282. The new pack records its own locators and fingerprints. Martial Arts level2 disarm+2 matches the original table and first pack, correcting the old inactive raw progression omission without editing old packs.

## Browser and editable PDF

A High School Human Mutant with I.Q.16, Acrobatics/Gymnastics/Climbing/Basic and Secondary Prowl startsHP44. Direct15 records fourteen D6=4 and fourteen power D4=4, producingHP156, with P.E.24/S.D.C.202/P.P.E.24 unchanged. Basic has7 attacks, strike2, initiative1, parry/dodge3 and damage4. Secondary allowance20. Own-rate growth changes the winning shared balance check to Gymnastics98 over Acrobatics95; tie-capped back flip uses the deterministic Acrobatics entry. Climbing/Rappelling and Prowl cap98.

Removing endurance yieldsHP84 and retains inactive power receipts. Reselecting restores156. Undo15→14 yieldsHP148 and a separate recovery; replay restores156 with the same dice. Autosave reopening preserves LEVEL15 and all28 receipts.

[Browser](19b2-browser.png), [editable sample](19b2-advancement-sample.pdf), [first page](19b2-original-page-1.png).

All six PDF pages were rendered with form appearances and visually inspected. No clipping or lost continuation content. Exact field values and every populated widget value/appearance were verified; edited Name survives save/reopen and rendering. No assertion is made about every third-party editor. Numeric combat automation and earned conditional guidance are included; later maneuver choices are explicitly unfinished.
