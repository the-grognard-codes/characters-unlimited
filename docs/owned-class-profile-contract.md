# Explicit class profile ownership (22E3)

Packs may opt into `class_profile_format: owned-v1`. Unknown formats, including an explicit null, reject. Existing packs without this field use their unchanged legacy adapter.

Every supported class, including `default_class`, has an explicit entry in `class_profiles`. The format permits1–1000 profiles. Each has exactly the supported fields listed below; omitted fields never inherit the root class. Empty lists/mappings express no declarations where the corresponding mechanical format supports them. The default profile is mandatory. All profiles validate for field ownership, field types and class identity before initial generation, including unselected profiles.

| Fields | Type |
| --- | --- |
| name, path_name | Nonempty text |
| source, pools, required, selection_rules, combat, class_bonuses, resources, advancement, higher_advancement | Mapping |
| physical_grants, fixed_domestic_grants, path_guidance, skill_effects | List |

`class_bonuses.class_id` and `advancement.class_id` must identify their profile's class. Root fields outside this ownership set remain shared catalogs, pack metadata and system rules. Profile fields replace whole fields; there is no recursive merge, implicit grant inheritance or executable callback. Even the formerly default class reads its owned declarations instead of root mechanics. Composition deep-copies results and leaves the pinned archive unchanged.

`profile_composition.py` owns strict shape/whole-field composition; the class adapter supplies its supported field types and checks identity-bearing declarations. No class-name dispatch is added. Class creation, derived views and portable reopening already cross this same adapter. Equipment profiles and core racial/class attributes remain separate existing paths.

The format proves explicit ownership, not complete mechanical acceptance. Nested operation/dependency validation, source review, equipment/race/R.C.C. precedence, importer findings and two source-grounded classes plus a nonhuman proof remain required before full import certification. Synthetic witnesses exercise independent skill allowances, automatic Physical grants and resource/growth totals with poisoned root mechanics; they do not accept new book content.

Mixed mappings such as `combat` currently include catalogs and class choices in one owned field. The plain format replaces that complete mapping; explicit shared mapping fragments are follow-up work to avoid copying those nested catalogs into every imported profile.
