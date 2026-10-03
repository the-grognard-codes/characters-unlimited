# Implementation progress

The user approved the work plan and the branch → implementation → review → validation → commit → PR → merge workflow on 2026-10-02.

## Source strategy

Read corrected local `sources-markdown` copies from the source-review workstream and use the pipeline's original PDFs for mechanical verification. Do not mutate either workstream. The initial processed-source inventory is preserved in `characters_unlimited/data/source-snapshots/initial-inventory.json`; the active inventory fingerprints the corrected copies. All 13 original PDF hashes are unchanged. Corrections and syntactic checks do not certify untouched mechanics. Application work proceeds without waiting for later conversions; content work depending on unavailable or ambiguous passages remains explicitly tracked.

South America 2 PDF page 108 / printed page 108 has confirmed damage obscuring Destroyer ’Borg mechanics. The active coverage view records its source-gap marker; `02c-destroyer-borg-source-gap.md` holds that option out of ingestion until an intact source is available. Missing abilities are not interpreted as absent or zero.

## Slices

- 01: Complete, merged in PR #1. Local Rifts Human/Vagabond identity, initial attributes, notes, transactional saves, and reopen path work. Type checking, four application workflow tests, Python/JavaScript syntax checks, and narrow/desktop browser checks pass. Windows GitHub CI also passes.
- 02: In progress, split into 02A (complete, merged in PR #2) and 02B (complete option audit and bounded content tickets). The scan finds 7,053 section candidates in all 13 books; zero candidates are claimed fully automated. Classifying headings is not a completed corpus audit.
- 02A2: Complete, merged in PR #6. Preserves the initial manifest and fingerprints corrected copies with 7,065 provisional candidates and one marked source gap. All 25 checks, both reviews, browser checks, and Windows CI pass. Parent 02B remains open.
- 03: Complete, merged in PR #28; all 104 local checks, both independent reviews and both Windows frozen-build checks pass. Separate Heroes Human-origin Mutant initial attributes, game-specific repeated exceptional sixes, normal mortal ceilings, manual values, rerolls/history, notes, local saves and exact portable bundles work. Source wording resolves the earlier optional interpretation question without inferring a user answer. Education, powers, category modifiers, combat, equipment, advancement and editable Heroes PDF remain pending.
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

## Heroes exceptional-die interpretation

Original printed p. 15 / PDF p. 16 says to roll again on another six, without a terminal cap. The implementation uses that repeated-six interpretation. The draw guard rejects a broken/nonterminating dice source atomically and does not silently truncate a valid roll chain. Independent review and deterministic regressions must verify this behavior.

## Retrospective

Perform the requested retro only after all slices are completed. Compare functionality, visual/media outcomes, and intent with the original ticket plan and record the final assessment in Markdown. Do not label a partial implementation as the completed retrospective outcome.

- 05B6: Complete, merged in PR #18; both Windows CI checks pass. Eleven Science definitions bring the selectable catalog to 57. Navigation prerequisites and once-only math bonus, Archaeology dual checks, History and Computer synergies, pool restrictions and exact portable pins pass 84 local checks and browser explanation verification. Both independent review axes approve; publication is complete. Zoology specialization, Lore targets, alien medical contexts and full category advancement remain pending.

- 20A: Complete, merged in PR #19. Editable Rifts export covers currently supported values, with missing resources/equipment blank and skill/note continuation fields. Original artwork is preserved while shared widget parents, shared appearances and incomplete font encoding are repaired in the exported copy. All 88 local checks pass, including Unicode field editing and save/reopen. Rendered short/long sheets and the browser checklist were inspected; actual browser filesystem delivery remains unverified after a download-event timeout. Both review axes approve after Unicode repairs; merged in PR #19 with both Windows CI runs passing. Actual browser delivery passed during 23A; full parent 20 remains open.

- 23A: Complete, merged in PR #20. The early Windows bundle passes create/reopen, portable import, source coverage, editable PDF and desktop-controller startup from outside the repository without Python or Node on PATH. Edge downloaded and reopened a real PDF. All 89 local checks pass; both review axes approve. Both Windows frozen-build CI checks pass. Full parent 23 and final release acceptance remain open.

- 07B: Complete, merged in PR #21. Reviewed ordinary Human M.E./P.E. saving contributions and I.Q. illusion contributions use skill pack 1.8.0. Low/high values, source explanations, explicit version preview, exact portable saves and editable PDF fields are implemented. All 93 local checks, browser/PDF validation, both reviews and both Windows frozen-build checks pass. Other modifiers and saving targets remain pending; parent 07 stays open.

- 02A3: Complete, merged in PR #22. Original Underseas printed page 131 is absent from the supplied PDF. A separate fingerprint-bound verified gap record survives CLI rescans without mutating books. The active view now exposes two source gaps; Ticonderoga mechanics stay blocked under 02C2. All 95 checks, browser validation, both review axes and both Windows frozen-build checks pass.

- 02B4: Complete, merged in PR #23; both Windows frozen-build checks pass. All 96 local checks and both review axes approve after documentation and source-provenance repairs. Sixty-two South America 1/Underseas identity records bring coverage to 129 confirmed identities and 128 unassigned entries. Original contents/body names and printed/PDF offsets were checked, with race/class and bi-form dependencies retained. Numerical acceptance, remaining variants, complete corpus identities and builder activation remain pending.

- 02B5: Complete, merged in PR #24; all 97 local checks, both review axes and both Windows frozen-build checks pass. Forty Atlantis/Splynn racial, occupational, form and conversion identities bring the catalog to 169; numerical rules, full dependency acceptance and named branch fan-out remain pending. Original contents and selected body headings resolve page and class-label discrepancies.

- 02A4: Complete, merged in PR #25; all 98 checks, both review axes and both Windows package checks pass. Original South America 2 neighbor labels correct the damaged-page locator to printed/PDF page 108. Verified metadata replaces the same passage description without changing source hashes or counting another gap.

- 02B6: Complete, merged in PR #26; all 99 local checks, both reviews and both Windows frozen-build checks pass. Fifty-five Mercenaries/Merc Ops/South America 2 creation identities bring the catalog to 224 across all eight supplied Rifts books. Complete core child paths, NPC-profile racial reconciliation, remaining Heroes books and mechanical/dependency review remain pending.

- 02B7: Complete, merged in PR #27; all 100 local checks and both Windows frozen-build checks pass. Both review axes approve after alias/dependency and documentation repairs; final additive data received self-review because the Standards reviewer reached its thread limit. Forty-seven Powers Unlimited 2 categories, named creation branches, genetic construction and power identities bring the partial catalog to 271. Numerical acceptance and supporting mechanical fan-out remain pending.

- 05B7: Complete, merged in PR #29; all 108 local checks, both review axes and both Windows frozen-build checks pass. Ten Medical definitions add dual and named contextual checks to the 1.9.0 catalog (67 skills), with narrowed source pool rules, prerequisites, mutual synergies, exact pins and PDF rates. Other Medical subsystems and combined contexts remain pending.

- 06A: Complete, merged in PR #30; all 113 local checks, both review axes and both Windows frozen-build checks pass. All twelve Heroes education outcomes support percentile rolls, direct choice, retained history and exact education pack pins. Program slots and bonuses, Secondary/Street allowances and literacy/source guidance are shown. Actual program selection, skills and percentages remain unfinished; parent 06 stays open.

- 02B8: Complete, merged in PR #31; all 114 local checks, both review axes and both Windows frozen-build checks pass. Forty-four Aliens Unlimited racial/branch identities from six original body groups bring the partial catalog to 315. Original offsets, singular/plural aliases and variant/class relationships are retained. No numerical acceptance or automatic builder activation is certified.

- 02B9: Complete, merged in PR #32 after both Windows builds passed. Sixty-nine additional Aliens profiles, branches, generation/shared rules and monster identities bring the partial catalog to 384. Source count reconciliation, supporting mechanical entries, numerical review and content tickets remain pending.


- 06B: Complete, merged in PR #33 after both Windows builds passed. Business program selections and six defined skill percentages (five program grants plus universal Pilot Automobile; Mathematics merges once) work through education, I.Q., saves, portable data and browser projection. Parent 06 remains open for remaining programs and skill choices. A subsequent original-page review identified a High School eligibility correction to deliver through an explicit rule-version update.

- 02B10: Complete, merged in PR #34 after both independent reviews and both Windows builds passed. Powers Unlimited 1/3 and three HU2 shared powers add 334 source identities, bringing the partial catalog to 718 with 717 awaiting named content batches. Aliens count discrepancies and original PDF pagination anomalies remain explicit. Four fingerprint-bound gaps require intact-source recovery under 02C, 02C2, 02C3 and 02C4; no source books were changed. All 126 local checks, original fingerprints and browser verification pass. Parent 02 stays open for full supporting-rule/dependency review and mandatory content-ticket fan-out.

- 06C: Complete, merged in PR #35 after both Windows frozen checks passed. Immutable Heroes program rules 1.1.0 correct High School Business eligibility. Existing pins retain earlier values until explicit preview/apply with a before-update backup. Public workflows, HTTP protection, cancellation, restore, visible warnings and reopen pass 130 local tests and browser verification. Both independent reviews approve; parent 06 remains open.

- 06D: Complete, merged in PR #36 after both independent reviews and both Windows frozen checks passed. Medical Assistant adds five fixed program grants and two source-grounded skills under immutable program rules 1.2.0. Browser catalog selection, shared bonuses, warnings, portable data and exact-pin update checks pass all 133 local tests. Parent 06 remains open.

- 06E: In progress. Supported Heroes Secondary selections add category guidance, education allowances and remaining counts, I.Q. without scholastic bonuses, shared-grant reconciliation, retained exceptions and portable exact pins under program rules 1.3.0. All 137 local checks and browser selection/reopen/removal pass; independent reviews and Windows CI precede merge. The remaining Secondary catalog and parent 06 stay open.
