# Canonical option identity audit

`characters_unlimited/data/canonical-options.json` is a source-bound identity catalog. `source-inventory.json` retains the provisional headings and book fingerprints; neither file executes rule text or activates a character option.

The initial 30 identities come from the original Ultimate Edition class list, printed p. 43 / PDF p. 46. Each record links the corresponding body heading in the corrected Markdown. Aliases consolidate list labels and body titles rather than treating repeated stats or skill headings as new classes. The SAMAS Pilot and Elite RPA labels identify the same listed class. A subsequent pass adds six hatchlings, their common creation rules, Civilized/Wild Psi-Stalkers, ten Heroes categories and two optional modifiers. Dog Boy breeds and further child paths still need audit. This does not claim a complete core catalog or mechanical review.

The version-one record contract is validated by `option_audit.audited_coverage`:

| Field | Meaning |
| --- | --- |
| `id`, `name`, `kind`, `book_id` | Unique stable option identity, display name, mechanical family and source book |
| `aliases`, `candidate_ids` | Alternate labels and source-section references; candidate book/hash must match |
| `source` | Exact Markdown/PDF SHA-256 and positive one-based printed/PDF evidence pages |
| `identity_review` | `pending` or `confirmed`; confirmation applies to identity only |
| `mechanical_review`, `dependency_review` | `pending` in this initial contract; numerical acceptance needs its later review/evidence contract |
| `automation` | `not-implemented` or `partial`; full automation is deliberately unavailable here |
| `tickets`, `dependencies` | Existing implementation ticket names and canonical dependency IDs within the same game (rule/source dependencies, not mandatory character prerequisites); unassigned tickets are counted, unresolved dependencies belong in findings |
| `findings` | Nonempty remaining review/implementation findings |

Catalog findings also name the unreviewed corpus areas. New records must be confirmed against prose/tables and original PDFs, with missing options and variants explicitly tracked. Rebuilding the provisional inventory with changed sources invalidates earlier identity evidence until re-reviewed; matching text headings do not carry acceptance across fingerprints.

The application joins this catalog into its coverage response and shows searchable identities separately from provisional sections. It counts zero mechanically reviewed or fully automated entries. Full corpus audit, complete dependency mapping, bounded named content tickets and numerical acceptance remain in 02B and subsequent content slices.

The current catalog has 384 identities and 383 entries awaiting named content batches. Explicit links connect Psi-Stalker variants, shared dragon creation rules, and South America 1/Underseas race, occupation and bi-form paths. These known relationships supplement the pending full dependency review; Heroes modifiers do not become extra random power categories.

The Heroes core subpath pass adds four Hardware specializations, Super Vehicle construction, five Special Training paths, four robot types and shared body/construction rules. Names and chapter locators were checked against original contents pp. 4–5; the training table p. 211 and robot types/construction pp. 194, 196–197 and 200 were also visually inspected. Original p. 197 explicitly reuses Type 1 pilot rules for Exoskeletons; the catalog records the source link without certifying calculations. Mechanical/dependency review, education, equipment, progression and complete named content batches remain pending.

The Atlantis/Splynn pass adds forty racial, occupational, form and conversion identities. Original contents and selected body headings confirm names and printed/PDF offsets. Undead Slayer overview/full-build locators share one identity; repeated Staphra Mystic lore/stat headings do too. Monster Were-Dragon remains a form-rule identity. Kittani contents/body class-label discrepancies, Pythonan occupational variants and Bio-Borg shared conversion rules remain explicit review findings. Known inherited source links do not impose another mandatory class choice.

The Mercenary/South America 2 pass adds 55 creation identities: nine new mercenary classes, company design, optional Lost Ones and Auto-G templates, and South America 2 racial/occupational paths and four True Inca heritage rules. Mercenaries PDF pages are printed +2, Merc Ops printed +1 and South America 2 printed/PDF pages match. The latter is verified at original contents and printed 20–21, 107 and 109; the damaged printed/PDF108 stays blocked. Named NPC examples and external racial profiles require further reconciliation, not invented classes.

The Powers Unlimited 2 pass adds 47 category, modifier, construction, branch and power identities. Sixteen Immortal table results share evidence while retaining distinct identities; Minor Hero remains a modifier rule. Original contents and selected body pages verify labels and printed/PDF offsets (+1). Genetic options, mental disciplines, weapon specialties and all numerical mechanics still need supporting-entry and content-ticket review.

The initial Aliens Unlimited pass adds 44 identities from six racial groups, confirmed against original body headings and footers (printed pp. 50–96, PDF pp. 51–97). Darkith retains Cameroon variant ancestry; Wardions is a Dergins warrior-class branch, not a separate species. Singular/plural stat aliases remain searchable. Remaining racial groups, generation choices, edition reconciliation and all numerical dependencies stay pending. Exact name/candidate/page locators are recorded in [the source evidence](evidence/02b8-source-locators.md).

The next Aliens pass adds 69 remaining profile, caste/training/augmentation, generation/shared-rule and monster identities. Original body scans confirm names, parent relationships and player/NPC distinctions without imposing an application access gate. The introductory 84-race count conflicts with 85 ordinary profiles; supporting entries, source-count reconciliation, edition precedence and full mechanics remain open. [The source mapping](evidence/02b9-source-locators.md) retains exact candidate and page evidence, including overlapping parent candidates for embedded branches.
