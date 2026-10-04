# Shared starting-resource formulas (22D1)

Starting HP, S.D.C., P.P.E., I.S.P. and other declared resource identities use the shared recorded numeric formula engine. Class/race names do not select a resource formula. Existing `resources.definitions[].contributions` compose formula terms and retained attribute terms.

## Formula terms

The legacy shape has `count`, `sides`, and `bonus`; it now accepts optional `multiplier` (default1). The adapter maps `bonus` to the shared `constant`. Calculation is `(sum(recorded dice) + bonus) * multiplier`. The multiplier applies to the whole formula. Shared bounds, exact allowed fields, integer/boolean distinction, die-face checks and safe result range apply. Zero-die fixed terms are evaluated during preflight, so a known overflow rejects before any resource dice.

## Attribute terms

An `attribute` contribution must identify one of the eight known attributes. Generation snapshots its effective recorded value once. Formula dice and snapshots replay from exact pinned definitions; later racial rerolls or player attribute edits do not change that starting contribution. Existing resource receipts and attribute snapshots retain their shapes. Existing manual fixed resource totals and adjustments remain authoritative.

All contribution definitions validate before generation. Resource dice ignore racial reroll-ones and extra-die options. Failure preserves the previous saved character. Portable reopening verifies source, raw dice and derived value without drawing again. Builder/PDF resource explanations consume the same projection.

Synthetic scaled P.P.E./I.S.P. fixtures are framework verification, not new accepted book rules. No accepted archive bytes change. Dynamic/nonlinear attribute terms, resource minimum operations, generalized level schedules, complete class imports and spell/psionic acquisition remain open.
