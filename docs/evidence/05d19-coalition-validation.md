# 05D19 Coalition Grunt and SAMAS / Elite RPA pilot validation

Human creation profiles use new immutable core 1.10.0, skills 2.31.0 and equipment 1.18.0 archives. Existing declarations and historical accepted bytes are unchanged. The skills catalog contains 210 identities. Canonical class owners remain open for wider race, equipment and required robot/bionic construction delivery.

## Source and behavior

Original Rifts Ultimate Edition scans were checked against the completed Markdown: printed 233–235 (PDF 236–238) for classes, 257–261 for issued equipment, 240/249 for SAMAS, 295 for XP, and 351–352 for conditional robot training. The source pipeline was read only.

- Grunt grants native American 92%, source skill bonuses, Body Building/Running, conditional Basic robot training, seven Related and five Secondary choices. Related awards occur at 2/5/9/12; Secondary at 4/8/12. Salary is a retained, no-dice 1700-credit receipt.
- SAMAS grants native American 94%, pilot/technical bonuses, Running and conditional Basic/Elite SAMAS training. Domestic Related training retains −5%. Eight Related and four Secondary choices grow by two Related at 3/6/9/12 and one Secondary at 4/8/12/15. Salary is 2000 credits without dice.
- Both have fixed Energy Pistol/Rifle and one combined elective proficiency. Expert is free; Martial Arts/Assassin consumes two Related choices. Fixed/elective overlap does not pay twice. Eligibility and Assassin alignment remain visible honor-system guidance. Grunt's source Basic robot training does not invent a free Robot Pilot prerequisite.
- Issued personal gear, armor, grenades, weapons and four matching spare clips per energy weapon retain original receipts separately from editable possessions. Grunt does not receive an automatic mission vehicle. SAMAS assignment and daily transport are separate stored possessions; they do not replace Human attributes or resources.
- Grenades remain weapons with descriptive damage/range/blast rules, manually edited quantities, no shot counter, no reload eligibility and no fabricated attack totals. Strict inactive-declaration preflight rejects unsupported gun fields before dice or import writes.
- CA-1/CA-2 retain five-hour oxygen and source price ranges. C-18 uses 2D4 M.D.; C-10 retains conditional targeting and exact failure descriptions. C-12 ordinary attacks use 2D6 M.D.; alternative burst and S.D.C. settings remain readable descriptions. The sheet no longer prints literal `None/None` or an unspecified armor price as `None`.

## Independent checks

Six class tests cover deterministic starting values, full source XP/award progression through level fifteen and undo/import, shared proficiency and paid-style costs/provenance, negative Domestic bonuses and repeat/growth behavior, fixed salary/issued equipment/clip capacities, and stored SAMAS isolation. Two descriptive-weapon tests cover invalid inactive declarations and editable quantities/import/PDF without invented gun mechanics.

With a die result of 3, Grunt P.S./P.E./Speed are 11/10/21, S.D.C. 31 and HP 13; pilot values are 9/10/21, S.D.C. 21 and HP 13. Source Cook/Electronics/Field Armorer/Airplane percentages are 35/30/55/55 versus 30/35/50/65. At level three, a Secondary Cook repeat legitimately supplies the stronger zero class modifier once, producing 55% across both acquisitions.

The first full run exposed an older pilot-catalog assertion that treated nonpercentile robot training as percentage skills. The assertion now retains its exact ordinary-pilot map while excluding training; all nine pilot checks pass in 38.747s and both focused reviews approve. Product and packaged/PDF artifacts are unchanged.

Final affected checks: 25 tests pass in 114.918s. After source/PDF review repairs, three equipment checks pass in 20.442s; the final C-12 wording/PDF check passes in 9.200s. Final mypy checks 195 files; compileall, every browser script under project Node 22.23.2 and whitespace checks pass. Final Windows build completes in 14.977s; its isolated frozen workflow passes in 66.788s.

## Actual packaged browser witnesses

Created through Chrome against the final Windows executable, using isolated local data. Mutation receipts were read after asynchronous saves settled. Both records reopened through the library after a browser reload; a separate public application with a die function that rejects any roll verified exact portable import/reopen and retained dice.

| Witness | Save / level | Retained behavior |
| --- | --- | --- |
| Avery — Coalition Grunt source witness | a35d1c9e-c71a-4984-ab60-bffd03305b8f / revision 30 / level 3 | All Related/Secondary and proficiency choices complete; 1700 credits; Cook 45%; Photography learned at level 3; CA-1 equipped; C-12 equipped with 7 remaining shots; grenade quantity manually reduced to 1, original grant remains 2; four pistol clips at 10 and four rifle clips at 20 shots. |
| Jordan — Coalition SAMAS source witness | d5c72f0f-52af-447d-abd6-c92bbebf1691 / revision 29 / level 3 | All choices complete; 2000 credits; Martial Arts costs 2 Related; initial Cook 30%, Electronics 35%, Field Armorer 50%, Airplane 65%; repeated Cook 55%; explicit fixed IQ 10 retains original base/dice 7; CA-2 equipped; SAMAS and daily hovercycle stored independently; two plasma grenades. |

Browser screenshots: [Grunt skill calculation](05d19-grunt-skills.png), [reopened rifle](05d19-grunt-weapon-reopened.png), [pilot skill calculation](05d19-samas-skills.png), [stored SAMAS](05d19-samas-stored-equipment.png), [reopened pilot](05d19-samas-reopened.png).

## Editable sheets and remaining gates

[Grunt editable sheet](05d19-coalition-grunt-sheet.pdf): 8 pages, 1491 canonical fields, 493 populated widgets. [Pilot editable sheet](05d19-coalition-samas-pilot-sheet.pdf): 9 pages, 1548 canonical fields, 548 populated widgets. Every populated widget agrees with the canonical value and has a nonempty normal appearance stream. Armor COST is 35000–45000; source notes, retained learning ages, weapon settings, grenade quantities and stored SAMAS traits are present. All 17 pages render and pass visual review without clipped or overlapping values or continuation text. Poppler reports missing optional Symbol/ArialUnicode display fonts; the actual populated values and source descriptions render legibly.

Both code/source and final artifact/snapshot review axes approve with no actionable findings, including the actual PR130 parent merge receipts. Stable final regression passes 655 tests in 2118.653s with one frozen-only skip covered by the separate 66.788s final frozen workflow. Exact-head hosted Windows/full/frozen gates precede merge. No merge or full-build completion is claimed here.

05D19 done. PR131 merged as `91db8278622fcdb2133a31f473c3971a67e5c11b` at 2026-10-06T18:53:48Z; reviewed head `ce30734da5c67a054b32da3a7d6409c5e0f17ff4`. Both independent review axes approve. Exact-head push37507200035 passes655 tests in3154.952s/frozen94.101s; PR37507210521 passes655 tests in3257.757s/frozen99.980s. Both pass typing195, static checks, Windows packaging and artifact upload. Local655 tests2118.653s/frozen66.788s and actual packaged/portable/all17-page editable PDF acceptance pass. Wider class/race/RCC, magic/Heroes, equipment, saved identity revision and robot/bionic construction requirements remain open; the full amended build is incomplete.
