# Paid training within an initial skill minimum

05D28 is implemented with inactive candidates on `codex/rifts-city-rat-initial-training`; the accepted defaults are unchanged. Both independent preliminary reviews approve this source/contract scope. Shared/source implementation and final artifact reviews remain acceptance gates; current results are in evidence/05d28-initial-training-validation.md.

## Source and expected behavior

Original Rifts Ultimate Edition printed88 requires ten City Rat Related skills, at least three Physical/Rogue. Expert costs one Related slot; Martial Arts/evil Assassin cost two. Printed316 includes Hand to Hand among Physical skills chosen once. A paid style therefore contributes one distinct qualifying choice, independently of its slot cost. Free Basic, automatic Running and Secondary choices do not fill this Related minimum. Printed89 makes implants optional.

Original PDF SHA256: `448715cb4301ca9cd0bc7333bda7e1f88a089f05f33b33f625736a7a96700b9c`. Root and independent Spec visually read88/89/316; ignored source renders are `tmp/pdfs/18b4-source/city-rat-091.png`, `city-rat-092.png`, and `tmp/pdfs/05d28-source/physical-319.png`. Markdown remains a locator.

With constant dice4/IQ12, Related Climbing45% (40+5) and Prowl40% (25+15), plus Expert, satisfy three distinct choices and leave seven Related slots. Martial Arts/Assassin satisfy the same minimum but leave six. These selections add no attribute dice: existing MA12/PS12/PE13/SPD33, HP17/SDC32 remain unchanged. A two-slot style alone credits one choice. Later acquired training cannot replace initial choices.

## Shared projection

Add optional `paid_hand_to_hand` IDs to an existing requirement. Support Related/distinct counting with a bounded nonempty distinct list of known styles whose own Related cost is a strict positive integer. Free/unknown styles, unsupported pools/counting and malformed inactive declarations reject before dice or writes. Capacity and actual training credit each increase by at most one, regardless of alternative count or slot cost. Existing requirements without the field retain their exact row/save shape.

Use the selected style's own cost, not total combat cost, which also includes weapon proficiencies. Compare retained acquisition level with the existing `before_level` cutoff; elapsed `learning_age` is not acquisition level. Reuse current choices and retained learning keys. Preserve existing replacement/reselection and permitted backdating behavior; introduce no ancestry ledger or persisted counter. These cutoff/replacement policies extend existing requirements rather than claiming the book prescribes a save schema.

The optional `training_credits` view list identifies the actual credited training/name/learning level/source; it contains at most one entry. Browser and PDF explain the minimum and the one distinct credit separately from paid slots. Existing honor-system choices remain retained with applicable guidance. Projection/reopen/import and requirement recalculation during undo draw no new dice; ordinary advancement retains its existing resource-roll behavior.

## Scope and verification

Verify source counts/costs, duplicate/Secondary/free/late exclusions, paid weapons alongside free Basic, inactive rejection, stale edits, retained first-learning/reselection, explicit permitted backdating, advancement/undo, no-dice exact portable/reopen, historic pins and explicit upgrades. Keep previous definitions/manifest entries immutable; other class profiles, ordinary catalogs, equipment and psychic packs remain unchanged.

City Rat PPE base/age22/rounding, optional augmentation catalog and wider canonical/subtype/racial work remain open. Primary89 supports correcting older “required implants” prose; source-owned optional selection remains future scope. This batch closes its initial-choice requirement only.
