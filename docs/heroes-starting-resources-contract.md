# 09C: Human Mutant starting resources

Generate starting Hit Points, physical S.D.C. and P.P.E. through the existing retained resource record. This covers the currently selectable Human Mutant path. Other categories, training/power additions, money, vehicles, equipment and Heroes advancement remain open.

| Resource | Reviewed rule | Source |
| --- | --- | --- |
| Hit Points | Effective P.E. at first generation + one raw D6; retain both contributions | General HP, printed 17 / PDF 18; Mutant Step One, printed 158 / PDF 159 |
| Physical S.D.C. | Mutant base 30 | Mutant resources, printed 162 / PDF 163 |
| P.P.E. | General superbeing 6D6; no Mutant exception stated | Printed 20 / PDF 21 |

The user previously chose effective P.E. at first HP generation for Rifts. Apply the same recorded starting-contribution interpretation here: HU gives no different formula and does not settle later P.E. changes. This is an implementation judgment, not a claim that HU explicitly specifies adjusted-attribute timing. Later P.E. edits or rerolls never rewrite starting HP. Explicit HP bonuses and level-up dice require their own later reviewed rules.

Source candidates: HP `51d3869aefc172d06711` (Markdown 899–905), Mutant Step One `cf4862defb63c88163bb` (8578–8581), Mutant resources `a55d4b286d0833d6578c` (8804–8806), P.P.E. `7c200ea5fcdc013cfe49` (1056). Corrected Markdown and rendered originals were inspected. An initial source packet incorrectly placed Step One on printed 161; the original verifies printed 158 and the new pack uses that corrected locator.

Use independent `heroes-resources` 1.0.0 pins and the existing resource generator, validation, manual edits and projection. Record one D6 and six P.P.E. D6s once; attribute reroll/drop options never affect them. No dice are consumed by projection, manual edits, restart or portable import. Old characters with no resources may generate these rules; generated characters retain their exact pack. Incomplete PDF exports keep ungenerated resource fields blank. Generated fields, contribution dice and sources use the same character snapshot.

Validate through the approved CharacterApplication, persistence/portable, HTTP and editable-PDF seams. Worked example: P.E. 16 and D6 4 give HP 20, S.D.C. 30, six D6 faces 4 give P.P.E. 24. A later P.E. 25 leaves HP 20. At P.E. 12 with raw dice all 1, HP is 13 and P.P.E. 6 despite both attribute options being enabled. Fixed totals and additive adjustments retain original contributions. Reject invalid dice, stale saves, absent pins, altered sources and forged snapshot power modifiers without changing saved work.

Expose the existing resource panel for Human Mutants with independent loading state and navigation guards. Keep Rifts workflows working. Include editable HP/S.D.C./P.P.E. and source continuations in the tailored Heroes sheet. Exercise all of this in the packaged Windows workflow. Parent09 and full corpus acceptance remain open.
