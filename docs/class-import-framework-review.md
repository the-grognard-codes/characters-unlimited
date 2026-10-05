# Class-import framework review

> The [player-focused scope amendment](player-focused-scope.md) changes the activation gate: exhaustive combat/activity simulation is optional. Core attribute and skill calculations, selectable content, saves and sheets remain required.

The framework supports adding options through reviewed data for several common mechanics, but it does not yet certify a complete imported class or race. New classes must not require a class-named handler. Unsupported mechanics must remain explicit dependencies until a reusable operation is implemented and verified.

## Current seams

| Responsibility | Shared implementation | Current limit |
| --- | --- | --- |
| Initial racial attributes | Per-attribute pools, caps and citations in `generation.py` | No R.C.C. replacement precedence or complete nonhuman traits yet. |
| Skill entitlements | Weighted selection groups, catalog selectors, fixed grants | Conditional/level entitlements and all prerequisite families remain incomplete. |
| Acquired numeric bonuses | Retained formulas and additive/minimum attribute effects | Generic acquisition scheduling and broader target types remain incomplete. |
| Percentile skill effects | Source-bound selectors and additive projection in `skill_effects.py` | Constant effects only; legacy adapters remain for existing definitions. |
| Resource generation | Shared ordinary formulas, retained attribute snapshots and additional per-level gains | Conditional schedules and generic ability costs remain incomplete. |
| Exact saves | Immutable rule versions, retained rolls, source replay and portable dependencies | Core-generation migrations remain unsupported. |
| Class composition | Data profiles in `class_rules.py` | Legacy overlays remain; owned profiles and explicit shared catalogs isolate field ownership. Complete mechanical import certification remains open. |

## Ownership and composition

Class-owned entitlements and effects must replace another class's fields; truly shared catalogs and system rules may be inherited. This is an explicit semantic distinction, not a rule that every profile should copy the entire pack. The22C2 review caught default-class skill-effect inheritance; nondefault profiles now default that field to an empty list. Existing legacy profiles retain their supported behavior.

Before broad class activation, composition needs a schema that identifies each field's owner and replacement/merge policy. It must validate the complete composed class, including resource definitions, advancement, automatic grants, choice groups, equipment entitlements and referenced ability catalogs. A profile's presence or a selectable identity alone cannot establish completeness.

Races and R.C.C.s need the same treatment: attributes, restrictions, replacements and retained compatible selections must be declarative. Precedence must be specified from book evidence, with a worked case proving that replacement does not silently retain another class's grants or discard the player's compatible choices.

## Import contract still required

A draft mechanical import needs game and edition, stable identities, versioned source evidence/fingerprints, referenced catalogs, grants, choices, typed operations, acquisition/progression timing and review findings. Validation must inspect declarations that are not currently selected as well as selected ones. Missing explicit references and unsupported operations must produce actionable findings. Category/tag selectors that match no options can be valid expressions; they do not prove the source catalog is complete.

Activation requires reviewed evidence and independently calculated characters, not just successful parsing. Ticket22's proof still requires two distinct source-grounded classes and a nonhuman/R.C.C. path to work by changing definitions rather than product code. Synthetic fixtures prove the engine contract; they do not satisfy that book-content acceptance gate.

The same selectors, grants, formulas, numeric effects and exact dependency pins should serve mutant powers, psionics and magic. Game-specific eligibility belongs in definitions and adapters. Ability selection, costs, ranges, durations, save targets and conditional activation still need a shared contract and representative end-to-end paths before those families can be called complete.

This review is an interim framework assessment. It does not replace the original ticket plan, full-corpus release gate or final retrospective.

## Explicit ownership follow-through (22E3)

The opt-in `owned-v1` class format now requires every supported class, including the default, to declare its complete supported field ownership. Shared root catalogs remain single definitions; all class-owned fields replace whole fields and all profile shapes/owners validate before initial dice. Legacy accepted profiles remain unchanged. See `owned-class-profile-contract.md`. This closes implicit default inheritance for the new format; nested mechanical/dependency validation, equipment and race/R.C.C. precedence and source-grounded certification remain open.

## Shared nested catalog follow-through (22E4)

