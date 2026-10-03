# 02b11-aliens-unlimited-alien-generation-rules: Implement rule from Aliens Unlimited: Alien Character Creation, Expanded Alien Character Generation, Optional Alien Generation Tables

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-hu2-aliens`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-alien-character-creation` | Alien Character Creation / `rule` | — | 8, 191 / 9, 192 | `6af1f91c87b4dc1d20d9`, `f8ad2c077b1490d146ee` | Original body profile and printed footer confirm the identity. Attributes, powers, education, resources, equipment, advancement, edition reconciliation and complete dependencies remain pending.; Original introduction states 84 specific races, but the original alphabetical race index at printed 191 / PDF 192 enumerates 85 primary body profiles. The index candidate is retained here as count evidence, not another creation mode. Atorians is a separate indexed profile; no confirmed counting convention permits excluding it. |
| `au-expanded-alien-generation` | Expanded Alien Character Generation / `rule` | — | 12 / 13 | `5789c226f9befed2847e` | Original body profile and printed footer confirm the identity. Attributes, powers, education, resources, equipment, advancement, edition reconciliation and complete dependencies remain pending. |
| `au-optional-alien-generation` | Optional Alien Generation Tables / `rule` | — | 18, 19 / 19, 20 | `2af9a6a0f26a2f490363`, `a80ddf9176c5b82b549f`, `83d4d40e813f41e95593`, `ef0271896bca9890ac66` | Original printed 18 / PDF 19 establishes a distinct quick racial generation procedure replacing most standard steps. It allows exceptional attribute bonuses on results 16-18 and none on 19 or higher, including pools greater than 3D6. All formulas, random tables, manual selection, resources, powers, education and edition reconciliation remain pending.; Original optional Tables A/B (printed 18-19 / PDF 19-20) contain 84 rows, omit indexed Atorians and list Mantis where the indexed/body profile is Manteze. This is an unresolved roster discrepancy, not a confirmed Mantis alias or permission to remove Atorians. Original Table A Photin roll range is 77-79; Markdown 77479 is an OCR error. Numerical table ingestion must reconcile the original. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
