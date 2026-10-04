# 22A shared recorded formula verification

Base: `96a6a9dc34ba03f3c5519068db3be38220e406a1`. Scope: class, Physical-skill and chosen mutant-power ordinary bonus formulas; see `docs/shared-rule-framework.md`. No accepted pack bytes, source rulings, receipt formats or UI/PDF layouts change.

## Before and after

- Malformed power formula constants and an unknown operation field were accepted. Public acquisition regression reproduced three failures before the fix; all cases now reject without changing the saved character. Added bounds, boolean/zero multiplier and arithmetic-overflow cases also pass.
- A synthetic class formula `(1D4 + 3) * 2`, with a recorded 4, contributed 7 instead of 14. The regression failed before consolidation; now M.A. is 12 + 14 = 26. Rerolling its racial base to 9 leaves its recorded class contribution intact (23), and portable replay validates it. This fixture demonstrates formula mechanics, not new book content.
- A synthetic Running formula `(4D4 + 3) * 2`, with four recorded 4s, was unsupported. Now it contributes 38 to a base Speed of 12, giving 50; removal returns 12 and reselection/import returns 50 without drawing again.
- Spec review found that an overflowing fixed resource effect could be saved and fail only on projection. The new public regression failed before repair; acquisition and retained-receipt validation now reject the formula before persistence, including effects with no dice.

## Standards

APPROVE. Independent review found no actionable documented-standard breach or Fowler smell. A read-only scan of 278 archived class/Physical/power formula entries found no incompatible shape. Focused re-review approved the zero-die repair and atomic-regression test. Reviewer did not rerun the suite.

## Spec

APPROVE after repair. One actionable finding, fixed: zero-die Physical resource overflow was not checked before save. Reviewer reproduced atomic rejection after repair. Shared grants/effects/importer and magic/psionics are explicitly future work rather than asserted deliverables of22A.

## Checks

- Initial affected31 tests passed. After review repair, affected20 tests passed, including the new fixed-resource regression.
- Required mypy passed over120 source files. Python compilation, all browser-script syntax and whitespace checks passed.
- Final full suite:378 tests passed in298.833 seconds, with one packaged-executable-only skip locally. Exact-commit Windows37226460205(11m35s) and37226434948(9m55s) passed, including frozen executable checks. PR89 merged as118d15d7a105f385eae6fcf97c5f75ec02c9da45. The earlier full run was deliberately interrupted after the review repair and is not claimed as a final result.
- Existing automated HTTP and editable-PDF workflow checks exercise the consolidated mechanics; no visual presentation changes or new PDF artwork are part of this increment.

## Remaining scope

The complete class/race mechanical importer, shared grants/effect composition, spell and psychic paths, and remaining supplied-book content remain open. No retrospective or release-complete claim is made.
