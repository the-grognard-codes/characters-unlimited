# 19B validation

Public application tests failed first at unsupported level3, then passed with the source oracle: initial PE14+D6(4)=HP18, gains2/3 add4 each forHP26; Related6/Secondary9; Cook60. Undo3→2→1 restoresHP22/18 and retains a later journal as a recovery save. Export/import and replay reuse both dice without calling the die provider.

Further red/green checks cover creation at4, in-range XP changes without dice, invalid lower/out-of-range levels, level15 XP286501 and HP74, Related9/Secondary14, malformed/missing/source-altered/nested histories and missing advanced XP. Current+historic exact pins validate each snapshot; ordered flat caches do not apply future HP gains after undo.

Independent combat implementation used original table oracles for Expert3/Knife3, Assassin15, late acquired/reselected training, untrained Assassin gun contributions and P.S.3–7 damage. Root integration tests first caught original equipped-gun bonuses and misclassified Hand to Hand physical damage; corrected equipped Knife1D6+6 and Energy Pistol11 single/15 aimed at training15. Low-strength knife expressions use the reviewed physical damage rule and preserve unresolved rounding.

Standards review found missing XP validation and absent PDF conditional notes; both reproduced failing public tests and were corrected. Spec review found the stale level2 gap message and inability to complete original combat choices after higher-level creation; explicit earlier learned-level selection now yields Expert15 attacks7, Knife+5 and Energy Pistol+8, retaining those dates on reselection. The proposed Assassin knife-strike restriction was withdrawn after the source confirmed that ancient W.P. bonuses combine with Hand to Hand bonuses. Final separate Standards and Spec reviews approve the corrected bounded implementation.

Actual Chrome workflow creates a character, selects Expert/Knife at1, generates resources, jumps to15 and shows all14 HP dice (finaldie3,HP79). Undo returns14 and preserves a level15 recovery; replay retains the same final3die andHP79. Restart on the final runtime retains both saves. Earlier learned-level controls subsequently complete Assassin and Energy Pistol at1; combat shows8attacks,initiative4,strike6 and the earned source moves. No browser console errors were recorded. Screenshots retain the advancement result and learned-level controls.

The browser fixture exported4 editable PDF pages. Native page1 preserves reference artwork and showslevel15/HP79/advanced skills/Expert combat. Continuations show every active die, learned levels, strikes, conditional critical/knockout/death-blow notes and exact contributions. Rendered first/continuation/finalpages were inspected; editing the native name field, saving and reopening retained the new value. Generated preview images are included as evidence; original book pages are not committed.

Final local suite: 216 tests pass (one frozen-only skip); mypy74, compilation and all browser JavaScript syntax checks pass. Frozen Windows validation runs on the PR before merge. Parent19 and full-corpus acceptance remain open; this is not the final retrospective.

Both Windows runs37160859638/37160862556 passed full checks, frozen build and level15 undo/replay/restart workflow. PR #56 merged as4a12a74. The bounded19B slice is complete; parent19 remains open.
