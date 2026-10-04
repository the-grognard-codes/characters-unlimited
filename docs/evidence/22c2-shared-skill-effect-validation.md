# 22C2 declarative skill effects verification

Review base: `2ad72dfdf4d12049c0525799d2c587a4de47ead1` (22E2/PR97).

Two public fixtures were RED: Rifts Cooking stayed50 instead of57; selected mutant effect left Heroes Basic Mathematics45 instead of52. Both now pass through the shared selector/effect engine. Rifts fixed and selected skills receive an overlapping selector effect once, with exact source metadata. Heroes active power effects disappear on removal while acquisition history survives portable reopening.

Required Native Language demonstrates the98% cap. Two separate same-name scholastic effects add9% to Pick Pockets, retain two source contributions and flow through its eligible contextual check. Effects do not grant Palming. Malformed operation/amount/source/unknown-target/extra-field definitions reject before any initial dice. A malformed inactive power effect prevents new power dice and leaves the character unchanged. These safeguards passed first against the implementation.

The cap fixture initially assumed a lower base; increasing its synthetic bonus to20 exercised the intended cap. The contextual fixture initially omitted its existing Seduction eligibility; selecting it corrected that fixture error. Neither is an implementation regression or a new RED claim.

Eleven shared/legacy power tests pass in5.954 seconds. Static checks, broader regression and independent reviews are pending. No accepted source definitions change.

The Spec review found default-class effect inheritance in a nondefault profile. A public City Rat case reproduced the leak (RED); resolved profiles now default their own effects to an empty list. The initial full run was stopped for this repair and is not a final pass.

The Standards review identified total overflow despite individually bounded amounts. The Spec review identified unpinned typed power target catalogs. Public regressions reproduced both; projected primary/contextual totals now reject out of range before save/export, and typed power selections pin both exact skill and education packs. A newer active catalog retains saved Basic Mathematics52; removing its required pin rejects import. A synthetic overflowing contextual modifier rejects skill selection atomically. Its initial fixture incorrectly assumed an uncapped context base; the existing capped-primary semantics required a synthetic contextual modifier instead.

Final15 affected tests passed in7.306 seconds. Required mypy passed134 source files; compilation/all browser syntax/whitespace passed. Both independent re-reviews APPROVE without rerunning tests. Final full regression passed413 tests in313.793 seconds, with one frozen-only skip. A supplemental editable-PDF assertion passed (1 test,1.200 seconds), confirming both Cooking fields hold67. Compatibility audit passed27 Rifts class projections/22 Heroes skill archives/10 power definitions. Exact-head Windows/frozen validation is pending. Publication base is the identical merged22E2 tree `c074870950295374f7831e12ebaf3dd8d4538e66`.
