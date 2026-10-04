# Implementation progress

The user approved the work plan and the branch → implementation → review → validation → commit → PR → merge workflow on 2026-10-02.

## Source strategy

Read corrected local `sources-markdown` copies from the source-review workstream and use the pipeline's original PDFs for mechanical verification. Do not mutate either workstream. The initial processed-source inventory is preserved in `characters_unlimited/data/source-snapshots/initial-inventory.json`; the active inventory fingerprints the corrected copies. All 13 original PDF hashes are unchanged. Corrections and syntactic checks do not certify untouched mechanics. Application work proceeds without waiting for later conversions; content work depending on unavailable or ambiguous passages remains explicitly tracked.

South America 2 PDF page 108 / printed page 108 has confirmed damage obscuring Destroyer ’Borg mechanics. The active coverage view records its source-gap marker; `02c-destroyer-borg-source-gap.md` holds that option out of ingestion until an intact source is available. Missing abilities are not interpreted as absent or zero.

## Slices

- 07B2: Complete, merged PR #66 as aa55eea after both Windows workflows passed. Power Kick doubles base dice and adds damage bonuses once for source-permitted styles; two-action variants and learned Karate kicks preserve exact rule pins. Other combat coverage remains open.
- 09A1: Complete, merged PR #67 as ec35d84 after both Windows full/frozen workflows passed. HU Mutant starting power outcome/count foundation supports rolled or chosen outcomes, retained D4 dice/history and exact pins, portable saves, builder and editable PDF. Individual powers/effects and remaining parent09 requirements remain open.

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

- 06E: Complete, merged in PR #37 after both independent reviews and both Windows frozen checks passed. Supported Heroes Secondary selections add category guidance, education allowances and remaining counts, I.Q. without scholastic bonuses, shared-grant reconciliation, retained exceptions and portable exact pins under program rules 1.3.0. All 137 local checks and browser selection/reopen/removal pass; The remaining Secondary catalog and parent 06 stay open.

- 06F: Complete, merged in PR #38 after both independent reviews and both Windows frozen checks passed. Computer fixed grants and explicit Repair/Radio choices introduce source-declared program choice groups under immutable rules 1.4.0, adding six definitions (14 total), distinct choice counts, retained exceptions, labeled dual/context checks and compatible portable records. All 143 local checks and browser select/remove/reopen pass; Both review axes approve and publication is complete. Technical/Science interpretation, other catalogs and parent 06 remain open.

- 06G: Complete, merged in PR #39 after both independent reviews and both Windows frozen checks passed. Communications fixed grants and all nine category alternatives add six definitions (20 total) under immutable program rules 1.5.0. Source contexts, Optic/Video synergy, Secondary Video, exact upgrades and browser select/remove/reopen pass 148 local checks. Both review axes approve and publication is complete. Duplicate fixed-grant credit awaits interpretation; parent 06 remains open.

- 06H: Complete, merged in PR #40 after both independent reviews and both Windows frozen checks passed. First Aid and Holistic Medicine add two definitions (22 total) and source Medical Secondary eligibility/costs under immutable program rules 1.6.0. Source-driven picker/list costs, explained percentages, retained excess/duplicates and exact updates/imports pass 151 local checks and browser verification. Full education and corpus remain open.

- 05B8: Complete, merged in PR #41 after both independent reviews and both Windows frozen checks passed. Reviewed Athletics and Body Building introduce recorded acquisition dice, additive attribute modifiers and ordinary defensive bonuses under immutable Rifts skills 2.0.0 (69 entries). S.D.C. bonuses remain separate from pending starting totals. Exact pins, portable histories and compatible updates retain dice; numerical changes to acquired Physical definitions require a separate migration. All 158 local checks, browser selection/remove/reselect and rendered editable PDF inspection pass. Parents 05, 07, 18 and 20 remain open.

- 07C: Complete, merged in PR #42 after both independent reviews and both Windows frozen checks passed. Immutable Rifts skills 2.1.0 adds explicit, one-time HP/S.D.C. generation, effective starting P.E. snapshot (user interpretation accepted 2026-10-03), Physical S.D.C. accumulation, manual resource values and fixed Vagabond saving/Perception contributions. Old pins and generated dice remain intact; changed generated-resource definitions require a separate migration. All 162 local checks, browser generation/edit/reopen, rendered editable PDF inspection and frozen Windows import/reopen passed. Other resources, Perception modifiers, advancement and full corpus remain open.

