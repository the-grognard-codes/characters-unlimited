# 05D2: Electrical and core Mechanical skill validation

Base: PR113 merge `d330251c18669e1022080dc0c33778a85b5b3237`. New immutable Rifts skill archive2.14.0 reviews13 identities, preserving four existing identities and adding nine. Current catalog99. All five Electrical skills are covered; eight core Mechanical skills are covered. Vehicle Armorer remains a separate source identity requiring its automatic Basic Mechanics grant; neither the full Mechanical category nor robot/bionic construction is certified by this batch.

## Source review

Read the supplied pipeline Markdown and visually checked original Ultimate Edition printed308/312/313 (PDF311/315/316), Secondary printed300 (PDF303), and Surveillance printed305 (PDF308). The Mechanical Engineer OCR is damaged; the original page confirms its base25, +5% per level, Basic or Advanced Mathematics/Basic Electronics/Literacy prerequisites and distinct +5% Locksmith/Surveillance bonuses. Source fingerprints are retained in `electromechanical_review`. Original books and pipeline output remain read-only outside this checkout.

| Identity | Base | Printed page |
| --- | --- | --- |
| Basic Electronics | 30 | 308 |
| Computer Repair | 30 | 308 |
| Electrical Engineer | 35 | 308 |
| Electricity Generation | 50 | 308 |
| Robot Electronics | 30 | 308 |
| Aircraft Mechanics | 25 | 312 |
| Automotive Mechanics | 25 | 312 |
| Basic Mechanics | 30 | 312 |
| Bioware Mechanics | 30 | 312 |
| Locksmith | 25 | 312 |
| Mechanical Engineer | 25 | 312 |
| Robot Mechanics | 20 | 312 |
| Weapons Engineer | 25 | 313 |

All gain5% per attained learned level. Computer Repair exposes separate procedure/actual checks at the same normal percentage. Mechanical Engineer exposes diagnosis, work and verification at the same percentage. Field repairs, unfamiliar technology, restricted installations, heavy-weapon strike and construction activities remain concise descriptions.

Interpretations: Electricity Generation's “at least Basic” electronics/mechanics can be satisfied by the respective Engineer skill; Robot Mechanics' at-least-Basic Mathematics accepts either Basic or Advanced. Other explicitly named Basic Mathematics prerequisites remain named guidance. Electrical Engineer and Mechanical Engineer add their distinct +5% bonuses to Locksmith once each. Surveillance now accepts the source's Electrical Engineer alternative to Basic Electronics; additional Computer Operation/Literacy requirements apply only to complex high-tech systems and remain descriptive. Existing class permissions and bonuses are preserved. Secondary Electrical permits Basic Electronics/Computer Repair and Mechanical permits Basic Mechanics/Automotive Mechanics; other choices remain retainable with guidance and no O.C.C. bonus.

## Independently expected witnesses

At I.Q.12: Locksmith25 +5 Electrical Engineer +5 Mechanical Engineer =35. Duplicate Mechanical Engineer does not add another5; removing it leaves30. Vagabond Surveillance is a retained class exception:30 +5 Mechanical Engineer =35, then30 after removal. Safe-Cracking with M.E.15 is20 +4 Rogue class +4 Locksmith +6 Mechanical Engineer =34, then28 after removing Mechanical Engineer. Existing Rogue grant Eyeball bonuses remain unchanged and applied once.

Vagabond related Basic Electronics/Computer Repair/Basic Mechanics/Automotive Mechanics are35/30/35/30; City Rat35/35/40/35. Secondary values30/30/30/25 have no class bonus. Retained Secondary Electrical Engineer/Robot Mechanics are35/20 with explicit availability/prerequisite guidance. Mechanical Engineer learned at character level3 starts25, reaches30 at character level4, and all three ordinary checks grow together. Exact2.13.0 saves retain90 catalog entries and old check metadata until an explicit upgrade to99 entries.

Five new public workflow tests plus29 affected Rogue, Communications, Medical, owned-profile and upgrade tests pass (34 total,19.215 seconds). Typing165, compileall, all Node22 browser syntax checks and whitespace checks pass. Standards and Spec independently APPROVE final head460b36f7923ef10df1bc46c94bb962c35d995a85. Local full regression passes490 tests in417.368 seconds (one frozen-only skip); the rebuilt Windows executable separately passes its frozen workflow in37.885 seconds. Exact-head hosted Windows/full/frozen runs37377127256 and37377132769 pass490 tests (646.149/631.689 seconds) and separate frozen checks (37.154/36.593 seconds). PR114 merged asa90ddf5f27cc74bec09c08e440a26eb14fb0145a;05D2 is done.

## Actual browser and editable PDF

Created `Machine skills proof` through the public application, then used Chrome to select Locksmith, Mechanical Engineer, Electrical Engineer, Surveillance and Safe-Cracking. The UI observed Locksmith25 ->30 ->35, Surveillance35 and Safe-Cracking34, source descriptions, named contributions and retained class/prerequisite guidance. `05d2-electromechanical-builder.png` shows the expanded Locksmith explanation. No override marker is required.

Exported the same saved character through the public PDF boundary:4 pages and1230 editable fields. `05d2-electromechanical-sheet.pdf` retains normal skill values, Mechanical Engineer's two additional checks, descriptions and source citations. Original continuation pages3/4 were rendered and visually inspected for readable content without clipping; page3 is `05d2-electromechanical-notes.png`. No PDF runtime/layout changes were required.

The user continues work in the ordinary active session without a Scheduled-task prerequisite and manages Windows availability through installed PowerToys/Awake. Broader amended coverage and final retrospective remain open.
