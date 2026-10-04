# Shared option selectors (22B2B)

A selector compiles a pinned game-specific catalog into exact option IDs. It never rolls, grants, saves, calculates bonuses or changes entitlement counts. Group accounting and effect activation remain separate.

## Definition

```json
{
  "any_of": [
    {"categories": ["Communications"]},
    {"tags_any": ["field-tech"]}
  ],
  "exclude_ids": ["radio-satellite"]
}
```

The example is a synthetic framework fixture, not a book rule. `any_of` contains1–100 nonempty clauses. Supported clause fields are `ids`, `categories`, `tags_any`. Each field is a list of up to1000 distinct nonempty strings. Fields within one clause intersect; clauses combine by union; exclusions apply last. Empty field lists match nothing. No implicit match-all or executable expression exists. Matching is exact and case-sensitive; results preserve catalog order.

Unknown fields, malformed values, duplicate/missing referenced IDs, invalid categories/tag metadata, ambiguous group definitions and costs outside the resulting option IDs are rule-data errors. Catalogs contain up to1000 distinct IDs, optional text `category`, optional distinct string-list `tags`. Missing tags/categories match no corresponding criterion. Category/tag criteria can yield an empty result; the remaining allowance remains visible. Full draft review/dependency completeness is subsequent importer work and must not treat an empty referenced catalog as complete automation.

## Adapters

Heroes program choice groups use either existing `skill_ids` or `selector`, never both. Every program choice group compiles and validates against the exact pinned skill catalog before saving, including unselected groups and empty selections. Projected groups expose compiled `skill_ids` to existing builder, grant and editable-PDF consumers, retaining entered selections, source, costs and warnings. Legacy explicit-ID packs and saved records remain unchanged.

Minor power allowance membership compiles the pinned power category through the same selector. Catalog metadata validates before acquisition dice, during receipt validation and when projecting the allowance. No class, race or individual power name controls matching. Other categories retain existing honor-system behavior and do not consume Minor slots.

As in existing workflows, outside-group percentile skills can retain base proficiency with no education bonus; outside-group Physical skills have no automatic Physical grant. Selection credit does not control every form of effect activation. Existing generic `power_bonus_tags` targeting remains in its legacy adapter until the shared effect increment; it is not silently renamed to `tags`.

## Proof and remaining scope

Public character/portable/editable-PDF workflows exercise categories, tags, exclusions, weighted/distinct credit, outside choices, malformed syntax, missing references and no-roll atomic rejection. Both game catalogs remain separate. No accepted rule pack or visual layout changes. Full fixed-grant composition follows22B2C; typed effects, resources/progression, complete mechanical importer and magic/psionic paths remain open.
