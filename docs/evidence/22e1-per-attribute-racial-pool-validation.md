# 22E1 per-attribute racial pool verification

Base:`21ab1a3a30f96a80bdbaef68330e682be5b38a9c` (merged22D1/PR95). Review baseline0d675ad has the identical tree; the dependent branch is rebased onto the squash before publication.

- Public mixed-pool fixture was RED (M.E.12 instead of22). Full replacement pools now produce M.E.4D6+6 without inherited Human exceptional dice, P.S.2D8+1 plus its retained class contribution, and zero-die I.Q.12. House extra/drop applies to each pool; per-attribute reroll, exact portable history and editable PDF M.E.22 are verified. A focused run caught and repaired a missing import; this is not a separate behavior RED claim.
- A full eight-pool map without a default works in Heroes, retaining raw I.Q.6 under automatic cap5 and allowing manual fixed40.
- Malformed later pools/exceptional rules/caps and missing defaults reject before any initial die. These passed on first execution against strict validation.
- An impossible later one-sided pool under reroll-ones was RED because earlier dice were reached; initial/whole-profile preflight makes it GREEN. Valid single-attribute options do not affect another pool and portable replay keeps its old settings.

Final16 affected tests passed in11.039 seconds. Required mypy passed131 source files; compilation, browser syntax and whitespace passed. Both independent reviews APPROVE without rerunning tests. Archive audit validated4 core archives/4 race definitions/32 resolved pools with no incompatibility. Full regression passed402 tests in311.819 seconds, with one frozen-only skip. Exact-head Windows/frozen results are pending. No accepted book definitions change.
