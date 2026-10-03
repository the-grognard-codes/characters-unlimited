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
| `tickets`, `dependencies` | Existing implementation ticket names and canonical dependency IDs within the same game; unassigned tickets are counted, unresolved dependencies belong in findings |
| `findings` | Nonempty remaining review/implementation findings |

Catalog findings also name the unreviewed corpus areas. New records must be confirmed against prose/tables and original PDFs, with missing options and variants explicitly tracked. Rebuilding the provisional inventory with changed sources invalidates earlier identity evidence until re-reviewed; matching text headings do not carry acceptance across fingerprints.

The application joins this catalog into its coverage response and shows searchable identities separately from provisional sections. It counts zero mechanically reviewed or fully automated entries. Full corpus audit, complete dependency mapping, bounded named content tickets and numerical acceptance remain in 02B and subsequent content slices.

The current catalog has 67 identities and 66 entries awaiting named content batches. Explicit links connect Psi-Stalker variants and shared dragon creation rules. These known relationships supplement the pending full dependency review; Heroes modifiers do not become extra random power categories.

The Heroes core subpath pass adds four Hardware specializations, Super Vehicle construction, five Special Training paths, four robot types and shared body/construction rules. Names and chapter locators were checked against original contents pp. 4–5; the training table p. 211 and robot types/construction pp. 194, 196–197 and 200 were also visually inspected. Original p. 197 explicitly reuses Type 1 pilot rules for Exoskeletons; the catalog records the source link without certifying calculations. Mechanical/dependency review, education, equipment, progression and complete named content batches remain pending.
