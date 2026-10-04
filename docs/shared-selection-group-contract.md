# Shared selection groups (22B1)

This increment implements the first selection portion of `shared-rule-framework.md`. It composes existing rule data; it introduces no class/race-specific handlers, new published options or accepted pack revisions.

## Shared interface

`selection_groups.py` validates and projects distinct, weighted selection groups. A normalized group contains:

- `count`: whole-number allowance from0 through1000.
- `option_ids`: up to1000 distinct nonempty referenced identities, compiled by the game/family adapter from its reviewed catalog.
- Optional `costs`: a mapping of those identities to whole-number costs from1 through100. Unspecified costs are1.
- Optional `unresolved`: distinct group identities whose selection credit remains uncertified.

Unknown normalized fields, invalid counts/costs, duplicate option definitions, and cost/unresolved references outside the group are rule-data errors. Selections remain entered data. Distinct eligible identities count once; outside-group and unresolved choices earn no group credit. Uncertified repeat entitlements earn no credit. The projection returns eligible identities, credited weight, remaining allowance, duplicate/outside/unresolved indicators. It never rolls, saves, grants an ability, or decides class eligibility.

## Current adapters

| Adapter | Composition | Preserved behavior |
| --- | --- | --- |
| Rifts required select groups | Referenced option definitions and optional `selection_costs` normalize to the shared group | Duplicate choices give one grant; excess choices remain saved. Text-language specialty normalization and exclusion remain in their existing adapter. |
| Heroes scholastic program groups | `skill_ids`, costs and pending fixed-grant credit normalize to the shared group; referenced skills must exist in the pinned catalog | Outside-group choices remain recorded without new group effects; repeated/pending choices do not certify new automatic grants. Existing warning text and group projections remain compatible. |
| Heroes minor super-ability allowance | The adapter compiles the pinned `minor` category into explicit identities and uses the recorded outcome's count | Other categories cannot consume a Minor slot. Directly selected reviewed powers still apply on the honor system, including choices beyond their starting allowance; budget warnings are nonblocking. Other categories' full entitlements remain unfinished. |
| Heroes recorded outcome counts | Base and attained count use the shared allowance validator; ordinary count dice use22A recorded formulas | Invalid source counts reject before saving an outcome. Existing dice/history shapes, draw order and exact version pins remain unchanged. |

The UI and editable-PDF adapters continue to consume the existing remaining/credited values. No presentation or layout change is included. The synthetic required-group weights and catalog-category fixtures test the framework contract; they are not book rulings or shipped content changes.

## Verification and next work

Public `CharacterApplication` and portable-save tests cover weighted required groups, duplicates/excess, category accounting and atomic rejection of malformed program costs and outcome counts. Existing source-grounded group, Physical, program, power, HTTP and editable-PDF tests protect current behavior.

Generalized category/tag criteria, prerequisite composition, automatic grants and specialty identity across all skill pools are22B2 work. Shared typed effects, resource/progression composition, a complete reviewed mechanical importer, and magic/psionic paths remain subsequent increments. No source-extraction candidate becomes an accepted class merely because this framework can count its choices.
