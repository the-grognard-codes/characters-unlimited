# Retained numeric contributions

Owned class `class_bonuses` may add `rolled_bonuses`: a bounded list of source-bound additive rows with exactly `id`, `name`, `target`, `formula`, and `source`. Targets use the existing perception, saving and combat identities. Formulas use the shared ordinary recorded-formula contract, including exact integer bounds; they do not use attribute exceptional or house-rule dice. Fixed integer additions keep their previous declaration and output.

Every profile, including inactive owners, preflights the entire declaration, target, source, possible formula bounds and distinct identities before initial dice. Fixed and rolled contribution identities must also be distinct. Creation retains the raw dice once in `numeric_acquisitions`, keyed by contribution identity, using the existing acquisition receipt shape. Profiles without rolled additions create no new save field.

Numeric projections replay all required receipts from the pinned profile without dice. Missing or extra identities, malformed formula groups and invalid faces reject. The ordinary contribution projection preserves source and amount explanations for builder and sheet callers. Initial and later advancement snapshots retain the same permanent receipts; altered historical dice reject portable validation. Undo restores those receipts and replay does not reacquire them.

Rule-correction previews reject changes to permanent rolled declarations, including formula and source changes. Receipt migration is separate required work. Exact prior archives and their saved pins stay available.

Public workflow witnesses: `tests/test_retained_numeric_contributions.py`. The Psi-Stalker source use is a retained D4 magic-save bonus; this contract alone does not activate or certify that class or any racial content.
