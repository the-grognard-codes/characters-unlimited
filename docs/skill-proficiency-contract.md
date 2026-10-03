# Skill proficiency record contract

Accepted packs are reviewed declarative JSON, fingerprinted by `packs/accepted.json`. Source text is evidence, never executed. Older definitions remain immutable and selected characters retain exact version pins; adding or correcting skill mechanics requires a new pack plus an explicit update preview.

A skill has `id`, `name`, `category`, `base`, `per_level` and `source` (`book`, printed `pages`, `section`). Primary proficiency sums source base, acquired-level progression, eligible class bonus, I.Q., repetition and named synergies, then caps at 98%. Selection rules and prerequisites provide honor-system guidance rather than deleting choices.

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
