# 02b11-aliens-unlimited-humanoid-races-01: Implement option family, race from Aliens Unlimited: Aluta, Arerri, Arismal and 7 more

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-hu2-aliens`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-aluta` | Aluta / `race` | — | 98 / 99 | `da8e81bae9562ebc98d0` | Original body heading and printed footer confirm the identity. Aluta. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending.; Humanoid section/body starts at printed 98 / PDF 99; alphabetical-list section locator 86 conflicts with original body and needs reconciliation. |
| `au-arerri` | Arerri / `race` | — | 99 / 100 | `f787f466af8dddb00d3a` | Original body heading and printed footer confirm the identity. Arerri. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-arismal` | Arismal / `race` | — | 100 / 101 | `4f7bab2470a3e6019cca` | Original body heading and printed footer confirm the identity. Arismal. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-atorians` | Atorians / `race` | Fehrans | 102 / 103 | `5b14c11dd061bdf697e4`, `992f8308a1e9f3ee02e7` | Original body heading and printed footer confirm the identity. Atorians; Fehrans alias in “a.k.a. Fehrans”. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-darakan` | Darakan / `race` | Darkan | 103 / 104 | `dc627012fed137f64111` | Original body heading and printed footer confirm the identity. Body spells Darakan; contents index lists “Darkan”. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending.; Original body spelling Darakan controls the identity; index Darkan is retained for source lookup, not silent normalization. |
| `au-hatha` | Hatha / `race` | — | 103 / 104 | `fb7ba65164ba275df303` | Original body heading and printed footer confirm the identity. Hatha; cave/surface variants below. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-hatha-cave-dweller` | Hatha: Cave Dweller / `option-family` | — | 104 / 105 | `fb7ba65164ba275df303` | Original body heading and printed footer confirm the identity. Explicit separate attributes/abilities under Hatha. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-hatha-surface-dweller` | Hatha: Surface Dweller / `option-family` | — | 104 / 105 | `fb7ba65164ba275df303` | Original body heading and printed footer confirm the identity. Explicit separate attributes/abilities under Hatha. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-kassans` | Kassans / `race` | — | 105 / 106 | `d911e4122e3c8cdf37ae` | Original body heading and printed footer confirm the identity. Kassans. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-klikita` | Klikita / `race` | — | 106 / 107 | `dfac79a0a4336cb6b789` | Original body heading and printed footer confirm the identity. Klikita; distinct race sharing Rizza with Aluta. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