- 02B11: Complete, merged in PR #43 after both Windows checks passed. The current 718-identity audit now has 510 bounded owning content tickets, retaining the existing Vagabond owner and adding 509 named children with source evidence, aliases, prerequisite owners and actual source-gap blockers. Ownership never accepts mechanics: review and automation states remain unchanged. All 164 local checks, browser coverage/search inspection and both review axes pass. Frozen Windows coverage verifies the bundled map; supporting-rule census, full dependency review and parent 02 remain open.

- 05B9: Complete, merged in PR #44 after both Windows frozen checks passed. Immutable Rifts skills 2.2.0 adds Physical Labor and Running (71 definitions), once-only acquisition dice, P.E./Spd/S.D.C. effects and current Running distance limits. Running is Secondary eligible; Physical Labor retains Secondary exception guidance. Starting HP keeps its original effective P.E. contribution. All 166 local checks, both independent review axes, browser selection/edit/remove/reselect/reopen and rendered editable PDF inspection pass. Other Physical skills, universal movement and advancement remain open.

- 05B10: Complete, merged in PR #45 after both corrected Windows checks passed. Immutable Rifts skills 2.3.0 adds Boxing (72 definitions), recorded S.D.C. dice, P.S. and ordinary defensive bonuses, plus one attack per melee. The natural-20 knockout condition appears in builder/PDF notes. All 168 initial local checks, independent Standards/Spec reviews, browser remove/reselect/reopen and rendered editable PDF inspection pass. Other fighting techniques and progression remain open.

- 08A: Complete, merged in PR #46 after both Windows frozen checks passed (37144659491 and 37144662103). Immutable Rifts equipment 1.0.0 adds Wilk's 320/447 weapons and Plastic-Man armor through purchases, funds, quantities, shot counts, equip/storage, source combat explanations and editable PDF fields. Exact pins/portable inventory and protected optimistic actions retain exceptions and reject invalid writes. All 172 local checks, both independent review axes after the PDF snapshot repair, browser workflows and rendered PDF inspection pass. Starting class equipment, ammunition purchases, broader items and parent 08 remain open.

- 18C: Complete, merged in PR #47 as 052eeab after both Windows frozen checks passed (37145797602 and 37145801884). Exact catalog corrections are displayed with their inventory and attack effects, all changed pins apply atomically after backup, and incompatible inventories remain unchanged. Parent 18 stays open.

- 08B1: Complete, merged in PR #48 as babb040 after both Windows checks passed (37146924086 and 37146927753). Reviewed Vagabond starting credits and saleable goods use immutable equipment 1.1.0. Once-only original dice, exact pins, balance addition and portable/PDF projection preserve goods separately. Starting gear and parent 08 stay open.

- 08B2: Complete, merged in PR #49 as 37bcb4d after both Windows frozen checks passed (37148507938 and 37148513086). All 184 local checks and rendered editable PDF/browser inspection pass. Independent Standards review approved; Spec integration review approved after receipt display repair, with root source review of the delegated module/pack. Fixed Vagabond personal gear uses immutable equipment 1.2.0. Free one-time grant, retained original receipts, editable generic possessions, unspecified values and incomplete carried weights are explicit. Choice-based gear and parent 08 stay open.

- 08C1: Ordinary large/small knives, source purchase ranges and held-knife melee projection implemented under equipment 1.3.0; complete in PR #50, squash 045866f, after both Windows checks passed (37150187267 and 37150183497). All 188 local checks pass, with browser/PDF validation and review approvals. Full starting choices and parent 08 remain open.

- 08C2: Standard short E-Clips with source price ranges, scoped compatibility, ammunition-preserving exchanges and quantity-preserving split UI implemented under equipment 1.4.0; complete in PR #51 as5b4fa49 after Windows checks37151425759/37151429347 passed. All 191 local checks pass. Other ammunition/recharge, class starting choices and parent 08 remain open.

