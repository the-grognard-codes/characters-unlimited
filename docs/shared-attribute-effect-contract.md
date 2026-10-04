# Shared typed attribute effects (22C1)

Class, Physical-skill and mutant-power attribute modifiers share numeric addition and minimum-target evaluation. There is no dispatch on a class, race or power name. A minimum preserves a higher calculated attribute; additions are summed first, then all minima apply. Existing caps apply next, then manual adjustments. A fixed player value remains authoritative.

## Data contract

A class may retain legacy `attribute_bonuses` or declare `attribute_effects`, keyed by one of IQ, ME, MA, PS, PP, PE, PB, SPD. A target cannot appear in both maps. Each typed effect has exactly `operation`, `formula`, and `source`: operation is `add` or `minimum`; formula uses the shared recorded formula contract; source is a source object with a nonempty text `book` citation. For example, a synthetic minimum definition is:

```json
{"MA":{"operation":"minimum","formula":{"count":1,"sides":6,"constant":24},"source":{"book":"Synthetic fixture","section":"Framework contract"}}}
```

This example is not an accepted book rule. Each class target currently has one contribution. Multiple contributions and broader target types remain future work.

Definitions validate before initial generation dice. Bonus dice do not use racial house options. Receipts retain operation, raw dice, derived value and exact source. Attribute rerolls retain those receipts. Portable current records, roll history and initial resource snapshots replay against exact pinned definitions; changing the operation or source cannot manufacture a different effect. Starting HP retains effective P.E. at its original generation.

Legacy definitions and receipts retain their existing shapes and source pins. The adapter translates legacy power-floor receipts into minimum operations for evaluation; it does not migrate accepted packs. New typed class receipts add an operation field. The builder labels a minimum as a target floor rather than an additive bonus, and the editable PDF projects the resulting attribute.

The numeric evaluator does not own eligibility, grants, acquisition timing or source certification. Existing family adapters own those decisions. This slice does not claim generic skill/save/resource effects, complete magic/psionics, a complete mechanical importer, or new reviewed class coverage.
