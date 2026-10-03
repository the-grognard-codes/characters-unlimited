# Skill proficiency record contract

Accepted packs are reviewed declarative JSON, fingerprinted by `packs/accepted.json`. Source text is evidence, never executed. Older definitions remain immutable and selected characters retain exact version pins; adding or correcting skill mechanics requires a new pack plus an explicit update preview.

A percentile skill has `id`, `name`, `category`, `base`, `per_level` and `source` (`book`, printed `pages`, `section`). Primary proficiency sums source base, acquired-level progression, eligible class bonus, I.Q., repetition and named synergies, then caps at 98%. Selection rules and prerequisites provide honor-system guidance rather than deleting choices.

`additional_checks` is an ordered list with unique names. An ordinary check provides `name` and `base`; it reuses the same contributions with that base, and caps independently at 98%. A contextual check provides `name` and `context_of`, naming `primary` or a previously declared check, plus an optional numeric `multiplier` (default 1) and `modifier` (default 0). It transforms the referenced normal, capped proficiency: `normal × multiplier + modifier`. A context is a separate result, not a universal penalty. Its progression rate inherits the referenced rate times the multiplier. No general expression interpreter or executable rule prose is supported.

For example, Medical Doctor has a 60% diagnostic primary check and 50% Treatment check. Animal treatment references Treatment with -35. Animal Husbandry wild-animal care references its normal proficiency with a 0.5 multiplier; a normal 98% yields 49%, not half of an uncapped intermediate. Fractional results are displayed without inventing a rounding convention; on integer percentile dice a fractional threshold has the same successful integers as its floor. Negative contextual results remain visible as an impossible normal percentile check, rather than silently inventing a minimum chance.

The projection returns each check's percentage, uncapped percentage, contribution breakdown and per-level rate; contexts additionally identify their normal reference, normal percentage and multiplier. The UI, upgrade preview, portable definition validation and editable PDF consume this shared projection. Authors must source-verify parameters, references, order, cap/penalty interpretation and prerequisites, add public workflow evidence for meaningful boundaries, and retain unsupported combinations in explicit findings. This limited contract does not claim a complete ingestion schema for all RPG mechanics.
## Heroes program choice groups

Reviewed program definitions may declare `choice_groups`: each group has a stable `id`, player-facing `name`, required `count`, explicit eligible `skill_ids` and source evidence. Saved program selections keep `slot` and `program`; only programs with declared groups may additionally store `choices`, a map from group ID to a list of reviewed skill IDs. Missing groups remain incomplete without altering the saved record. Unknown groups/skills and malformed values are rejected; known outside-group choices remain retainable with guidance.

```json
{"slot":0,"program":"computer","choices":{"repair-radio":["radio-basic"]}}
```

Projection reports each group's entered count, distinct eligible credited count and remaining requirement. Duplicates and outside-group choices do not fill another distinct choice; negative remaining values identify excess eligible choices. Qualifying first-program choices use the slot bonus once; outside-group choices add no group education bonus. Shared skill grants use the highest eligible program bonus once with I.Q. once. Secondary selections add no education bonus. Repeated-program category entitlements require separate source definitions; a retained first-program group on a repeat does not certify those entitlements or add a new group education bonus.

Old two-field selections and accepted pack bytes are preserved. New program catalogs require explicit version updates for pinned characters. Computer Repair uses `primary_check_name` for the procedure and `additional_checks` for the separate actual roll; source-defined contextual checks use the shared proficiency contract above.

Heroes skills reuse declarative `synergies` from the shared percentile contract: a selected source skill adds its named amount once before the 98% cap. Shared or duplicate selections do not stack it. Choice groups may list `unresolved_skill_ids` and `guidance`; such selections remain saved but receive no entitlement credit until interpretation is accepted. Their existing fixed grants remain intact. This is source-specific uncertainty guidance, not a manual override marker.

Heroes Secondary projection expands the reviewed `selection_costs` into an effective map for every catalog skill. Skill IDs omitted from the pack cost one; each retained list entry consumes its cost, including duplicates and honor-system exceptions. The picker and saved list display costs from this map; they do not infer cost from the skill name. Allowance minus total cost may be negative and does not delete saved work. First Aid costs one and Holistic Medicine costs two under program rules 1.6.0.

## Recorded Rifts Physical bonuses

