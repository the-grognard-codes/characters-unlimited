# Character creator ticket breakdown

> Scope update (2026-10-05): [Player-focused scope amendment](player-focused-scope.md) supersedes conflicting exhaustive calculation requirements. The original text is retained for retrospective comparison.

Status: Review draft. These are proposed vertical slices, not published ready-for-agent issues. Specification: the character creator specification. Review test seams, granularity, and blocking edges before publication.

Each slice includes the applicable rule/schema support, character interface, player or maintainer UI, and meaningful behavioral checks. Initial slices prove representative source-grounded options; they do not substitute for complete corpus coverage. Keep slices small enough for a fresh implementation context. If source inventory reveals a larger slice, split it into named, dependency-ordered cases before implementation.

## Proposed tickets

| ID | Title | Blocked by | What it delivers |
| --- | --- | --- | --- |
| 01 | Create and reopen a basic Rifts character | None | Launch a local UI, select one source-grounded human/class path, generate attributes, explain their base values, enter identity/notes, and autosave/reopen an incomplete character. Establish the rule-version and character contracts through this usable path. |
| 02 | Account for the full supplied corpus | 01 | Show a maintainer coverage view covering every supplied option, source locator, dependency, review finding, and automation state. Freeze the initial 13-book manifest and propose bounded content batches for all remaining entries. |
| 03 | Create and reopen a basic Heroes Unlimited character | 01 | Select Heroes Unlimited independently of Rifts, use a representative core category, generate source-correct attributes, save/reopen it, and keep the catalogs separate. |
| 04 | Configure dice and manually edit character values | 01, 03 | Use both house-rule toggles, repeated rerolls of ones, individual/whole-set rerolls and history, manual attributes, additive adjustments, and fixed values; demonstrate both games' exceptional rules and racial-formula contracts. |
| 05 | Complete a Rifts skill selection path | 01 | Grant required skills, expose related and secondary pools with correct counts/categories/prerequisites, compute percentages, and allow honor-system retention with useful completion guidance. |
| 06 | Complete Heroes Unlimited education and skills | 03 | Roll or choose education, select a representative program/background, respect category exceptions, show remaining skill selections, and calculate skill percentages and education bonuses. |
| 07 | Explain unarmed and weapon combat totals | 05, 06 | Select physical/hand-to-hand/proficiency skills, compute representative melee/ranged/unarmed attacks with proper strength types and conditions, and expand totals into source-grounded contributions. |
| 08 | Purchase, equip, and store equipment | 07 | Browse categorized items, manage funds, quantities, ammunition, carried/storage locations, armor capacities, and contextual equipment effects, with nonblocking budget/weight warnings. |
| 09 | Create a character with superpowers | 03, 07 | Complete one representative Heroes Unlimited power-category path, enforce its selection entitlements, apply its attributes/resources/combat effects, and explain them. Remaining power families are content batches. |
| 10 | Create a magic character | 01, 07 | Complete one representative Rifts practitioner path including spell selections, P.P.E., progression definitions, and conditional spell effects; expose missing source dependencies. |
| 11 | Create a psychic character | 01, 03, 07 | Resolve representative game-specific psychic eligibility and selections, I.S.P., derived bonuses, and source-specific restrictions without merging game catalogs. |
| 12 | Create a nonhuman or racial-class character | 04, 05, 06, 07 | Complete representative race/R.C.C. paths, use racial attribute pools and class restrictions, preserve compatible earlier selections, and expose incompatible choices without silently deleting work. |
| 13 | Build a character with augmentation | 08, 12 | Complete one representative cybernetic/augmented path, choose compatible components, apply replacements and strength/combat changes, and retain costs and capacity effects. |
| 14 | Build a robot character | 08, 09 | Complete one source-grounded robot construction path with component choices, budget/capacity constraints, and resulting attributes and attacks. Additional robot/construction systems receive their own bounded content batches. |
| 15 | Generate an alien character | 06, 09, 12 | Complete one Aliens Unlimited generation path including racial/body/ability choices and education or category interactions, with source-derived results rather than descriptive placeholders. |
| 16 | Generate a mutant-animal character | 06, 09, 12 | Complete one supplied mutant-animal path including construction allocations, characteristics, skills, and resulting powers/combat effects. |
| 17 | Add custom entries and revise earlier selections | 08, 09, 12 | Add character-specific skills, powers, weapons, armor, and equipment with explicit effects; demonstrate reversible backtracking with compatible work retained and incompatible work identifiable. |
| 18 | Move characters between PCs and update their rules | 02, 04 | Duplicate and portably import/export characters with exact rule versions; preview/apply corrections explicitly; verify interruption-safe saves and backups, rejected imports, and reopening without silent rule substitution. |
| 19 | Advance characters and undo advancement | 05, 06, 09, 10, 11, 12, 18 | Use XP or direct level, create above level one, resolve progression choices and rolled gains, retain pre-advancement snapshots, and undo/replay without duplicate bonuses. Exercise representative ordinary and special paths. |
| 20 | Export editable Rifts sheets | 08, 10, 11, 18 | Inspect the reference visually, export an actual Rifts character with usable editable fields, add matching continuation pages, and export incomplete characters after a checklist. Render and edit/save both short and long samples. |
| 21 | Export tailored Heroes Unlimited sheets | 09, 18, 20 | Adapt the Rifts visual structure to Heroes Unlimited education, powers, and equipment; verify editable values and continuation pages using both short and long HU characters. |
| 22 | Convert, review, and activate an additional rule pack | 02, 12 | Run a documented Markdown-to-draft conversion on a bounded fixture, inspect source evidence and uncertain passages, validate dependencies and mechanical operations, activate only reviewed definitions, and see new choices work in the builder. |
| 23 | Deliver the self-contained Windows package | 18, 20, 21 | Double-click a packaged offline application without developer tools; document data/backups and verify create/save/reopen/advance/import/export/PDF flows in the packaged environment. Full content completion is a release gate, not a prerequisite to testing packaging. |
| 24 | Prove full coverage and final release acceptance | 13–17, 19, 22, 23, every content batch | Reconcile every supplied option and mechanical dependency, run source-grounded representative end-to-end characters, resolve or explicitly report remaining review findings, and verify packaged offline operation and editable PDFs. Any automation gap prevents claiming full scope completion. |

