# 22H racial creation validation

Review base: `32ad13d99c0aaf13bdd3693dfbae09f4dc59be50` (PR109). Contract: `../racial-creation-contract.md`.

Before implementation, malformed unselected pairing declarations were ignored until initial dice, and multiplied racial pools were unsupported. Four new public workflow witnesses now cover declarative race defaults, multiplied pools with retained automatic/class bonuses, incompatible creation/import rejection, whole-catalog preflight, both games and legacy cross-product behavior. Final affected suite26 tests passed in14.210 seconds after the review repair; mypy157, Python compilation, all browser JavaScript syntax and diff checks pass. No accepted archive changes.

Actual local browser creation on port8816 verifies filtering to the synthetic race's City Rat pairing, compatible class retention when returning to Human, extra/drop generation, SPD134 and normal class skills. The base113 comes from retained4/4 x10 +33; City Rat adds5 and automatic Running adds16. The numeric expression follows the published Forest Runner attribute rule; the fixture pairing is explicitly synthetic and does not claim a book entitlement. Final UI initialization uses the profile's first class, subsequent changes retain compatible choices. Screenshots: [pairing](22h-creation-pairing.png), [formula](22h-racial-formula.png).

The actual browser-created witness's editable Rifts PDF was exported and rendered. Page1 visibly retains race/class, SPD134 and City Rat skill percentages without clipping; field assertions and exact portable reopen/history also pass. Existing Poppler Symbol/ArialUnicode warnings did not affect inspected text. No sheet layout changed.

Spec review approves with zero findings, including final default initialization repair. Standards review found one exceptional-roll overflow path; reachable bonus bounds and final total guards repaired it, with finite/unbounded unselected-profile regression cases. Both review axes approve the final code with zero unresolved findings. Exact-head Windows/full/frozen gates remain pending before merge. This is shared creation framework, not complete nonhuman/R.C.C. content or saved-identity backtracking certification.

PR110 merged as `e0faf49ff33aa9810925677a9cf84e2201a8eea7`. Both exact-head Windows runs37326418001/37326541730 passed at `1fd74f354a69c4f4430dd6b77d79aa71c38646cf`, including frozen executable checks. Full462 tests (561.337 seconds in PR run); one frozen-only skip exercised separately. No subsequent product changes.
