# Canonical option identity audit

`characters_unlimited/data/canonical-options.json` is a source-bound identity catalog. `source-inventory.json` retains the provisional headings and book fingerprints; neither file executes rule text or activates a character option.

The first 30 identities come from the original Ultimate Edition class list, printed p. 43 / PDF p. 46. Each record links the corresponding body heading in the corrected Markdown. Aliases consolidate list labels and body titles rather than treating repeated stats or skill headings as new classes. The SAMAS Pilot and Elite RPA labels identify the same listed class. Dragon species and Psi-Stalker/Dog Boy child paths require further audit. This does not claim a complete core catalog or mechanical review.

The version-one record contract is validated by `option_audit.audited_coverage`:

| Field | Meaning |
| --- | --- |
| `id`, `name`, `kind`, `book_id` | Unique stable option identity, display name, mechanical family and source book |
| `aliases`, `candidate_ids` | Alternate labels and source-section references; candidate book/hash must match |
| `source` | Exact Markdown/PDF SHA-256 and positive one-based printed/PDF evidence pages |
| `identity_review` | `pending` or `confirmed`; confirmation applies to identity only |
| `mechanical_review`, `dependency_review` | `pending` in this initial contract; numerical acceptance needs its later review/evidence contract |
| `automation` | `not-implemented` or `partial`; full automation is deliberately unavailable here |
| `tickets`, `dependencies` | Existing implementation ticket names and canonical dependency IDs; unassigned tickets are counted, unresolved dependencies belong in findings |
| `findings` | Nonempty remaining review/implementation findings |

Catalog findings also name the unreviewed corpus areas. New records must be confirmed against prose/tables and original PDFs, with missing options and variants explicitly tracked. Rebuilding the provisional inventory with changed sources invalidates earlier identity evidence until re-reviewed; matching text headings do not carry acceptance across fingerprints.

The application joins this catalog into its coverage response and shows searchable identities separately from provisional sections. It counts zero mechanically reviewed or fully automated entries. Full corpus audit, complete dependency mapping, bounded named content tickets and numerical acceptance remain in 02B and subsequent content slices.