Definitions with `kind: "physical"` omit percentile base/rate. `attributes` and `resources` map named effects to reviewed `{count, sides, bonus}` formulas; fixed effects use count/sides zero. `combat` maps explicit ordinary combat statistics to fixed bonuses. This bounded contract currently supports Athletics, Body Building, Physical Labor, Running and Boxing; other Physical and combat contexts remain pending.

Saved `physical_acquisitions` maps each acquired skill ID to `rolls`, keyed by `attribute:SPD` or `resource:SDC` for random effects. First acquisition rolls each formula once without racial house rules. Removal keeps the acquisition but removes active effects; reselection and duplicates reuse it. Attribute records carry source-bound `physical:<skill-id>` modifiers alongside class modifiers. Fixed manual values remain authoritative. Portable validation checks dice, active modifiers and any historical modifiers against the exact pinned definition; historical absence is valid before acquisition.

Projection reports each unique skill's effects and dice, separate resource bonus rows and ordinary combat contributions. It never rolls. The UI and PDF consume these values without inventing percentages or resource baselines. Athletics dodge is excluded from gunfire/energy defense under the reviewed p. 361 rule. Compatible explicit catalog updates preserve acquisitions and historical records; changes to acquired Physical definitions are rejected pending a dedicated migration.

## Starting Rifts resources and fixed class bonuses

Rifts skills 2.1.0 adds `resources.definitions`, each naming an ID, label and ordered source-bound contributions. A contribution has either a standard `{count, sides, bonus}` formula or a captured attribute. Generate all starting resources once through the revisioned character action after selecting attributes. Saved resource records contain contribution IDs, values, dice and sources, plus `adjustment` and `fixed`; `resource_attribute_snapshot` retains the captured P.E. record. User interpretation accepted 2026-10-03: HP uses effective P.E. when first generated and preserves that starting contribution afterward.

S.D.C. sums its recorded general/class values and active Physical bonuses. HP sums captured P.E. and its level-one D6. Manual fixed values replace the displayed capacity; additive values follow calculated contributions. Absent generation leaves resource totals absent. Portable validation checks exact rule provenance, source dice/formulas and captured attribute records. Compatible updates preserve them; changed generated definitions require a separate migration. Source locators and the agreed interpretation remain in the new pack; older accepted bytes stay immutable.

`class_bonuses` names its class ID, fixed saving contributions, Perception contribution and source. Savings combine applicable attribute and class contributions; Perception reports only the O.C.C. contribution until other modifiers are implemented. This contract is level-one capacity calculation, not live damage tracking or a complete generic effect/schema system.
## Physical endurance activities

Rifts skills 2.2.0 adds Physical Labor and Running through the recorded Physical acquisition contract. Running's `activities.running` rule declares half-speed miles/km per effective P.E. and the maximum-speed distance divisor. Projection produces named half/maximum-speed activity records with current speed attribute and distances. It does not invent elapsed time or universal movement conversion. Nonpositive or unrepresentable manual attributes remain saved; activity numbers are absent with guidance.

Activities are derived rather than saved acquisitions. Explicit numerical updates show separate speed, mile and kilometer rows in the reviewed preview and preserve source dice. Their values appear in builder explanations and editable PDF notes. Running is eligible Secondary under the original p. 300 list; Physical Labor is an eligible Related choice and remains a retained exception in Secondary.

Boxing uses the fixed Physical `combat.attacks` contribution, added once to the selected hand-to-hand attacks per melee. Its natural-20 knockout condition is retained in source notes; encounter durations are not rolled during acquisition. Physical notes also appear in editable PDF continuation fields.

## Physical skills with percentile checks

Skills2.4.0 adds Swimming as kindPhysical with base/per_level and separate conditional checks. Physical definitions without base retain their effect-only projection; those with base add ordinary proficiency contributions and any additional checks. Recorded empty acquisitions consume no dice; duplicates do not add proficiency/effects. Comparisons include both Physical activities and percentage/check rows.

`activities.swimming` declares yards/meters per effectiveP.S. and minutes per effectiveP.E. The source coefficients are3/3/1. Limits are absent for nonpositive attributes or results outside browser-safe integer representation. UI and PDF show these units independently from Running's mile/km records. Storm and non-powered MDC armor checks are conditional examples; afloat/buoyancy and combined armor/context adjudication remain visible rather than automatically resolved.
