# 22B1 shared selection framework verification

Base:`118d15d7a105f385eae6fcf97c5f75ec02c9da45`. Contract:`docs/shared-selection-group-contract.md`. The shared module handles distinct eligible/weighted credit; adapters preserve game-specific grants, existing records and honor-system guidance. Accepted pack bytes and UI/PDF layouts are unchanged.

## Before and after

- Required select groups ignored declared weights. The synthetic two-slot group with a two-cost choice reported one remaining; the regression was RED, then GREEN after sharing group accounting. Duplicate choices earn one credit/grant; an additional one-cost choice produces an overage without removing entered choices.
- Heroes program rules accepted zero, fractional and boolean costs, unknown cost references and a boolean allowance. Five subcases were RED; all now reject before saving the character.
- The Minor allowance counted every active power irrespective of its declared category. A synthetic category fixture was RED; now only referenced Minor identities consume Minor slots, while entered reviewed powers remain active under existing honor-system behavior.
- Outcome selection accepted boolean, negative and out-of-range source counts. Three subcases were RED; shared allowance and recorded-formula validation now reject before persistence without changing retained dice/history format.
- Spec review found that case-folding opaque option IDs could grant a valid option but miscount its cost. The public `PilotA`/`pilota` fixture was RED; exact select identities now control grants, duplicate detection and credit, while text specialties retain normalization.

Synthetic fixtures exercise import mechanics; they are not new book rulings or accepted content.

## Standards

APPROVE. No actionable documented-standard violation or Fowler smell. Read-only archive inspection found no incompatible Heroes groups/categories. Focused re-review approved the exact-ID correction. Reviewer did not rerun tests.

## Spec

APPROVE after exact-ID correction. One new bounded regression was identified and fixed; no further actionable22B1 findings. Reviewer did not rerun tests. Generalized categories/tags, full grants and all-pool specialty accounting remain future increments.

## Checks

- Final affected37 tests passed in16.861 seconds across shared-group, required-group, Heroes Physical/program/Communications, power and budget workflows.
- Required mypy passed over122 source files; Python compilation, browser-script syntax and whitespace checks passed.
- The initial full run was interrupted after the review repair and is not a final result. Final full suite passed: 383 tests in 252.753 seconds, with one frozen-only skip. Exact-commit Windows/frozen outcomes remain pending.
- Existing HTTP and editable-PDF tests protect retained projections; this increment changes no visual/media element.
