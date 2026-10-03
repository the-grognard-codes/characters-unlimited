# 07C — Rifts Vagabond resources and bonuses

## Source locators

| Rule | Candidate / corrected Markdown | Original locator |
|---|---|---|
| Vagabond O.C.C. bonuses | `4723d131c9eb5765a291`, lines 4548–4553 | printed 97 / PDF 100 |
| Vagabond O.C.C. skill/stat block | `53ee8e2436810fe4d848`, lines 4554–4627 | printed 97–98 / PDF 100–101 |
| Starting physical S.D.C. fallback | `a9fb249f780172d26ec3`, lines 16205–16214 | printed 287 / PDF 290 |
| Level-one Hit Points | `f55d7c74462262770772`, lines 16225–16232 | printed 287 / PDF 290 |

RUE source fingerprints: PDF SHA-256 `448715cb4301ca9cd0bc7333bda7e1f88a089f05f33b33f625736a7a96700b9c`; corrected Markdown SHA-256 `601c9483f5e1c6c01a828383f0cc1ae41008f94bf1799e9aad4fe0771de029b9`. Original scans visually checked at PDF pages 100, 101 and 290 (printed pages 97, 98, 287).

## Findings

At level one, the general HP rule is rolled-up P.E. plus 1D6. The Vagabond O.C.C. adds +2 P.E. and +2D6+10 S.D.C.; its O.C.C. text does not separately state a starting S.D.C. pool. The general S.D.C. rule supplies 2D6+12 when an O.C.C. gives no base, then adds O.C.C./R.C.C. and physical-skill bonuses cumulatively. Thus a human Vagabond’s sourced S.D.C. expression is 4D6+22 before physical-skill bonuses. Physical bonuses are acquired once: e.g. Athletics adds 1D8 S.D.C.; Body Building adds 10 S.D.C. (see `tmp/05b8-physical-source.md`).

O.C.C. bonuses also grant +4 Perception, +1 save vs possession and psionic attacks, and +2 save vs Horror Factor. These are fixed O.C.C. bonuses, with no level progression stated in this entry.

HP sequencing remains ambiguous in the source: the HP instructions refer to P.E. after attribute generation, while Vagabond’s +2 P.E. is an O.C.C. bonus. The source does not expressly resolve that order. On 2026-10-03 the user accepted effective P.E. at first HP generation, retaining the recorded starting contribution afterward. This adopted interpretation includes class/Physical/manual effects present at that step and does not recalculate HP on later attribute changes. The source does not establish a Human-specific S.D.C. modifier here; only the general fallback and reviewed class/Physical contributions apply.
