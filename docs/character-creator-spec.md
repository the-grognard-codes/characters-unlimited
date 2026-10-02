# Characters Unlimited specification

Status: Review draft, synthesized from the confirmed design interview of 2026-10-02. Product requirements below are confirmed; proposed implementation and testing contracts await review. Tracker destination and ticket breakdown await approval.

## Problem Statement

Players creating Rifts and Heroes Unlimited characters must combine scattered race, class, education, skill, power, equipment, and advancement rules. Manual calculation makes it difficult to select the correct number of eligible skills, calculate contextual combat bonuses, and produce a complete editable character sheet. Adding books needs a repeatable process that preserves source provenance and distinguishes implemented mechanics from gaps.

## Solution

Provide an offline Windows utility with a double-click launcher and a local browser interface. Guide players through creation while allowing free navigation, honor-system manual adjustments, and incomplete saves. Fully automate the character options in the supplied Rifts and Heroes Unlimited books, explain calculated values, support advancement, and export editable PDFs styled after the supplied sheet references.

Use reviewed, versioned rule packs to incorporate source books. Track every source option and its mechanical dependencies. Missing source rules stay visible and allow manual completion but remain automation gaps until their definitions or agreed interpretations are available.

## User Stories

1. As a player, I want to launch the utility on Windows without developer tools, so that I can use it like an ordinary application.
2. As a player, I want to work offline without an account, so that character creation does not depend on a service.
3. As a player, I want to choose Rifts or Heroes Unlimited, so that my character follows that game's rules and catalog.
4. As a player, I want every supplied O.C.C., race, R.C.C., and other character category to be discoverable, so that supported choices are not arbitrarily omitted.
5. As a player, I want race and class choices to determine attribute formulas and prerequisites, so that generation follows the selected option.
6. As a player, I want book-prescribed attribute rolls, so that ordinary generation follows the correct edition.
7. As a player, I want optional repeated rerolls of ones and an extra die with the lowest dropped, so that I can use agreed generation rules.
8. As a player, I want exceptional attributes handled for my game and race, so that later bonuses do not accidentally trigger initial-generation benefits.
9. As a player, I want manual attributes, individual rerolls, whole-set rerolls, and roll history, so that generation supports my table's practices.
10. As a player, I want required skills and eligible selection pools presented correctly, so that I know what my class grants and what I may choose.
11. As a Heroes Unlimited player, I want education and backgrounds to determine programs, selections, and bonuses, so that skill creation follows my character category.
12. As a player, I want remaining skill counts, category restrictions, and prerequisites shown, so that I can finish legal selections without counting by hand.
13. As a player, I want skill percentages and level improvements calculated, so that advancement keeps my sheet accurate.
14. As a player, I want physical skills, hand-to-hand skills, weapon proficiencies, attributes, race, class, and powers combined correctly, so that combat totals reflect their actual rules.
15. As a player, I want an overall combat summary and individual attack entries, so that I can distinguish unarmed, melee, ranged, and conditional bonuses.
16. As a player, I want to expand a calculated value and see its contributions, so that I can understand its result.
17. As a player, I want powers, spells, psionics, resource capacities, and category-specific selections automated, so that special abilities are supported beyond descriptive labels.
18. As a player, I want alien, mutant-animal, robot, cybernetic, and other construction choices reflected in my character, so that unusual categories receive the same mechanical support.
19. As a player, I want categorized weapons, armor, and equipment, so that I can find suitable items.
20. As a player, I want quantities, ammunition, prices, funds, carried weight, equipped items, storage locations, and armor capacities recorded, so that equipment has coherent effects.
21. As a player, I want funds and weight warnings without forced rejection, so that I can follow the honor system.
22. As a player, I want additive adjustments and fixed values, so that I can choose whether a manual edit evolves with calculated statistics.
23. As a player, I want custom skills, powers, weapons, armor, and equipment with explicit effects, so that I can represent character-specific additions.
24. As a player, I want no GM password, mandatory reason, or override marker, so that manual edits remain straightforward.
25. As a player, I want guided steps, free navigation, concise rule help, source references, and a persistent summary, so that I understand both my choices and remaining work.
26. As a player, I want earlier choice changes to retain compatible work and identify incompatible selections, so that I can revise a character without silent data loss.
27. As a player, I want autosaving, reopening, duplication, and incomplete saves, so that I can work across sessions.
28. As a player, I want portable character import and export, so that I can move or share characters between PCs.
29. As a player, I want XP-based advancement, direct level selection, and above-level-one creation, so that I can use new and established characters.
30. As a player, I want pre-advancement snapshots and undo, so that advancement mistakes are reversible.
31. As a player, I want my saved character's rule versions preserved, so that corrections do not silently change an established character.
32. As a player, I want to preview and explicitly apply rule updates, so that I understand their effect.
33. As a player, I want an editable Rifts PDF matching the reference's visual identity, so that my exported sheet is usable at the table.
34. As a Heroes Unlimited player, I want a Rifts-like sheet adapted to my game's needs, so that education, powers, and equipment have appropriate space.
35. As a player, I want matching continuation pages and concise ability summaries, so that long characters remain legible.
36. As a player, I want incomplete PDF export after a completion checklist, so that I can finish fields manually without a mandatory draft stamp.
37. As a player, I want application saves to remain authoritative, so that edits in an exported PDF do not ambiguously alter my character.
38. As a rule-pack maintainer, I want documented conversion and validation, so that additional books can be incorporated consistently.
39. As a rule-pack maintainer, I want source references, review states, dependency checks, and coverage evidence, so that uncertain transcriptions do not silently become accepted mechanics.
40. As a player, I want missing dependencies identified while retaining access to the option, so that I can manually complete a character without mistaking fallback for automation.
41. As an owner, I want a source coverage checklist, representative end-to-end characters, and verified editable PDFs, so that completion is demonstrated rather than assumed.

