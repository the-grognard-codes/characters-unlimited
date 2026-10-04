# 22B1: Shared selection groups and entitlements

**Parent:** 22/05/06/09/10/11/12. **Status:** done.
**Blocked by:** 22A and its merged Windows checks.
**Design:** `docs/shared-rule-framework.md`.

**Base:**118d15d7a105f385eae6fcf97c5f75ec02c9da45.

Implement a shared, declarative selection-group projection behind existing player workflows. First adapters: Rifts required select groups, Heroes program choice groups and mutant power-category counts. Preserve exact pins, old selections/receipts and player-facing warning semantics. Keep source-sensitive differences explicit in data; no class/race-ID dispatch. Required text-language choices keep their existing normalization/exclusion adapter.

Define allowance, referenced eligible option identities, positive weighted costs, distinct identity accounting and unresolved fixed-grant credit. Calculate eligible/credited/remaining; adapters preserve their nonblocking warning text. Unknown cost references or malformed costs are rule-data errors; excess/ineligible player choices retain their existing honor-system behavior. Automatic program grants still depend on group eligibility and certified credit. Directly selected reviewed powers retain their existing active effects even when a starting allowance is exceeded; a budget warning does not introduce an approval gate. Generalized category/tag filters, full fixed-grant composition and free-text identity accounting remain22B2 work; this increment compiles the existing category-filtered catalogs into explicit referenced options.

Prove two current game-specific adapters share the same operations. Independently verify allowed/excluded choices, exact counts, duplicates/granted identities, weighting, source explanations and backtracking at the agreed CharacterApplication/portable seams. Keep HTTP/PDF projections compatible; add focused behavior tests before implementation. Review, validate and merge this slice before broadening to education/skill pools in22B2. Magic/psionic content and full importer remain blocked by their shared effects/resources contracts.

Merged in PR90 as ec893471c9296ce75e52a1114fc4a2815feb3111 after exact-head Windows37228954932/37228951577 passed, including frozen executable checks.