## Content batches: required fan-out after ticket 02

The number and names of content tickets must follow the complete inventory, not a guessed count of O.C.C.s or races. Before publication of those tickets, produce an entry-to-ticket map covering all 13 books and review the resulting breakdown. This fan-out is mandatory work, not optional follow-up.

Each actual content ticket must name its exact source options and dependencies. It implements a narrow, fully usable group of options through selection, calculations, advancement, and sheet projection, with independent expected-value evidence. Split complex options or construction systems further when one context is insufficient. Avoid tickets titled only "implement a whole book" or "import all remaining rules."

Suggested grouping is by mechanical family within a book, not by arbitrary page ranges. Each batch is blocked by ticket 02 and only the feature tickets or shared-rule batches it actually uses. For example, an ordinary Rifts class batch does not depend on Heroes Unlimited mutant-animal support; a spellcaster batch requires the magic path and its referenced spell definitions.

### Draft content-ticket template

- **Title:** Enable the named source options from the named book.
- **What to build:** Players can create, revise, advance, and export each named option using its complete supported mechanics.
- **Blocked by:** Corpus manifest plus the exact supporting feature and shared-rule tickets.
- **Acceptance:** Every named entry is selectable in its own game; source locators and precedence are reviewed; selection counts and derived values are independently verified; advancement and relevant attack contexts work; dependency gaps are explicit; PDF projection contains the relevant values; coverage links identify evidence.
- **Size gate:** Split before implementation if the named entries and supporting definitions will not fit a fresh context. Review each resulting ticket's dependencies.

## Review points

1. Approve the primary character-interface test seam, with separate persistence and editable-PDF artifact checks.
2. Confirm whether the proposed feature slices are too coarse or too fine and identify merges/splits.
3. Confirm that blocking edges represent genuine integration prerequisites. Independent source analysis can start earlier than a ticket's UI dependency.
4. Approve the tracker destination. Local Markdown publication uses one file per approved ticket in dependency order and the ready-for-agent status; external publication requires explicit authorization.
5. Approve the inventory-first content fan-out. Its final named tickets are reviewed after ticket 02 establishes complete option coverage; no unknown corpus work is hidden inside a single agent-sized issue.
