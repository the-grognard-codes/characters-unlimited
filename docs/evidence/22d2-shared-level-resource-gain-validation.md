# 22D2 shared level-resource validation

Review base: `9107d7c4793fe7adc0db996d121b5e44d32e9bc5` (PR99); its merged tree is `6debd9a12fc69dd541f7f8ff84c3751e84d30475`.

Synthetic public application fixtures originally showed no additional growth (Rifts PPE10 rather than19, Heroes24 rather than48), accepted a combined overflow, and leaked default additional class growth. Shared acquisition/projection/ownership guards repair those failures. Invalid later targets/formulas/evidence reject before dice and preserve saved state; this preflight test first passed against the implementation and is not claimed as an initial failing test.

Supplemental export/first-level undo checks exposed Rifts page-less citation failure and Heroes inactive-cache dependency access. Both are repaired. Resource citations share a formatter across editable exports; tests assert resource field values and book/section evidence. One Rifts evidence assertion initially ignored PDF line wrapping; the assertion now normalizes whitespace. Six focused tests pass (5.507 seconds). Heroes undo all the way to level1 and replay3 retains all first/later rolls. Manual fixed totals and forged value/source/faces are covered.

Final static checks, full regression, archive compatibility audit, independent reviews and exact-head Windows/frozen runs pending. No accepted archive bytes changed and no source-grounded new progression rule is claimed.

Standards review found a valid starting-contribution label could be overwritten by a level label. A public regression reproduced HP25 instead of32; level labels now disambiguate against existing contributions and preserve both values. Spec review found no actionable issue. Seven focused tests and re-review pending.

Seven focused tests pass (7.534 seconds); mypy136, compilation, all browser-script syntax and whitespace checks pass. A compatibility audit validates25 archived progression declarations. The audit helper initially used an incorrect composition function and browser directory; those helper errors were corrected without product changes. Both independent re-reviews APPROVE. The pre-repair regression run was superseded; the final full run is in progress.

Self-review also reproduced a zero-die multiplied overflow drawing two ordinary HP dice before failure. Zero-die gains now evaluate during definition preflight, matching starting-resource behavior. The added subcase validates no dice or saved-state change. Final exact-head CI will cover the complete suite after this repair.

Final affected suite:38 tests pass (99.949 seconds), including existing progression/resource workflows and all seven new public tests. Both final repair reviews APPROVE. Full exact-head Windows/frozen checks remain the merge gate.

The local full420-test run passed (366.300 seconds, one frozen-only skip) before the final zero-die preflight subcase; the final38-test affected suite covers that repair. Exact-head CI remains authoritative for the complete final tree.

PR100 merged as `7f168d187cd1f045a67d631a34985d150890534b` after both exact-head Windows runs37243495491/37243470670 succeeded, including complete regression and frozen executable validation.
