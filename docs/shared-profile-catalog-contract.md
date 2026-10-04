# Explicit shared profile catalogs (22E4)

Owned class profiles may reference a shared mapping instead of repeating its catalogs. `profile_catalogs` contains at most1000 entries. Each stable identity has exactly `field`, `value` and `source`; field identifies a supported mapping-valued owned field, value is a literal mapping, and source requires nonempty book and section evidence. Every catalog validates, including unused entries.

A profile field may contain exactly `catalog_ref` and `values`. The reference must exist and match that owned field. Its values mapping supplies class-owned keys that are absent from the catalog. Overwriting catalog-owned keys rejects; choose a different reviewed catalog when shared facts differ. Catalog mappings cannot themselves be reference envelopes. No recursive reference expansion, callbacks or prose evaluation is performed.

All profiles resolve and validate before initial dice, including unselected profiles. Resolved profiles feed existing class-owner checks, creation, derived calculations and exact-pinned portable reopening. Original archive definitions remain unchanged; resolved views deep-copy catalog and owned values. Root catalogs remain available with their source evidence in the composed view and the exact portable archive.

This allows a single combat training/W.P./attribute-chart catalog to serve distinct class choices and proficiency allowances. Plain owned profiles and legacy accepted archives retain their behavior. Mapping references can also serve other owned mapping fields without adding class-name handlers. Numeric effects, skill selection and advancement continue using their existing shared operations.

This is bounded ownership/reference validation, not complete nested mechanical, source or dependency certification. Equipment and race/R.C.C. precedence and source-grounded full import witnesses remain open. Synthetic witnesses do not accept new book content.
