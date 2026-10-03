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

- 02B2: Complete, merged in PR #11; 49 checks, both reviews, browser verification and Windows CI pass. Canonical source identities expand to 51 entries across the games, with explicit shared hatchling and Psi-Stalker links. No numerical acceptance or builder activation is claimed.

- 05B3: Complete, merged in PR #12; both Windows CI runs pass. Nine reviewed noncombat choices expand the catalog to 18; category-specific bonuses, prerequisites, language specialties and once-only Barter family synergies pass 53 local checks. Browser category selection and explained Barter totals pass; the Spec review approves, and the Standards review identified duplicate specialty detection, now consolidated. Both reviews approve after consolidating specialty detection. Parent 05B remains open.

- 05B4: Complete, merged in PR #13; both Windows CI runs pass. Fourteen reviewed Technical choices bring the selected catalog to 32. Both History checks, subject specialties, literacy prerequisite guidance, Art quality and Research synergies pass 59 local checks and browser verification. Standards approves; Spec caught an Art quality edge case, now repaired with a regression. Targeted Spec re-review approves; both reviews approve after the Art repair.

- 07A: Complete, merged in PR #14; both Windows checks pass. Representative level-one Rifts combat training, action costs and explained melee/firearm bonuses pass 66 checks and browser verification. Both review axes approve after repairing required energy-weapon eligibility, Assassin alignment guidance and the extra-training warning. Parent 07 remains open; the UI identifies the remaining mechanics.

- 04B: Complete, merged in PR #15; both Windows CI checks pass. New Vagabonds record +1D4 M.A., +1 P.S. and +2 P.E. separately under primary 1.1.0. Rerolls preserve class dice, manual fixed/additive modes apply correctly and portable validation rejects altered contributions. All 71 checks and browser explanation/reroll verification pass; both review axes approve after repairing guidance for older skill pins; publication is complete. Earlier primary versions remain unchanged, with random primary-upgrade support still pending.

- 05B5: Complete, merged in PR #16; both Windows CI checks pass. Fourteen Communications choices bring the selectable catalog to 46. Category exclusions, writing repetition/quality, source-grounded conditional checks, grant-aware prerequisites and named specialties pass 78 checks and browser verification. Spec caught missing guidance for optional languages duplicating grants; shared normalization and a regression repair it. Both targeted reviews approve; publication is complete. Source discrepancy and remaining dependencies are recorded in docs/evidence/05b5-validation.md.

- 02B3: Complete, merged in PR #17; both Windows CI checks pass. Sixteen source-bound Heroes Unlimited identities add four Hardware specializations, Super Vehicle construction, five Special Training paths, four robot types and two shared robot rules. There are 67 identities, zero mechanically reviewed entries, and 66 unassigned identities. All 79 local checks and browser alias/dependency validation pass. Both review axes approve; publication is complete. Evidence: docs/evidence/02b3-validation.md.

## Pending source ruling

Heroes Unlimited Second Edition adds a die to an initial 16–18 and says to roll again on another six without stating a terminal cap; Rifts explicitly caps at two bonus dice. An asynchronous question asks the user to choose repeated bonus sixes or a two-bonus-die cap. The original PDF page was visually inspected; do not infer approval from elapsed time or silently copy the Rifts cap.

## Retrospective

Perform the requested retro only after all slices are completed. Compare functionality, visual/media outcomes, and intent with the original ticket plan and record the final assessment in Markdown. Do not label a partial implementation as the completed retrospective outcome.

- 05B6: Complete, merged in PR #18; both Windows CI checks pass. Eleven Science definitions bring the selectable catalog to 57. Navigation prerequisites and once-only math bonus, Archaeology dual checks, History and Computer synergies, pool restrictions and exact portable pins pass 84 local checks and browser explanation verification. Both independent review axes approve; publication is complete. Zoology specialization, Lore targets, alien medical contexts and full category advancement remain pending.

- 20A: Complete, merged in PR #19. Editable Rifts export covers currently supported values, with missing resources/equipment blank and skill/note continuation fields. Original artwork is preserved while shared widget parents, shared appearances and incomplete font encoding are repaired in the exported copy. All 88 local checks pass, including Unicode field editing and save/reopen. Rendered short/long sheets and the browser checklist were inspected; actual browser filesystem delivery remains unverified after a download-event timeout. Both review axes approve after Unicode repairs; merged in PR #19 with both Windows CI runs passing. Actual browser delivery passed during 23A; full parent 20 remains open.

- 23A: Complete, merged in PR #20. The early Windows bundle passes create/reopen, portable import, source coverage, editable PDF and desktop-controller startup from outside the repository without Python or Node on PATH. Edge downloaded and reopened a real PDF. All 89 local checks pass; both review axes approve. Both Windows frozen-build CI checks pass. Full parent 23 and final release acceptance remain open.

- 07B: In progress. Reviewed ordinary Human M.E./P.E. saving contributions and I.Q. illusion contributions use skill pack 1.8.0. Low/high values, source explanations, explicit version preview, exact portable saves and editable PDF fields are implemented. Other modifiers and saving targets remain pending; parent 07 stays open.
