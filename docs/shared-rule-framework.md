# Shared rules framework and class/race imports

This review follows the user's 2026-10-04 instruction to prioritize common mechanics and avoid bespoke class/race implementations. The full requirements in `character-creator-ticket-plan.md` remain in force. Framework completion must precede large content batches; an imported heading is not an automated option.

## Current audit

| Area | Reusable implementation already present | Remaining coupling or gap |
| --- | --- | --- |
| Sources and versions | Immutable `RuleArchive`, exact portable pins, source references, provisional coverage inventory | There is no complete mechanical draft-to-accepted import workflow. Hash acceptance alone does not validate every mechanic or dependency. |
| Classes | Legacy profiles plus explicit `owned-v1` fields and source-bound shared catalog references | Complete nested mechanical/dependency certification, equipment ownership and race/R.C.C. precedence remain open. Do not add branches on a new class ID. |
| Races | Shared uniform/per-attribute generation and replay, caps, exceptional rules and race/per-attribute source citations | R.C.C. replacement precedence and complete nonhuman traits still need reviewed composition. |
| Skills | Shared selectors, fixed grants, weighted groups, percentile effects/checks and retained Physical acquisitions | Rifts and Heroes selection adapters use different records; conditional/level grants and complete entitlements remain incomplete. |
| Mutant powers | Shared ordinary acquisitions, parameters and current-state requirements; retained additive/floor effects, skill/saving bonuses, resources and advancement gains | The current effect adapter and Human Mutant applicability are still restricted; other power categories are not implemented. |
| Magic and psionics | Shared source/version, selector, formula/cache, parameter, requirement and resource foundations | Complete game adapters, catalogs, grants, learned-level timing, source-specific P.P.E./I.S.P. and conditional effects remain open. |
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

## Catalog selector increment (22B2B)

`option_selectors.py` compiles exact category/tag/identity criteria and exclusions for program groups and Minor power allowances. Details are in `shared-option-selector-contract.md`. It does not grant effects or certify missing catalog dependencies; shared grants remain22B2C work.

## Typed attribute increment (22C1)

`effect_operations.py` shares addition/minimum evaluation for class, Physical and power attributes. Classes may declare typed formula/source effects without class-specific handlers. Exact receipt replay, manual ordering and retained resource snapshots remain enforced. See `shared-attribute-effect-contract.md`; broader grants, targets, acquisitions and importer validation remain open.

## Fixed-grant increment (22B2C)

`grants.py` resolves exact identities and catalog selectors once per granted identity. Existing Rifts/Heroes Physical acquisitions and Heroes fixed program skills use it; compiled program IDs preserve the existing UI/PDF contract. All unselected program grants also validate before mutation. See `shared-fixed-grant-contract.md`. This is identity resolution, not complete conditional/level entitlements or generic acquisition scheduling.

## Starting-resource formula increment (22D1)

Starting-resource formula terms now use the same ordinary acquisition/replay engine as class, Physical and power bonuses. Legacy bonus fields adapt to shared constants and optional whole-formula multipliers; known effective attribute snapshots remain retained. See `shared-resource-formula-contract.md`. Generic level scheduling, nonlinear terms and complete magic/psionic acquisition remain open.

## Per-attribute racial increment (22E1)

`generation.py` resolves complete per-attribute replacement pools, optional defaults and caps without race handlers. Every definition validates before initial dice; whole-profile house preflight preserves single-target rerolls. See `per-attribute-racial-pool-contract.md`. This is a generation seam, not acceptance of a complete nonhuman/R.C.C. path; source composition and other traits remain open.

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

## Racial citation increment (22E2)

Racial generation resolves a declared race source and optional per-attribute citations with legacy core fallback. Rerolls and portable current/history/resource snapshots use the same pinned resolver. Every declared citation validates before initial dice. See `racial-attribute-source-contract.md`. Core migrations, R.C.C. composition and full importer certification remain open.

## Percentile skill-effect increment (22C2)

`skill_effects.py` compiles source-bound additive percentile effects through the shared selector engine. Rifts class skill projections, Heroes program packs and active mutant powers use the same targets and numeric projection, retaining detailed source contributions and existing caps/contextual checks. Effects grant no skills. See `shared-skill-effect-contract.md`; conditional/level effects and generic magic/psionic activation remain open.

## Retained level-resource increment (22D2)

`level_resource_gains.py` shares additional per-level formula acquisition and exact replay across both games. Generated resource identities receive retained, source-bound contributions; inactive caches do not affect totals. Nondefault classes own their extra growth declarations. See `shared-level-resource-gain-contract.md`; ordinary HP growth and legacy class fallback remain unchanged. Conditional schedules, ability grants, full importer certification and magic/psionic content remain open.

## Explicit profile ownership increment (22E3)

The opt-in `owned-v1` format composes class fields through `profile_composition.py`, preserving shared catalogs while eliminating default-class field inheritance. All profile shapes and declared class owners validate before initial dice. See `owned-class-profile-contract.md`; legacy archives are unchanged and full mechanical import certification remains open.

## Shared profile catalog increment (22E4)

Owned mapping fields resolve explicit, source-bound common catalog references with disjoint class keys. Every catalog/reference validates before dice; no recursive merge or class handlers are introduced. See `shared-profile-catalog-contract.md`. Source-grounded imports and nested mechanical validation remain open.

## Common ability parameter increment (22F1)

`ability_parameters.py` projects source-bound literal guidance or exact whole-number base/per-level quantities independently of game or ability names. Heroes power selection preflights all declarations, and active/inactive builder/PDF views and portable validation derive current-level values from exact pins. Costs are displayed; spending, conditional activation and complete magic/psionic eligibility/catalogs remain open. See `shared-ability-parameter-contract.md`.

22F2 adds a common source-bound requirement compiler/projector for level, effective attribute minima and distinct catalog-selected prerequisites. Heroes powers use cited current-state honor-system guidance without discarding choices/effects; every unselected declaration preflights. Full magic/psionic adapters, activation, timing and source-reviewed catalogs remain open. See `shared-ability-requirement-contract.md`.

22F3 consolidates whole-catalog formula validation, exact inactive cache replay, first acquisition and reselection in `retained_acquisitions.py`. Both shared Physical skills and mutant powers consume it while preserving their legacy receipt/source/history formats. Generic effects, schedules and source-grounded psychic/magic paths remain open. See `shared-retained-acquisition-contract.md`.

22E5 preflights supported nested resources, pool/category costs, fixed/required/Physical grants and effects, default combat references and progression/resource dependencies for every resolved owned profile before generation. Legacy overlays remain compatible; complete proficiency/conditional combat, unreferenced fragment mechanics, equipment/race/RCC precedence and source-grounded importer certification remain open. See `owned-profile-component-preflight-contract.md`.

22C3 adds shared source-bound additive numeric contributions for class saving/perception and mutant named saving bonuses, with distinct identities, collision-safe explanations, exact pins and safe-total persistence guards. Owned class declarations preflight before dice. See `shared-numeric-contribution-contract.md`; conditional effects and complete importer certification remain open.
