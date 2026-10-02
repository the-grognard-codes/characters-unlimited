# Character creator design interview

Status: Shared understanding confirmed by the user on 2026-10-02. Specification and ticket refinement are in progress; the final implementation plan has not yet been approved.

## Accepted requirements — round 1

- Support Rifts and Heroes Unlimited initially. Palladium Fantasy Second Edition is deferred in round 2 until its source book is available.
- Every O.C.C., race, and R.C.C. from the supplied books must be available. The user rejected limiting supplemental character options to a curated subset. Round 2 confirms full mechanical coverage.
- Run locally on Windows through a browser interface and Windows launcher; work offline without an account.
- Guide selections and calculations using the selected rules by default. Permit honor-system manual adjustments without GM access gates, mandatory reasons, or override markers (round 2 supersedes the corresponding round-1 controls). Round 3 settles additive adjustments and fixed values.
- Configure rerolling ones and extra-die/drop-lowest generation options.
- Support creation, saving, reopening, duplication, and level advancement. Live session tracking is outside initial scope.
- Export editable PDF fields with the supplied sheets' visual identity and matching continuation pages. Application saves are authoritative; importing PDF edits is outside scope.
- Provide a documented, validated rule-pack schema with source references. Markdown conversion yields a draft requiring review before activation.
- Continue the interview, then conduct specification and ticket refinement before implementation.

## Source inventory

The repository currently contains 13 Markdown books: Heroes Unlimited Revised Second Edition; Aliens Unlimited; Powers Unlimited 1–3; Rifts Ultimate Edition; Merc Ops; Mercenaries; and Rifts World Books 2, 6, 7, 9, and 21.

No Palladium Fantasy rules book is currently present in sources-markdown. The sheet references are a one-page static Palladium Fantasy sheet and a two-page Rifts PDF with 299 form fields. Their visual styling has not yet been assessed.

## Open decisions

No remaining product decision on the current interview frontier. Source-specific ambiguities and missing dependencies must be investigated and reviewed during rule extraction; they are not silently resolved by this interview.

## Accepted requirements — round 2

- Defer Palladium Fantasy entirely from the initial requirement. Its intended future edition is Second Edition; the user does not yet have the book.
- Fully automate creation and advancement mechanics for every supplied option, including spells, psionics, superpowers, cybernetics, robot construction, mutant animals, and alien abilities.
- Explicit option-specific exceptions take precedence over general rules. Otherwise use the selected core edition unless a supplement explicitly replaces a rule. Record uncertain or corrupted passages as proposed interpretations for review before rule-pack acceptance.
- Keep game catalogs separate. Cross-game options and automatic conversions are outside the initial scope.
- Offer book-prescribed random generation and direct choices; allow manually entered attributes, individual rerolls, and whole-set rerolls, retaining roll history. Apply exceptional-attribute rules by race and game. Required visible deviation markers are superseded by the honor-system instruction below.
- Permit manual adjustments on the honor system. No separate GM access, mandatory reason, or override marker is required.

## Accepted requirements — round 3

- Autosave locally and support portable character-file import/export, including game and rule-pack versions.
- Preserve the rule-pack versions used by saved characters. Provide an explicit update with a preview of affected selections and values.
- Support XP-based advancement, direct level selection, and creation above level one. Keep a snapshot before each advancement so it can be undone.
- When earlier race, class, or power-category selections change, retain compatible selections, identify selections that no longer qualify, and allow replacement or retention. Never silently discard entered work.
- Support additive adjustments and fixed-value replacements. An adjusted strike bonus of +4 plus a manual +2 becomes +7 after a +1 advancement; a fixed value of +6 remains +6. Neither requires approval, a reason, or a sheet marker.
- Track starting funds and purchases, quantities, ammunition, carried weight, equipped versus stored items, armor damage capacity, and applicable equipment bonuses. Warn about budget and weight issues without blocking honor-system edits or selections.

## Source findings relevant to remaining decisions

