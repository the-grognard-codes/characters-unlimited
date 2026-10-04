# 22B1: Shared selection groups and entitlements

**Parent:** 22/05/06/09/10/11/12. **Status:** ready-for-agent.
**Blocked by:** 22A and its merged Windows checks.
**Design:** `docs/shared-rule-framework.md`.

Implement a shared, declarative selection-group projection behind existing player workflows. First adapters: Rifts required select groups and Heroes mutant power-category counts. Preserve exact pins, old selections/receipts and player-facing warning semantics. Keep source-sensitive differences explicit in data; no class/race-ID dispatch.

Define allowance, referenced eligible options or reviewed category/tag filters, positive weighted costs, distinct option/specialty identity and fixed grants. Calculate eligible/used/remaining and nonblocking warnings. Unknown references or malformed costs are rule-data errors; excess/ineligible player choices remain honor-system selections. Do not grant effects merely because a retained choice exists outside its entitlement.

Prove two current game-specific adapters share the same operations. Independently verify allowed/excluded choices, exact counts, duplicates/granted identities, weighting, source explanations and backtracking at the agreed CharacterApplication/portable seams. Keep HTTP/PDF projections compatible; add focused behavior tests before implementation. Review, validate and merge this slice before broadening to education/skill pools in22B2. Magic/psionic content and full importer remain blocked by their shared effects/resources contracts.
