# 02b11-aliens-unlimited-galactic-dopplegangers: Implement option family, race from Aliens Unlimited: Dop-Elpoep, Dopplegangers, Reipoc and 1 more

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-au-galactic-monster-player-guidance`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-dop-elpoep` | Dop-Elpoep / `race` | Dop-elpoeps | 152 / 153 | `8b0526f45c4821c64b8a`, `18b9caddebbc4432cd08` | Doppleganger race; NPC/antagonist-facing. Pronunciation/stat heading “Dop-elpoeps” belongs to the same race.; Section source defaults to monster/NPC use unless an entry explicitly allows a player character. Cyklops-Serpentmen, Reipoc and Dragonoid have such options; player/NPC distinctions are source guidance, not an application access gate. Full mechanics, powers, magic, eligibility and edition dependencies remain pending. |
| `au-dopplegangers` | Dopplegangers / `option-family` | — | 152 / 153 | `5998568fbde19f884473` | Umbrella race family / transformation group; not a separate species option. Introduces the three doppleganger races below; keep it as a family heading.; Section source defaults to monster/NPC use unless an entry explicitly allows a player character. Cyklops-Serpentmen, Reipoc and Dragonoid have such options; player/NPC distinctions are source guidance, not an application access gate. Full mechanics, powers, magic, eligibility and edition dependencies remain pending. |
| `au-reipoc` | Reipoc / `race` | — | 153 / 154 | `cb88c6d4b78360940c30`, `71ca17dd26c49949662d`, `dee6a32a1b151fc6a9cb` | Doppleganger race; optional PC with source-stated GM approval. Explicit PC marker appears in a separate candidate between overview and stat profile.; Section source defaults to monster/NPC use unless an entry explicitly allows a player character. Cyklops-Serpentmen, Reipoc and Dragonoid have such options; player/NPC distinctions are source guidance, not an application access gate. Full mechanics, powers, magic, eligibility and edition dependencies remain pending. |
| `au-erishiks` | Erishiks / `race` | — | 154 / 155 | `eb470bdabd52153cd11d`, `48cc75dfc639bf974ff8` | Doppleganger race; monster/NPC-facing. Overview and stat heading describe one identity.; Section source defaults to monster/NPC use unless an entry explicitly allows a player character. Cyklops-Serpentmen, Reipoc and Dragonoid have such options; player/NPC distinctions are source guidance, not an application access gate. Full mechanics, powers, magic, eligibility and edition dependencies remain pending. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
