# Rifts generation validation

Validated 2026-10-02 against main a7e0dd0. Ten application workflow tests pass, including repeated ones, dropping after rerolls, unchanged exceptional dice, terminal Rifts bonus dice, preserved fixed/additive values, stale writes, and failed random sources. Mypy and Python/JavaScript syntax checks pass.

Browser verification covered whole-set and individual rerolls, fixed values, reopening an additive +2 without changing its mode, saving it unchanged, and retaining +2 after another reroll. History shows the discarded die, every rerolled one, and both generation settings. See [captured history](04a-roll-history.jpg).

Independent standards review approved. Spec review found incorrect editor initialization and incomplete history explanations; both were repaired and the focused re-review approved. The Heroes Unlimited source ruling and additional racial catalogs remain outside this Rifts-only slice.
