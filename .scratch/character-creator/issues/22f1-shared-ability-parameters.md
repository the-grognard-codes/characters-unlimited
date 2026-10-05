#22F1: Shared source-bound ability parameter projection

**Status:** DONE. **Review base:**5dee95d1dbb2332e2b3cded2070e4ad9ff44c412 (PR102).

Introduce data-defined ability parameters shared by mutant powers and future magic/psionic adapters: stable parameter identities/display names, either nonempty literal guidance or integer base/per-level quantities with explicit units, plus book/section citations. Project from current level with exact-integer/nonnegative range checks; no expression evaluation or option-name handlers. Costs/ranges/durations/save targets can use the same parameter shape; this increment displays them and does not spend resources, activate conditional effects or certify spell/psionic eligibility.

Wire optional parameters through existing Heroes power catalog/active/inactive views, selection preflight, portable exact-pin validation and both browser/PDF explanations. Validate all declarations before new power dice, even unselected powers. Legacy definitions unchanged; new synthetic fixtures test scaling, literal conditions, overflow, malformed inactive metadata, exact reopening and editable PDF values/source evidence. Independent source-grounded metadata acceptance is separate: original HU PDF page308 provides Sense Evil ISP2/radius140feet/duration2minutes perlevel/no save; Rifts original is image-only and requires rendered source checking. The native HU full-scan helper hit a later malformed CMap, so it is not claimed as complete source validation.

Merged in PR103 as563bcee20757dd9f9332b4e21424d8e1af4cc0e4 after both exact-head Windows37246351844/37246382013 passed, including frozen executable validation.