- 08B3A: Representative free Vagabond armor/gun/knife/transport/spare-clip choices implemented under equipment1.5.0, with original receipt retention and explicit missing transport/broader catalog mechanics. Complete in PR #52 as53b8f66 after Windows checks37153441547/37153445623 passed. All193 local checks, both review axes and browser/PDF verification pass; parent08 stays open.

- 21A: Tailored Heroes Unlimited editable sheet for reviewed identity, attributes, education and program/Secondary skills implemented. Exact rule pins, original selections/allowances, Unicode and matching continuations retained; pending powers/combat/resources/equipment blank. Complete in PR #53 as7140443 after Windows checks37154597569/37154600287 passed. All196 local checks, separate review approvals and native/browser PDF verification pass; full ticket21 remains open.

- 05B11: Swimming mixed Physical/percentile projection, source storm/armor contexts and P.S./P.E. activity limits implemented under immutable skills2.4.0. Complete in PR #54 as2f0fdaf after Windows checks37155722512/37155725162 passed. All199 local checks, separate review approvals and browser/PDF inspection pass; overlapping conditions/buoyancy, further Physical rules and parent05 remain open.

- 19A: First Human/Vagabond advancement from1to2 implemented under immutable skills2.5.0. XP/direct/create2, per-skill learned levels, allfour current Hand to Hand/five weapon proficiency increments, Martial Arts strikes, recorded HP gain, complete snapshots, atomic undo/recovery and exact historic pins are supported. Merged in PR #55 as 226c3d1 after Windows checks 37158295005/37158298354 passed. All 205 local checks, separate review approvals and browser/PDF inspection pass; later levels, special paths and parent19 remain open.

- 19B: Human/Vagabond XP/direct/create progression through15 under skills2.6.0, per-level HP/cache/flat historical snapshots, new skill allowances, earned combat/W.P. tables, equipped effects and editable conditional notes implemented. Earlier learned-level combat choices support completing higher-level creation. Complete in PR #56 as4a12a74 after Windows checks37160859638/37160862556 passed. All216 local checks, mypy74, separate reviews and browser/PDF verification pass. Full attack resolution, other paths and parent19 remain open.

- 07B1: Current four ordinary Hand to Hand styles gain source natural-roll conditions, Knee/Body Flip, Martial sweep/trip and native condition/Leap fields under immutable skills2.7.0. Local218 and focused19 checks, mypy75, both independent reviews and browser/render/edit/reopen verification pass; Windows frozen checks precede merge. Parent07 and full combat resolution remain open.

- 07B1 merged PR57 as32539cc after corrected Windows runs37162757164/37162760399 passed full and frozen checks. Parent07 remains open.
- 05C1: Declarative required percentile skill groups and catalog-driven controls in progress; City Rat preparation is recorded in docs/required-skill-groups-contract.md. No additional O.C.C. is activated yet.

- 05C1: Complete in PR #58 as864ccc5 after Windows checks37164049347/37164051385 passed all222 and frozen validation. Declarative required groups, legacy updates and browser autosave/reopen passed both review axes.
- 05C2: Human City Rat foundation in progress; full O.C.C. review remains pending. Scope and open dependencies are recorded in docs/city-rat-contract.md.

- 05C2: Complete in PR #59 as3fcd2c5 after Windows full/frozen runs37166246403/37166240913 passed. Local227 tests, mypy80, both review axes and browser/render/edit/reopen pass. City Rat remains partial, with full mechanics and parent tickets open.
- 05C3: Source-defined optional skill selection costs in progress; City Rat Paramedic consumes two Related slots under new immutable skills2.10.0. Physical/Rogue minimum interpretation remains pending user response.

- 05C3: Complete in PR #60 as4ac78d3 after corrected Windows full/frozen runs37167359410/37167357481 passed. Local229 tests, both reviews and browser/render/edit/reopen pass. Physical/Rogue minimum remains independent pending interpretation.
- 08B4: City Rat starting credits and separate Black Market item value in progress under equipment1.6.0; equipment/cybernetics and parent08 remain open.

