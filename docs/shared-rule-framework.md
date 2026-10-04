# Shared rules framework and class/race imports

This review follows the user's 2026-10-04 instruction to prioritize common mechanics and avoid bespoke class/race implementations. The full requirements in `character-creator-ticket-plan.md` remain in force. Framework completion must precede large content batches; an imported heading is not an automated option.

## Current audit

| Area | Reusable implementation already present | Remaining coupling or gap |
| --- | --- | --- |
| Sources and versions | Immutable `RuleArchive`, exact portable pins, source references, provisional coverage inventory | There is no complete mechanical draft-to-accepted import workflow. Hash acceptance alone does not validate every mechanic or dependency. |
| Classes | `class_rules` overlays declarative profiles for required skills, pools, bonuses, resources and progression; equipment profiles overlay starting grants | Default-class fallback and separate pack layouts must become explicit composition. Do not add branches on a new class ID. |
| Races | Shared generation and replay, caps and exceptional rules | Current race definitions have one common attribute formula. Per-attribute and R.C.C. replacement rules still need a reviewed contract. |
| Skills | Required choice groups, weighted pools, percentile checks, synergies and shared Physical acquisitions | Rifts and Heroes selection adapters use different records; generalized grants and entitlements are incomplete. |
| Mutant powers | Retained acquisitions, additive/floor effects, skill/saving bonuses, resources and advancement gains | Power shapes and Human Mutant applicability are still restricted; other power categories are not implemented. |
| Magic and psionics | Source/version infrastructure and the resource model provide foundations | Spell/psychic catalogs, acquisition grants, eligibility, P.P.E./I.S.P. formulas and conditional projections are not implemented. |
| Progression | Retained dice, learned age, intermediate levels and undo/replay | Game/path-specific progression adapters need common grants and acquisition scheduling. |

`class_rules` is already data-driven for its supported mechanics. The problem is incomplete shared mechanics and composition, rather than a need to write a Python class for each O.C.C. Existing Human Mutant guards honestly restrict reviewed coverage; removing them alone would falsely advertise support.

## Import contract to build

A class, race or R.C.C. supplies a reviewed definition with an identity, game/edition, version, exact source evidence and references to shared definitions. It composes these pieces:

- Generation: ordinary or per-attribute pools, exceptional rules, ceilings and a declared precedence for racial-class replacements.
- Grants: referenced skills, powers, spells, psionics, resources, equipment or capabilities; an explicit acquisition time and learned level.
- Choice groups: allowed categories/tags or explicit referenced options, quantity or weighted cost, prerequisites, exclusions and growth by level.
- Effects: typed operations such as numeric addition, a minimum attribute target, a conditional bonus, a named proficiency adjustment or a resource contribution. Each contribution retains its source and acquisition identity.
- Progression: referenced XP schedule, level awards, retained roll timing and replacement rules. Removal, undo and reselection reuse acquired dice rather than rerolling them.
- Unresolved dependencies and automation gaps: explicit records that keep an option incomplete instead of silently inventing missing rules.

The imported definition cannot contain executable expressions, Python, callbacks, or a handler named after an individual class/race. A genuinely new mechanic adds one shared operation with public-workflow verification, after which every applicable option references that operation. Game separation remains explicit even when implementations are shared.

This is the design contract for upcoming increments, not a claim that the complete schema or importer exists today. Do not publish speculative accepted packs against it before its operations and validators are implemented.

## Processing and review

```text
Book Markdown/PDF evidence
  -> provisional candidate with source fingerprints
  -> reviewed draft definition and dependency references
  -> schema, operation and dependency validation
  -> independently checked worked character examples
  -> explicit accepted version
  -> class/race composition
  -> shared selection, acquisition, effects and progression
  -> builder and editable PDF projections
```

Unknown operations and missing definitions must produce actionable findings. They must never be ignored or counted as complete. Honor-system selection warnings permit player choices; they do not permit malformed rule data. Existing saves stay on their exact versions, and explicit corrections require previews and receipt/history compatibility checks.

## Implemented increment: recorded bonus formulas (22A)

`recorded_formulas.py` now implements ordinary numeric bonus acquisition and replay for class attribute additions, Physical-skill effects and chosen mutant powers. It has no class/race/power-name dispatch. Definition validation, die-face validation, arithmetic and range checks live in one place.

The formula contains integer `count` (0–1000), integer `sides` (0–1000, positive when dice are drawn), optional integer `constant` (default 0), and optional positive integer `multiplier` (default 1). No other fields are permitted. Constant, multiplier and final result stay within the supported safe whole-number range. Calculation is `(sum(recorded dice) + constant) * multiplier`; the multiplier applies to the complete ordinary formula, not just its dice.

Legacy Physical definitions retain `bonus` as their constant field; the adapter translates it and accepts optional `multiplier`. Power definitions retain their attribute target metadata, which the adapter separates from the numeric formula. Class definitions directly use the shared shape. Existing pack files, source records, receipt IDs and saved data formats are unchanged.

These are bonus dice, so reroll-ones, extra-die/drop-lowest and exceptional-attribute rules do not apply. Initial racial generation remains in `generation.py`. The existing floor/additive precedence, resource snapshot timing, manual fixed values and adjustments are also preserved. A formula does not decide its target, stacking, eligibility or acquisition timing; those belong to the next shared increments.

The regression fixtures use synthetic multiplier definitions to test the import contract; they are not new book rulings or published content. Existing source-grounded tests verify actual class, skill and power behavior, including retained resource dice and advancement.

## Implemented selection increment (22B1)

`selection_groups.py` now shares distinct weighted choice accounting across required select groups, scholastic program groups and Minor power allowances. It validates counts, costs and references, and reports duplicate/outside/unresolved credit without granting effects. Referenced identities remain exact; free-text specialties keep their existing normalization. Recorded outcome-count dice also reuse22A formulas. Legacy adapters preserve their warning, grant and active-power behavior. 22B2A adds explicit entry-count policy for Rifts optional pools and Heroes Secondary selections, retaining their separate grant/bonus rules and validating all declared costs before save. Details and remaining limitations are in `shared-selection-group-contract.md`.

## Next dependency-ordered increments

| Slice | Deliverable | Reuse proof |
| --- | --- | --- |
| 22B | Shared grants and selection groups; adapt current Rifts pools, Heroes education and mutant budgets | The same selection engine handles fixed grants, categories, weighted costs, duplicate identities, prerequisites and honor-system warnings without class-ID branches. |
| 22C | Shared effect operations and retained acquisitions; adapt existing Physical and super-ability effects | Attribute additions/floors, skill and saving bonuses and resource contributions use typed operations with stable identities and source explanations. |
| 22D | Resource and progression composition | P.P.E./I.S.P./HP/S.D.C. and level grants compose from definitions; generate once, retain on backtracking, validate history and preview corrections. |
| 22E | Mechanical importer and class/race composition | Validate draft operations/dependencies before activation; import two distinct source-grounded classes and a nonhuman/R.C.C. path by changing rule data only. |
| 10A/11A | Representative magic and psionics paths using those shared operations | Select spells/psychic abilities, display costs, save targets, ranges, durations and conditional effects; keep game-specific eligibility in data. |
| Content batches | Remaining reviewed classes, races, powers and abilities | Add data and worked examples. A new mechanic may extend the framework; a new option using supported mechanics requires no product-code edits. |

Conditional combat work from 19B4 is preserved separately on its original branch in a scoped Git stash. It is deferred behind this framework direction and will be integrated using the shared operations where appropriate. No final retrospective or full-coverage claim is made by this increment.
