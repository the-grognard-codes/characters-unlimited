# 02b11-aliens-unlimited-insect-races: Implement option family, race from Aliens Unlimited: Danaus, Lixilas, Manteze and 5 more

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-hu2-aliens`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-danaus` | Danaus / `race` | — | 116 / 117 | `a4da2006f325721ecf1a` | Original body heading and printed footer confirm the identity. “Danaus (Atorian Empire)”; polity affiliation, not ancestry. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending.; Atorian Empire association is political/military history, not racial ancestry. |
| `au-lixilas` | Lixilas / `race` | — | 117 / 118 | `3afb47e340548a8d6915` | Original body heading and printed footer confirm the identity. Lixilas. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-manteze` | Manteze / `race` | — | 118 / 119 | `85073d255ec146b9c56d` | Original body heading and printed footer confirm the identity. Manteze; Queen Mother is a ruling office, not another race. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending.; Queen Mother is a ruling office, not another race. |
| `au-photins` | Photins / `race` | — | 119 / 120 | `338685c7ce7612848788` | Original body heading and printed footer confirm the identity. Photins; former Atorian shock troops, not an Atorian variant. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending.; Atorian Empire association is political/military history, not racial ancestry. |
| `au-pyralis` | Pyralis / `race` | — | 120 / 121 | `6864a432a3a827a02873` | Original body heading and printed footer confirm the identity. Pyralis. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-relogians` | Relogians / `race` | — | 121 / 122 | `f09f4fd000ac7935dfb8` | Original body heading and printed footer confirm the identity. Relogians. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-xippus` | Xippus / `race` | — | 122 / 123 | `94da45e0558dcf01e790` | Original body heading and printed footer confirm the identity. Xippus; Queen caste below. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |
| `au-xippus-queen` | Xippus: Queen / `option-family` | — | 122 / 123 | `94da45e0558dcf01e790` | Original body heading and printed footer confirm the identity. Distinct caste with specified powers, ISP, age and horror factor. All numerical rules, restrictions, advancement, equipment and complete dependencies remain pending. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
