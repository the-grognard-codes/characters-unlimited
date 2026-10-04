# Class-import framework review

The framework supports adding options through reviewed data for several common mechanics, but it does not yet certify a complete imported class or race. New classes must not require a class-named handler. Unsupported mechanics must remain explicit dependencies until a reusable operation is implemented and verified.

## Current seams

| Responsibility | Shared implementation | Current limit |
| --- | --- | --- |
| Initial racial attributes | Per-attribute pools, caps and citations in `generation.py` | No R.C.C. replacement precedence or complete nonhuman traits yet. |
| Skill entitlements | Weighted selection groups, catalog selectors, fixed grants | Conditional/level entitlements and all prerequisite families remain incomplete. |
| Acquired numeric bonuses | Retained formulas and additive/minimum attribute effects | Generic acquisition scheduling and broader target types remain incomplete. |
| Percentile skill effects | Source-bound selectors and additive projection in `skill_effects.py` | Constant effects only; legacy adapters remain for existing definitions. |
| Resource generation | Shared ordinary formulas and retained attribute snapshots | Full resource/progression composition and generic ability costs remain incomplete. |
| Exact saves | Immutable rule versions, retained rolls, source replay and portable dependencies | Core-generation migrations remain unsupported. |
| Class composition | Data profiles in `class_rules.py` | Profiles are overlays, not a certified mechanical import schema. |

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