Owned mapping fields can now explicitly reference one source-bound catalog and supply disjoint class keys. The same resolver validates all references before generation; catalog-owned keys cannot be overwritten. See `shared-profile-catalog-contract.md`. This avoids duplicating common combat catalogs across classes; nested mechanical/source certification and other composition families remain open.

## Common ability follow-through (22F1/22F2)

Ability parameters and current-state requirement guidance now use shared source-bound projectors. Heroes powers consume them without ability/class identity dispatch; synthetic spell/psychic catalogs exercise the same requirement boundary. Exact pins, all unselected dependency preflight, effective attributes, distinct option counts and honor-system retention are covered. These seams do not yet provide a generic ability acquisition/effect lifecycle: the current mutant adapter still acquires its established attribute/resource formula families. Initial-only timing, conditional activation, complete class imports and source-grounded magic/psionic adapters remain open.

22F3 shares ordinary first acquisition, whole-catalog formula preflight and inactive/reselection cache replay between Physical skills and mutant powers. Existing source/UUID/history/effect adapters remain authoritative. This closes duplicate retained-dice lifecycle logic; generic ability effect activation, learned-level timing and complete importer certification remain open.

## Supported nested component follow-through (22E5)

Every resolved owned profile now preflights supported starting resources, pool/category cost declarations, fixed/required/typed-effect references, Physical targets/acquisition formulas, default combat identity and XP/HP/resource growth before generation. Shared catalog resolution occurs first; class/component errors identify the affected declaration. See `owned-profile-component-preflight-contract.md`. This is supported-component coverage, not complete mechanical/source certification: full proficiency/conditional combat schemas, unavailable legacy allow/exclusion catalog content, unreferenced fragments, equipment/RCC precedence and source-grounded activation remain open.

22C3 adds shared source-bound additive numeric contributions for class saving/perception and mutant named saving bonuses, with distinct identities, collision-safe explanations, exact pins and safe-total persistence guards. Owned class declarations preflight before dice. See `shared-numeric-contribution-contract.md`; conditional effects and complete importer certification remain open.

## Archive acceptance boundary

`RuleArchive` verifies identities, immutable canonical bytes and manifest fingerprints; it does not certify full mechanical/source completeness. Runtime component preflights are shared validators, not a completed maintainer conversion/activation report. The future activation workflow must aggregate those validators with catalog completeness, source review and independently calculated class/nonhuman witnesses before declaring a new import complete.

User cleanup on2026-10-05: general insanity projections/automatic HU sheet fields are removed. Source-specific Crazy traits/permanent injuries remain in scope. HU Mega Heroes and super-vehicle/base design are excluded; robot/bionic construction remains required. Existing optional combat/activity work is compatible legacy support, not a further implementation or release gate. Refer to `player-focused-scope.md`.

## Next core creation batch after 22F4

22F4 is merged. Ordinary descriptive abilities now share validated retained acquisitions, sources, optional parameters, skill effects and numeric additions without artificial attribute changes. New content does not require a handler named after its ability.

The next import batch should prove a complete required creation path through the existing data seams, rather than add further maneuver operations. Required gaps are class-owned equipment composition, race/R.C.C. replacement and compatible choices, and game-specific ability allowances/catalog references. Heroes category composition must use the same ownership principle as Rifts profiles; its current Mutant-specific pack boundaries are not a complete category importer. Character attributes, skill entitlements and percentages, choice persistence and editable export must be demonstrated with source-grounded examples. Existing validators should be aggregated into a maintainer import report; parsing alone cannot certify book coverage.

Optional attack variants, situational activation resolution, movement rates and fatigue do not block this batch. Describe significant effects and reasonable interpretations in source-bound guidance. Robot/bionic components and their resulting attributes, skills and costs remain required. Keep the original plan as the retrospective baseline and assess changed scope through player-focused-scope.md.

22G closes class-owned equipment composition for the existing Rifts entitlement formats, including explicit empty grants and shared catalogs. All resolved owners preflight before creation dice. It preserves existing archives and does not certify wider book content. See `owned-equipment-import-contract.md` and `evidence/22g-owned-equipment-validation.md`. Race/R.C.C. ownership, HU category composition and a combined maintainer activation report remain the next creation seams.