## Implementation Decisions

### Confirmed product contracts

- Initial games: Rifts Ultimate Edition and Heroes Unlimited Revised Second Edition. The source boundary is the 13 Markdown books recorded in the design interview. All supplied character options and their creation and advancement mechanics are in scope.
- Game catalogs remain separate. Shared mechanical implementations may be reused only where rule behavior agrees; this does not permit foreign game choices.
- Rule precedence: explicit option-specific exceptions override general rules; otherwise the selected core edition governs unless a supplement explicitly replaces a rule. Uncertain passages require a reviewed interpretation.
- Attribute generation uses the selected option's prescribed pool. Repeatedly reroll initial dice showing one if enabled; add one die and retain the original count if extra-die/drop-lowest is enabled; drop the lowest after rerolls; apply eligible game-specific exceptional rules to the retained total. House rules do not alter exceptional bonus dice. Later skill, class, equipment, or ability bonuses do not re-trigger initial exceptional rolls.
- Pool transformations must preserve the source formula's constants and explicit exceptions. Formulas that do not fit ordinary dice-pool generation require a reviewed definition rather than an invented transformation.
- A fixed value replaces a derived result; an additive adjustment changes the derived result as it evolves. Do not require approval, reasons, or a sheet marker for either.
- Rule guidance identifies unmet requirements and remaining choices without preventing honor-system retention. Computation must distinguish an intentionally retained incompatible selection from an accidentally valid one without imposing a special override marker.
- Equipment capacities are character-sheet values. Recording ammunition and armor capacities does not expand scope into an automated combat encounter or live resource-tracking system.
- Always permit incomplete saves. Before incomplete PDF export show a checklist, then leave unspecified values blank; do not fabricate zeroes or legal defaults.
- Saved characters are authoritative. PDF edits are not imported. Editable PDFs must retain usable form fields after export, rather than flattening their values into page artwork.

### Proposed module and interface contracts

