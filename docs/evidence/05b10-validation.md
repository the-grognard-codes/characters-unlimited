# Boxing validation

Before the slice, public selection failed because Boxing was unavailable. Immutable Rifts skills 2.3.0 adds the reviewed definition (72 total). Public workflows verify +1 attack, ordinary defenses, P.S./S.D.C., actual dice with house options enabled, nonstacking duplicates, Secondary exception guidance, resource generation, removal/reselection, portable/reopen and explicit old-pin updates. Acquisition never rolls a knockout duration. The editable export contains the source rule in form-field notes.

The first full suite passes 168 tests (one frozen-only local skip), mypy over 56 files, compilation and all browser syntax checks. Standards review suggested removing redundant attacks initialization; that cleanup passes focused tests and targeted re-review. Spec review reports no finding. The final full checks after cleanup and the frozen regression addition also pass (168 tests, mypy, compilation and browser syntax). Windows frozen results are recorded before completion.

Edge selected Boxing as Related, recording S.D.C. faces 6,4,6 and P.S. 15. Basic training shows five attacks, parry/dodge +2 and roll with impact +3; gunfire dodge remains zero. Removal returns four attacks and zero parry/dodge; reselection restores the original values. Reload/reopen preserves the same dice. [Browser evidence](05b10-boxing-browser.png) was visually inspected. Rendered editable PDF pages 1 and 3 preserve the reference layout, display five attacks and bonuses, leave Boxing percentage cells blank, and retain the natural-20 knockout notes through the continuation without clipped text. The unchanged original page 2 is preserved.

Other fighting techniques, levels and complete corpus acceptance remain open.

The first frozen Windows run exposed a test assumption: randomized P.P. can make parry absent below eight or add its own bonus above fifteen. The regression now checks the independent Boxing +2 and Athletics +1 contribution entries, retaining the five-attack assertion. Product behavior was unchanged; targeted Standards re-review approves. A local frozen rebuild and both replacement CI runs validate the correction.

Both corrected Windows runs pass (37142194086 and 37142196882). The locally rebuilt frozen application also passes the complete workflow outside sandbox restrictions, including hidden controller startup; the first sandboxed GUI attempt timed out. Merged in PR #45.