- 08B4: Complete in PR #61 as40def5c after both Windows full/frozen checks passed. Original City Rat credits/item value, exact pins and editable sheets verified.
- 08B5: City Rat six-row fixed personal gear grant in progress; full class/equipment review remains open.

- 08B5: Complete in PR #62 as8b9a3d2 after both Windows full/frozen workflows passed.
- 08D1: Core Urban Warrior/Huntsman light armor and explicit environmental status/notes in progress. Full equipment and contextual resolution remain open.

- 08D1: Complete in PR #63 asa6b2f09 after both Windows workflows passed.
- 08B6: Independent City Rat starting armor group in progress; original receipts remain separate from current inventory.

- 08B6: Complete in PR64 as6545e0f after both Windows workflows passed.
- 08B7: Free City Rat starting knife in progress; other weapons and equipment remain open.

- 08B7: Complete in PR65 ase670451 after both Windows workflows passed.
- 07B2: Source-permitted Power Kick in progress with user-confirmed base-dice doubling and bonuses once.

- 09A2: Chosen Extraordinary Mental Affinity, retained acquisitions, trust/intimidate chart and supporting Pick Pockets/Seduction percentages implemented. User confirmed keeping the higher calculated M.A. Source-defined power floor, exact pins, portable history, browser and editable PDF verified. Parent09 and full corpus acceptance remain open; Windows validation pending.

- 09A2: Complete in PR68 as8c37ee4 after Windows full/frozen workflows37177547682/37177550490 passed.

- 09A3: Chosen Extraordinary Mental Endurance, named saving contributions/targets and explicit compatible power-pack updates implemented. Source, browser and editable PDF verified; both review axes approve. Local261 tests pass (one frozen-only skip), mypy93 files, compile/JavaScript checks pass. Windows checks pending; parent09 remains open.

- 09A3: Complete in PR69 asa14be97 after both Windows full/frozen workflows37178847318/37178849111 passed.

- 09A4: Chosen Extraordinary Physical Beauty and supporting Palming under immutable power1.2/skills1.8 implemented. Higher-target, separate charm chart and named skill bonuses/source synergies verified in public worked examples; independent review and full/browser/PDF validation pending. Parent09 remains open.

- 09A4: Both review axes approve after Secondary guidance repair. Final 266 local tests pass (one frozen-only skip), strict mypy94, compile/JS checks, browser remove/reselect and three-page editable PDF verification pass. Windows PR checks pending; parent09 remains open.

09A4 merged in PR70 as34ef6c59d84ad6dbd5a1089afb96fdd1e462bb8c after Windows37180579805(5m4s)/37180582307(5m39s) passed, including packaged executable validation.

- 09B: Five reviewed Heroes Rogue Secondaries implemented in immutable skills1.9. Latest user interpretation grants Concealment M.A. bonus. Both reviews approve; final 271 local tests pass (one frozen-only skip), strict mypy95, compile/JS checks, browser recalculation and three-page editable PDF verified. Windows checks pending; parent09 remains open.

09B merged in PR71 as43d097b04d23c07f055aa5568939070a8b90b389 after Windows37181451825(5m44s)/37181454551(5m45s) passed, including packaged executable validation.

- 09C: Human Mutant starting HP, base S.D.C. and general P.P.E. implemented with independent exact resource pins and retained initial P.E. Both reviews approve; final277 local tests pass (one frozen-only skip), required mypy96 files, compile/JS checks, browser edits/reopening and four-page editable PDF verified. Windows checks pending; parent09 remains open.

09C merged in PR72 as ab45fca533753bb52425c085b68910ca51613f12 after Windows37183026472(6m12s)/37183044312(7m46s) passed, including packaged executable validation.

- 06I: Ventriloquism, Art, Photography and General Repair/Maintenance added under immutable skills1.10. Exact half-proficiency, reversible M.A. contribution and legacy update verified. Both reviews approve; final280 local tests pass (one frozen-only skip), required mypy97, compile/JS checks, browser and three-page editablePDF inspected. Windows checks pending; parent06/09 open.

06I merged in PR73 as c9fa7185ca605bb69e25f2f562d0a2e4685d4dd3 after Windows37184169547(6m15s)/37184175254(6m20s) passed, including packaged executable validation.

