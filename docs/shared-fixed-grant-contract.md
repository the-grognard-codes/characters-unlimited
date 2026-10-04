# Shared fixed grants (22B2C)

`grants.py` resolves fixed entitlements against an exact pinned catalog. A declaration list contains explicit identity strings, selector objects with exactly one `selector` field, or both. Declaration order is preserved; each selector produces catalog order. The final identity list is distinct, so overlapping grants and player selections apply each acquisition once.

```json
["running", {"selector":{"any_of":[{"tags_any":["reviewed-tag"]}]}}]
```

The example demonstrates syntax, not a new accepted book rule. Lists are bounded to1000 declarations and reuse the strict catalog selector contract. Unknown explicit identities/references, unknown wrapper fields and malformed catalog metadata reject. A valid selector can match no options; that does not certify content completeness or missing dependencies.

## Adapters

- Rifts and Heroes retained Physical acquisitions resolve `physical_grants` against reviewed Physical definitions. Non-Physical references reject in this adapter. Legacy identity lists and duplicate grant-once behavior remain unchanged.
- Heroes programs retain legacy `skill_ids`, or declare `skill_grants`, but cannot supply both. Every program's fixed grants validate, including unselected programs, before saving. Universal skill identities use the same resolver. Projection exposes compiled `skill_ids` to existing UI and PDF consumers; the raw selector declarations remain in the pinned archive.

Education eligibility, highest eligible program bonus, repeated-program warnings, prerequisite honor choices and separate grant/effect decisions remain in their adapters. Selecting a Physical grant records its original dice. Removal and reselection reuse retained acquisitions; an automatic grant remains active when an optional duplicate is removed. Portable validation uses exact pinned definitions.

This module resolves identities only. It does not decide acquisition time, training age, effects, sources, prerequisite enforcement, level scheduling or conditional entitlements. The containing reviewed definition and acquisition adapter retain source evidence. Complete spell/psionic/power grants, generic per-grant provenance, class/race composition and importer certification remain open. No accepted source pack changes are included.
