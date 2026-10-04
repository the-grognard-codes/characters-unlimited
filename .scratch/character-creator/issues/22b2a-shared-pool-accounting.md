# 22B2A: Shared entered-selection pool accounting

**Status:** in-progress. **Base:** ec893471c9296ce75e52a1114fc4a2815feb3111 (merged22B1/PR90).

Extend shared groups with an explicit `counting` policy: `distinct` (existing default) or `entries`. Each-entry pools debit all entered known options, including duplicates and choices that carry honor-system eligibility warnings. Effects and proficiency still occur according to their existing separate eligibility/stacking rules. Neither counting policy controls grants.

Adapt current Rifts optional skill pools and Heroes Secondary allowances to the entries policy, preserving selected rows, weighted costs, per-pool bonuses, specialty normalization, source guidance and learning levels. Existing supported catalogs compile into exact option IDs. Validate all declared counts/costs/references before persistence rather than validating only the selected cost. No class/race-ID dispatch, accepted pack revision, save migration or visual change.

Verify through agreed CharacterApplication and portable seams: malformed source costs/counts reject atomically; source-grounded duplicate/ineligible/weighted choices retain current credit and effects; history and explicit rule updates remain compatible. Shared category/tag selectors and full fixed-grant composition follow as22B2B, not implied by this accounting increment.
