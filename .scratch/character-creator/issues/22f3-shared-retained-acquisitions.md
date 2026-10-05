#22F3: Shared retained ordinary acquisition lifecycle

**Status:** DONE. **Review base:**67062684213a89888a06ff033e9cc44e190cf54d (PR104).

Consolidate cache identity/group validation, whole-catalog formula preflight, first acquisition and inactive/reselection retention in a game/family-independent module. Adapt both shared Rifts/Heroes Physical acquisition and Heroes mutant-power acquisition without changing archived or saved receipt shapes, UUID/history order, resource snapshots or effects. Validate all declarations and retained inactive receipts before any new die; reject formulas whose possible bounds exceed exact-integer range. Support empty formula groups for nonrandom abilities, with adapter-specified retention of zero-die constant groups to preserve existing formats. House initial-attribute options must never affect ordinary bonus acquisition. Source/owner/UUID/history validation remains in existing adapters. No actual spell/psychic adapters/content, generic effect activation or timing are claimed.

Merged in PR105 asb9bf1790e239882823c072ba4bcaeea56023a2de after both exact-head Windows37248264225/37248267640 passed, including frozen executable validation.
