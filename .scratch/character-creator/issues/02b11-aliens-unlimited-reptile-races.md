# 02b11-aliens-unlimited-reptile-races: Implement option family, race from Aliens Unlimited: Aurovax, Baccarus, Erittima and 5 more

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-hu2-aliens`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-aurovax` | Aurovax / `race` | — | 132 / 133 | `3d77921b9e940bf2b3e2` | Original body profile and printed footer confirm the identity. Printed p.132 begins “Reptile Races” and the Aurovax entry; shares alien-generation and reptile section context. All numerical and edition-dependent rules remain pending. |
| `au-baccarus` | Baccarus / `race` | — | 133 / 134 | `a27c517f1a46d8fbe3ee` | Original body profile and printed footer confirm the identity. Alphabetical list OCR truncates page as “13”; rendered page sequence and +1 offset resolve it to printed 133. All numerical and edition-dependent rules remain pending. |
| `au-erittima` | Erittima / `race` | Erittimas | 134 / 135 | `e2015ef278a9c1d672a5` | Original body profile and printed footer confirm the identity. First race heading is singular “Erittima”; its stat heading at MD line 6073 is plural “Erittimas.” All numerical and edition-dependent rules remain pending. |
| `au-jenjorans` | Jenjorans / `race` | — | 135 / 136 | `59c952cfcc3e04d0dec3` | Original body profile and printed footer confirm the identity. Entry contains a named anti-magic warrior role and associated bonuses (MD line 6143); no separate heading/candidate is shown, so treat as an embedded branch. All numerical and edition-dependent rules remain pending. |
| `au-jenjoran-anti-magic-warrior` | Jenjoran Anti-Magic Warrior / `option-family` | — | 136 / 137 | `59c952cfcc3e04d0dec3` | Original printed 136 / PDF 137 explicitly grants trained anti-magic warriors additional bonuses, a recognition skill, psionic protection and distinct PPE. Embedded named training branch, not another race; full mechanics remain pending. |
| `au-nithians` | Nithians / `race` | — | 136 / 137 | `433d88317c88b1ccd3ef` | Original body profile and printed footer confirm the identity. Species entry has its own selectable power-category proportions; common alien-generation context applies. All numerical and edition-dependent rules remain pending. |
| `au-qua-trau` | Qua-Trau / `race` | — | 137 / 138 | `40910fa29d50c32bdc9f` | Original body profile and printed footer confirm the identity. Species entry includes alternative bionic/robot/hardware-style power paths; common alien-generation context applies. All numerical and edition-dependent rules remain pending. |
| `au-thisseras` | Thisseras / `race` | — | 138 / 139 | `f1378b0da2e5d3e77c65` | Original body profile and printed footer confirm the identity. Distinct from Thissera-Micean Cooperative (organization, not a race); shared TMC cross-reference with Miceans. All numerical and edition-dependent rules remain pending. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
