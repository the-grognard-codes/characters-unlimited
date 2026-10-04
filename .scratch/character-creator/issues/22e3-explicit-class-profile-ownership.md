# 22E3: Explicit class profile ownership

**Status:** in-progress. **Review base:**13a9ff5d4e9934f7d63f2e758ca3846235fee90c (PR100).

Add opt-in `class_profile_format: owned-v1` to existing Rifts rule data. In this format every class (including the former default) has its own complete profile; all supported profile fields are required, with explicit empty collections where appropriate. Shared root catalogs/system constants retain their single definitions, while root class mechanics are discarded rather than inherited. Whole-field replacement is deliberate: no recursive generic merging or executable callbacks. Validate all profiles, including unselected profiles, their shape and supported class identity fields before initial dice. Legacy packs without the format keep exact behavior; unknown formats reject. Shared profile composition module receives the allowed field set from its adapter, with no option-name dispatch.

Public tests: missing unselected profile field rejects before any dice/save; default class uses its profile rather than poisoned root values; nondefault profile has independent skills/resources/growth and portable exact-pinned reopening. Accepted archive bytes unchanged. This is ownership validation only, not complete mechanical/dependency/source certification, equipment composition, race/R.C.C. precedence or full imports.