- Exceptional-attribute generation differs between the transcribed Heroes Unlimited and Rifts rules. Do not share one unqualified exceptional-die algorithm across games. Rifts explicitly excludes bonuses gained later from skills, classes, augmentation, or magic from exceptional-roll eligibility.
- Rerolling individual ones and adding a die/drop-lowest are optional house rules; their scope and ordering require explicit decisions.
- Combat modifiers depend on attack context and strength type; one universal strike or damage total would be misleading.
- Heroes Unlimited education determines programs and skill bonuses, with category-specific exceptions. Rifts skill entitlements are driven by O.C.C./R.C.C. and their required, related, and secondary skill rules.

## Accepted requirements — round 4

- Reroll initial attribute dice showing one repeatedly until the result is not one. Do not offer a reroll-once variant.
- Retain the proposed house-rule ordering: reroll initial dice, drop the lowest if enabled, then apply game-specific exceptional-attribute rules to the retained total. Extra-die/drop-lowest adds one die to the prescribed racial pool while retaining its original die count. Exceptional bonus dice are unaffected by these house rules. This ordering was stated back to the user after the round-4 answer.
- Show an overall combat summary and attack-specific entries for unarmed attacks and equipped weapons. Separate melee, ranged, and conditional modifiers. Expand totals to show contributing attributes, skills, class, race, powers, and equipment.
- Create a Heroes Unlimited sheet close to the Rifts reference in structure, tailored to Heroes Unlimited where required. A small visual element or title is acceptable. The user reported finding no official Heroes Unlimited Second Edition sheet on the Palladium site; this is user-provided context, not an independently verified inventory claim.
- Export statistics, skills and percentages, attacks, powers, spells, psionics, equipment, and notes. Put concise ability summaries on continuation pages; retain detailed calculation explanations in the application.
- Provide a guided sequence, freely accessible sections, and persistent character summary. Show eligibility, remaining selections, concise explanations, and book/page references by relevant choices. Heroes Unlimited education/background steps depend on the chosen category.
- Deliver a self-contained Windows package with a double-click launcher, setup instructions, and a clear location for character data and backups. Normal use requires no developer tools or terminal commands.
- Completion requires a checklist covering every supplied character option, validated rule packs, meaningful tests for dice, skill entitlements, bonus stacking, advancement, and special construction systems, representative end-to-end characters across major creation paths, and PDF checks for layout, overflow, and saved editable fields. List every unresolved source interpretation for user review before final acceptance.

## Accepted requirements — round 5

- Always allow saving incomplete characters. Allow PDF export after showing a completion checklist, leaving unfinished fields blank. No mandatory draft stamp or override marker.
- Allow character-specific custom skills, powers, weapons, armor, and equipment with editable values and explicit bonuses. Reusable additions belong in reviewed rule packs; prose alone does not generate mechanical effects.
- If a supplied option depends on rules absent from the supplied collection, keep it visible, identify the missing dependency, permit manual completion, and record the automation gap in the coverage checklist. Do not invent mechanics. Require the missing source or an agreed interpretation before claiming full automation for that option.
- Manual fallback for a missing dependency is an interim usability feature, not evidence that the full-automation requirement has been met.

## Confirmation checkpoint

The user confirmed shared understanding on 2026-10-02. Proceed with specification and ticket refinement. No application implementation, commit, publication, or deployment has been performed at this checkpoint.

## Initial source boundary

The initial corpus is the following 13 files in sources-markdown. Additional source deliveries change this boundary explicitly.

- Aliens Unlimited.md
- Heroes Unlimited - Powers Unlimited 1.md
- Heroes Unlimited - Powers Unlimited 2.md
- Heroes Unlimited - Powers Unlimited 3.md
- Heroes Unlimited - RPG - 2E.md
- Rifts - Merc Ops.md
- Rifts - Mercenaries.md
- Rifts - Ultimate Edition.md
- Rifts - World Book 02 - Atlantis.md
- Rifts - World Book 06 - South America 1.md
- Rifts - World Book 07 - Underseas.md
- Rifts - World Book 09 - South America 2.md
- Rifts - World Book 21 - Splynn Dimensional Market.md
