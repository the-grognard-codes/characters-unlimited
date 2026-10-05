# 22E3 explicit class ownership validation

Review base:13a9ff5d4e9934f7d63f2e758ca3846235fee90c (PR100).

A public test first reproduced an incomplete unselected City Rat profile being accepted while creating the default class. Strict ownership now rejects with the profile/field name before any dice or saved character. The test's character-list method was corrected from a nonexistent helper to public `list()` before its first successful run.

Additional public witnesses use synthetic `owned-v1` declarations for both existing class identities. The root skill allowance, automatic grant, resources and advancement are deliberately unusable; default and nondefault owned profiles still generate independent allowances, retained starting HP and PPE growth and reopen their exact bundles without dice. These witnesses first passed after ownership implementation and are not claimed as initial failing tests. Unknown/null formats, absent default profile, unsupported callback field, wrong field type and mismatched unselected owner all reject before dice.

Three focused tests pass (1.917 seconds); mypy138 passes. No accepted rule bytes change. Shape/ownership validation is bounded; it does not certify nested mechanics, source completeness or full class/race/R.C.C. imports. Independent review, final regression/static/archive audit and Windows/frozen checks pending.

Both independent reviews APPROVE. Compilation, all browser syntax/whitespace checks and27 archived legacy class projections pass. Mapping-valued fields such as combat currently replace whole mappings; explicit shared fragments are a follow-up to avoid duplicating nested catalogs across broad class imports.

Final full423 tests pass (355.106 seconds, one frozen-only skip). Both reviews approve; mypy138, compilation, browser syntax, whitespace and27 legacy projections pass. Exact-head Windows/frozen checks remain the publication/merge gate.

PR101 merged as `30b8da6590aed44024b544c40b6b7df1d340663f` after both exact-head Windows runs37244277796/37244275193 passed, including frozen executable validation. App attachment failed because the thread already has100 attachments; the PR remains available at its GitHub URL and no older attachments were removed.