- 06J: Body Building & Weight Lifting and Running added under immutable skills1.11 with retained Physical receipts, reversible attributes and S.D.C., initial effective P.E. HP snapshot, portable history, separate UI/PDF summaries and full-definition Heroes upgrade protection. Both reviews approve after outside-group grant and Rifts compatibility repairs. Required mypy99, focused15, compile/JS checks and browser/three-page editable PDF verification pass. Final full suite290 tests passes (one frozen-only skip); Windows checks pending. Parent06/07/09 remain open.

06J merged in PR74 as a978688502364058f08f8063cbd4785856f561f7 after Windows37185966456(6m24s)/37185962664(7m36s) passed, including packaged executable validation.

- 09D: Extraordinary Physical Endurance implemented under immutable powers1.3: additive P.E., retained multi-formula HP/S.D.C. receipts including confirmed level1D4, ordinary P.E. saves/fatigue and independent resource projection. Focused40 and required mypy100 pass; compile/JS/whitespace, browser and four-page editablePDF verification pass. Both reviews approve; full297 tests pass (one frozen-only skip); Windows pending. Heroes advancement and parent09/07 remain open.

09D merged in PR75 as107218415f4319d32a3ed0d05f835ec1504f81ee after Windows37187385452(4m34s)/37187383195(5m45s) passed, including packaged executable validation.

- 06K: Heroes ordinary Human level-one combat and Basic training added under immutable skills1.12. Exact pins, retained acquisitions, duplicate effects, action costs and independent attribute-range guards verified. Both reviews approve after fixed-training and unsupported-contribution repairs. Final303 local tests pass (one frozen-only skip), mypy102, compile/JS/whitespace checks and browser/three-page editable PDF verification pass. Windows checks pending; parent06/07/09 remain open.

06K merged in PR76 as14b19cf49d75b3ec8a6bb10994988eb30b6a4467 after Windows37189357106(4m20s)/37189359767(5m4s) passed, including packaged executable validation.

- 06L: Heroes Expert, Martial Arts and Assassin added under immutable skills1.13, with explicit active-training choice, non-stacking costs/profiles, reversible retained acquisitions and portable validation. Both independent reviews approve after removed-source disclosure repair. Focused training5/Basic5/HTTP7, required mypy104, compile/JS checks and browser/four-page editable PDF verification pass. Final full308 tests pass (one frozen-only skip); Windows pending. Parent06/07/09 remain open.

06L merged in PR77 as403b9233cff76c24d202e93ac58cf113d3114390 after Windows37190505307(6m40s)/37190507594(6m23s) passed, including packaged executable validation.

- 06M: Heroes Climbing/Rappelling and Swimming added under immutable skills1.14. Separate percentile checks, retained Physical receipts, independent effective pace/endurance and fatigue sources verified. Both reviews approve after exact-duration range repair. Full314 local tests pass (one frozen-only skip), required mypy105, compile/JS/whitespace and browser/four-page editable PDF verification pass. Windows pending; parent06/07/09 remain open.

06M merged in PR78 as fe6896d07c91386be4035e1af4439d8de4d94379 after Windows37192051111(6m27s)/37192053664(6m51s) passed, including packaged executable validation.

- 06N: Athletics added under immutable skills1.15 with retained dice and reversible combat/resource effects. Hybrid Physical percentile upgrade comparison repaired. Both reviews approve; focused20/full318 tests pass (one frozen-only skip), required mypy106, compile/JS/whitespace and browser/four-page editable PDF checks pass. Windows pending; parent06/07/09 open.

06N merged in PR79 as b17ecea00ef1e72100f3bd96d27621e284d2b653 after Windows37192953719(8m29s)/37192957051(8m0s) passed, including packaged executable validation.

- 06O: S.C.U.B.A. added under immutable skills1.16 with separate underwater pace, proficiency, prerequisite honor warning, retained empty receipts and fatigue source. Both reviews approve; focused21/full322 tests pass (one frozen-only skip), required mypy107, compile/JS/whitespace and browser/four-page editable PDF checks pass. Windows pending; parent06/07/09 remain open.
