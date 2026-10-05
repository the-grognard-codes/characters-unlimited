# 05D1: Rifts Rogue skill validation

Desktop continuation resumed by the user on 2026-10-05 from main `8df0c8fc8a4906ef34029fa7750f0d1c40a667ab`. New immutable Rifts skill archive 2.13.0 adds the 17 Rogue checklist identities, with shared normal attribute/synergy calculations, existing class entitlements, portable state and editable sheet descriptions. Old accepted archives are unchanged.

## Original source review

Read the Rogue descriptions in the supplied pipeline Markdown, then visually checked original PDF printed pp.320-321 (PDF323-324). The scan restores Cardsharp's omitted right-column continuation and Imitate Voices' damaged dual percentage. Also checked printed pp.309 (Pick Locks/Pockets),317 (Prowl),322 (Artificial Intelligence bonus),300 (Secondary restrictions),88-89 and97-98 (class skills and entitlements). Source files remain outside the creator checkout at `../rpg-docling-pipeline/data/processed/Rifts - Ultimate Edition.md` and `../rpg-docling-pipeline/data/raw/Rifts - Ultimate Edition.pdf`; ingestion output was not edited.

| Skill | Base / per attained learned level | Printed pages |
| --- | --- | --- |
| Cardsharp | 24 / 4 | 320 |
| Computer Hacking | 20 / 5 | 320 |
| Concealment | 20 / 4 | 320 |
| Find Contraband | 26 / 4 | 320 |
| Gambling (Standard) | 30 / 5 | 320 |
| Gambling (Dirty Tricks) | 20 / 4 | 320 |
| I.D. Undercover Agents | 30 / 4 | 320-321 |
| Imitate Voices & Sounds | 42 and36 / 4 | 320-321 |
| Palming | 20 / 5 | 321 |
| Pick Locks | 30 / 5 | 309,321 |
| Pick Pockets | 25 / 5 | 309,321 |
| Prowl | 25 / 5 | 317,321 |
| Roadwise | 26 / 4 | 321 |
| Safe-Cracking | 20 / 4 | 321 |
| Seduction | 20 / 3 | 321 |
| Streetwise | 20 / 4 | 321 |
| Tailing | 30 / 5 | 321 |

Interpretations: overlapping Cardsharp/Palming +4/+5 bonuses use the larger +5 once; both Gambling forms qualify for the Secondary list's generic Gambling entry and Vagabond Eyeball bonus. Seduction's Cardsharp/Sing/Dance bonuses affect normal proficiency; its victim-specific theft bonus remains descriptive. Prowl has one shared Rogue identity for these two classes. Roadwise has an editable regional specialty and descriptive customary class restriction. Safe-Cracking's Locksmith/Mechanical Engineer synergies are declared, but those catalogs remain unavailable; Hacking's conditional electronic-lock bonus and Imitate Voices' Impersonation bonus remain descriptions until those target catalogs are supplied. City Rat's three Physical/Rogue related-choice guidance remains an existing limitation; this batch does not certify either complete class.

## Independent expected witnesses

Vagabond Cardsharp with Palming, Dirty Tricks and Seduction:24+4 class+10 Eyeball+5 Palming+6 Dirty Tricks+5 Seduction=54. I.D. grant with Streetwise and duplicate Find Contraband:30+10 class+10 Eyeball+10 Streetwise+10 Find Contraband=70, with each synergy once. City Rat's Tailing grant with Prowl:30+20 class+5 Prowl=55; optional Prowl is25+15=40. Basic Mathematics grant with Standard Gambling:45+10 class+5 Gambling=60.

Seduction at M.A.24/P.B.23 with normal Vagabond related/Eyeball bonuses:20+4+10+4+3=41. M.A.20/P.B.18 gives35 (P.B. rounds up). Safe-Cracking at M.E.14 is20+4-10=14; M.E.15 gives24. Pick Locks first learned at level3 with Safe-Cracking:30+4+5=39, then44 at character level4. Effective I.Q. and the shared98% cap continue to apply.

Eleven new public workflow tests pass, covering the complete source identity/base/rate table, thresholds/caps, synergy deduplication, grants, prerequisites, late acquisition, reopening, portable import, old exact pins, update previews, malformed declarations and editable fields. Four additional witnesses cover fixed-grant attribute contributions and rejection before save/import/export when combined normal bonuses exceed the exact integer range, including attributes edited before learning and an explicit earlier learned level. The focused Rogue/owned-profile run passes14 tests; typing164, compileall and all browser JavaScript syntax pass. Final full regression, independent Standards/Spec review and exact-head Windows/frozen CI remain pending.

Actual Chrome interaction created `Rogue catalog proof`, filtered all17 Rogue choices and saved Cardsharp, Palming and Seduction. UI observed38% Cardsharp, then43% with Palming and48% with Seduction; Palming28%, Seduction39% including M.A.25's +5. The expanded UI shows attribute contributions and source descriptions. Proof: `05d1-rogue-builder.png`. The same public application's PDF export has4 pages and1205 editable fields, including the skill descriptions/attribute contributions: `05d1-rogue-sheet.pdf`.

## Desktop operation

Python3.14.7 project venv, project-local Node22.23.2 and Poppler25.07 are provisioned. `gh` authentication works in the user's ordinary process; the sandbox account cannot access the same keyring. A reversible hidden Python helper in ignored `tmp/keep-awake.py` holds Windows system/display execution requests. Screen saver was already off. Create `tmp/keep-awake.stop` to release the guard; it restores any screen-saver state it temporarily changed. It does not change security policy or prevent a manual lock/sleep.

No new unattended schedule is configured: scheduling tools are absent and native desktop control reports its connection unavailable. The old machine's schedule remains recorded as paused. Continue in this checkout with one writer; finish this PR's exact-head validation before starting another product slice. The full amended build and final retrospective remain incomplete.