- A local application service owns saved characters, immutable accepted rule versions, backups, imports, and PDF generation. A browser interface uses that service; normal operation has no network or account dependency. Bind the service to loopback and include all runtime and visual assets in the Windows package.
- A character application interface accepts character selections, generation settings, explicit manual values, rule-version references, and actions such as selection changes, advancement, and update preview. It returns a saved character projection, available choices, selection entitlements, calculation explanations, completion findings, and missing dependencies. Random generation receives an injectable random source for reproducible behavioral checks.
- Rule evaluation is independent of browser state and file storage. Contributions identify their source, target, operation, condition, and stacking or replacement policy; modifiers cannot be naively summed when the rule specifies precedence, replacement, or conditional applicability.
- The rule-pack schema includes game and edition, stable option identifiers, pack/schema versions, source identity and locators, dependencies, availability conditions, attribute formulas, selection entitlements, progression, modifiers, attack contexts, item categories, and descriptive summaries. Validation rejects malformed structures, duplicate identifiers, unresolved accepted references, dependency cycles, and unsupported mechanical operations before activation.
- Accepted rules use declarative mechanical operations; importing a pack does not execute arbitrary source-supplied code. Complex systems may require named, tested rule handlers whose inputs and semantics are documented. Unknown handlers produce a visible automation gap rather than a made-up calculation.
- Source locators include book identity and section or Markdown location; include printed page numbers where supported by evidence. Do not equate Markdown line numbers with printed pages or fabricate references absent from the transcription.
- Conversion yields draft rule packs and a review report. Review distinguishes accepted mechanics, uncertain interpretations, missing source dependencies, and implementation gaps. Reviewed packs can be activated locally; source prose by itself never becomes executable rules.
- Saved characters include stable identities, game, character-format version, selections, generated base values and roll history, custom entries, manual adjustments, rule references, and advancement snapshots. Derived projections are reproducible from accepted rules and persisted character inputs.
- Portable exports preserve or include the exact rule definitions needed to reopen the character offline on another PC, with provenance and content identity. Imports validate before changing an existing character; missing or incompatible versions are reported without silent substitution.
- Autosaves and backups must tolerate interruption without replacing a valid save with a partial file. Establish one documented user-data location independent of the installed application folder. Duplicates receive independent character identities.
- Rule updates run as previews against preserved character state. Show changed values, new unmet requirements, and missing selections. Applying the update is explicit and recoverable; opening an existing character does not apply it.
- Advancement uses source-defined XP and progression, including multiclass or special progression where present. Creating above level one must resolve all prior-level selections and rolled gains. Replay, undo, or switching between XP and direct level cannot double-apply bonuses or re-roll retained gains.
- Selection changes preserve entered and rolled values where compatible. Explain consequences before replacement; changing a prerequisite must not silently erase dependent skills, powers, or equipment.
- PDF export consumes the same character projection used by the UI. Rifts follows the supplied Rifts reference; Heroes Unlimited follows its structure with game-specific sections and an optional small title or visual. Overflow creates matching continuation pages with independently editable fields and concise summaries.
- The implementation language and frameworks are left to implementation. The packaging contract, offline behavior, data portability, and mechanical interfaces govern that choice; no framework-specific dependency is required by this draft.

## Testing Decisions

Proposed primary test seam: the character application interface, exercised with accepted rule fixtures, character actions, and controlled dice. Verify player-observable projections, allowed choices, explanations, and saved inputs; do not test private helpers or mirror implementation arithmetic without independent expected results.

Two additional boundaries need their own evidence: persistence/portable-file round trips, and actual editable PDF artifacts. Use focused UI checks for navigation and displayed selection consequences, plus a packaged Windows smoke test. This is a new application; there are no existing application test conventions to reuse.

- Dice cases include both games' exceptional rules, racial pools and constants, repeated ones, extra-die/drop-lowest ordering, both options combined, individual and whole-set rerolls, retained histories, and exclusion of later modifiers from exceptional eligibility.
- Rule tests cover category counts, required and secondary skills, education-specific programs and exceptions, prerequisites, progression, caps, physical and hand-to-hand bonuses, weapon contexts, strength categories, explicit exceptions, and non-stacking effects.
- Special-system checks use source-grounded representative characters for powers, magic, psionics, augmentation, alien generation, mutant animals, and construction. Expected values cite reviewed source evidence rather than being copied from evaluator output.
- Lifecycle checks cover incomplete saves, compatible and incompatible backtracking, duplication, custom entries, fixed values versus additive adjustments, repeated advancement, XP/direct-level switching, above-level-one creation, undo, and explicit rule updates.
- File checks cover offline portability with pinned rules, failed or incompatible imports, interrupted saves, and recoverable update previews.
- PDF checks inspect field identities and values, edit and save exported fields, and render short and long characters for visual inspection. Verify continuation pages, non-ASCII names, blank incomplete fields, multiline content, legible sizing, and no clipped text.
- Coverage evidence accounts for every supplied option and dependency, with structural validation for all entries and meaningful mechanical verification. Sampling can supplement coverage, not justify omission. A selectable option with an automation gap is not fully implemented.
- Release checks launch the packaged application on Windows without developer tools and with network access unavailable, then create, reopen, advance, import/export, and generate both games' PDFs.

## Out of Scope

- Palladium Fantasy, including its sheet export, until explicitly reintroduced with its source book.
- Cross-game catalogs or automatic conversion.
- Hosted services, accounts, collaboration, and remote publishing.
- Live encounter execution or automated in-session damage/resource tracking.
- Importing manually edited PDFs into saved characters.
- Automatically activating unreviewed book conversions or inferring mechanical effects from custom prose.
- Mandatory GM access controls, edit reasons, override markers, or draft stamps.

## Further Notes

The current sheet references have been inventoried but not visually rendered. Their exact typography, spacing, and artwork must be assessed during the PDF tickets before claiming a visual match.

Source transcriptions require interpretation review. Missing referenced books or ambiguous passages can block full automation for particular options; list those dependencies explicitly and request the source or an agreed interpretation. Manual fallback does not satisfy the completion gate.

Implementation tickets are review drafts until granularity, genuine blocking edges, test seams, and tracker destination are approved. Content work must be divided using a complete source inventory; one whole supplement is not assumed to fit a single implementation context.
