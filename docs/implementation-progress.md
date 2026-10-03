# Implementation progress

The user approved the work plan and the branch → implementation → review → validation → commit → PR → merge workflow on 2026-10-02.

## Source strategy

Read corrected local `sources-markdown` copies from the source-review workstream and use the pipeline's original PDFs for mechanical verification. Do not mutate either workstream. The initial processed-source inventory is preserved in `characters_unlimited/data/source-snapshots/initial-inventory.json`; the active inventory fingerprints the corrected copies. All 13 original PDF hashes are unchanged. Corrections and syntactic checks do not certify untouched mechanics. Application work proceeds without waiting for later conversions; content work depending on unavailable or ambiguous passages remains explicitly tracked.

South America 2 PDF page 108 / printed page 107 has confirmed damage obscuring Destroyer ’Borg mechanics. The active coverage view records its source-gap marker; `02c-destroyer-borg-source-gap.md` holds that option out of ingestion until an intact source is available. Missing abilities are not interpreted as absent or zero.

## Slices

- 01: Complete, merged in PR #1. Local Rifts Human/Vagabond identity, initial attributes, notes, transactional saves, and reopen path work. Type checking, four application workflow tests, Python/JavaScript syntax checks, and narrow/desktop browser checks pass. Windows GitHub CI also passes.
- 02: In progress, split into 02A (complete, merged in PR #2) and 02B (complete option audit and bounded content tickets). The scan finds 7,053 section candidates in all 13 books; zero candidates are claimed fully automated. Classifying headings is not a completed corpus audit.
- 02A2: Complete, merged in PR #6. Preserves the initial manifest and fingerprints corrected copies with 7,065 provisional candidates and one marked source gap. All 25 checks, both reviews, browser checks, and Windows CI pass. Parent 02B remains open.
- 03: Draft normal-attribute creation, separate game catalogs, and game-aware identity/save support are prepared on `codex/03-heroes-character`. Heroes Unlimited exceptional-die interpretation awaits the user's ruling; the original PDF (printed page 15) confirms the uncapped wording. Do not publish this slice as complete before resolving that rule. Its owned draft files are preserved in a named Git stash while independent Rifts work proceeds.
- 04: Rifts generation options are complete as 04A, merged in PR #3. Ten workflow tests, browser verification, independent reviews, and Windows CI pass. The full two-game slice remains dependent on 03.
- 05: In progress. Named slice 05A is merged in PR #4 and covers domestic selections and their percentage/quality rules. Sixteen checks, browser verification, independent reviews, and Windows CI pass. Remaining categories, required choices, I.Q. modifiers, and prerequisites are tracked as the follow-on 05B. Parent 05 stays open.
- 06–24 and corpus content batches: Not complete.
- 18: Split into 18A (portable Rifts saves, independent duplicates, exact supported rules, and atomic backups) and 18B (accepted-version archives and explicit upgrade previews). 18A is complete and merged in PR #5; 23 checks, browser validation, both reviews, and Windows CI pass. Parent 18 stays open.
- 18B1: Complete, merged in PR #7. Exact saved versions govern generation, skills, and portable definitions; changing a default does not change a saved pin. All 30 checks, both reviews, browser reopening, and Windows CI pass.
- 05B1 / 18B2: Complete, merged in PR #8. I.Q. bonus chart and domestic-only explicit correction pass both reviews and Windows CI. Version 1.1.0 applies the bonus once, including beyond-30 intervals; 1.0.0 stays accepted for older saves. Preview/cancel/apply, pre-update backups, stale/failure handling, and portable pins pass 34 checks and browser verification. Other 05B and full 18B cases remain pending.

- 05B2: Complete, merged in PR #9; 39 checks, both reviews, browser verification and Windows CI pass. Reviewed Vagabond language, pilot and repair choices, required grants, Eyeball/Streetwise synergies, and both horsemanship percentages use domestic 1.2.0. Older definitions remain accepted with explicit upgrade previews. Begging, combat choices, remaining categories, conditional effects, and parent 05B stay open.

- 02B1: Complete, merged in PR #10; 47 checks, both reviews, browser verification and Windows CI pass. Source-bound canonical identity records cover 30 core-list O.C.C. names, with aliases and source/candidate links. Mechanical/dependency review, complete corpus identities and named content-ticket fan-out stay pending; unassigned identities remain visible.

- 02B2: In progress. Canonical source identities expand to 51 entries across the games, with explicit shared hatchling and Psi-Stalker links. No numerical acceptance or builder activation is claimed.

## Pending source ruling

Heroes Unlimited Second Edition adds a die to an initial 16–18 and says to roll again on another six without stating a terminal cap; Rifts explicitly caps at two bonus dice. An asynchronous question asks the user to choose repeated bonus sixes or a two-bonus-die cap. The original PDF page was visually inspected; do not infer approval from elapsed time or silently copy the Rifts cap.

## Retrospective

Perform the requested retro only after all slices are completed. Compare functionality, visual/media outcomes, and intent with the original ticket plan and record the final assessment in Markdown. Do not label a partial implementation as the completed retrospective outcome.
