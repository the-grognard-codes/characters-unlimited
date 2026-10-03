# 02b11-aliens-unlimited-canine-races: Implement option family, race from Aliens Unlimited: Canis, Dergins, Wardions and 5 more

**Status:** ready-for-agent.

**Book:** `aliens-unlimited`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `44b4ebf5c9f1741b8e00dc8c36d4008f67f2cbd2378ed1e9fc7e55c6746e9c6f`, original PDF `7522ed23a47cfd6b7add90036d0fe1298837fd26560319f0d73458ad33f36702`.

**Blocked by:** `02`, `12`, `15`, `19`, `21`, `02b11-hu2-aliens`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `au-canis` | Canis / `race` | — | 80 / 81 | `bd3b0fbf80c61cbd0408` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |
| `au-dergins` | Dergins / `race` | — | 82 / 83 | `f56376f97729d55ffb43` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |
| `au-wardions` | Wardions / `option-family` | — | 83 / 84 | `21b67b4c94bcbe85ca81` | Original body heading and printed footer confirm this named warrior-class branch of dergins. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending.; Named warrior-class branch inside the Dergins profile, not an independently headed species; shares Dergin traits. Its distinct occupation rules need review. |
| `au-latran` | Latran / `race` | — | 84 / 85 | `baa116508e9fede1ad38` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |
| `au-lupis` | Lupis / `race` | — | 85 / 86 | `15c333c1887f748a81ca` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |
| `au-toyoc` | Toyoc / `race` | — | 86 / 87 | `e38229f9f882fcd1ee58` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |
| `au-vulpese` | Vulpese / `race` | — | 87 / 88 | `e58fb3e8bf83f039a29f` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |
| `au-wulf` | Wulf / `race` | — | 88 / 89 | `fe10e5103cdf65c27722` | Original body heading and printed footer confirm this canine race. Complete attributes, abilities, education, class compatibility, advancement, equipment, edition reconciliation and mechanical dependencies remain pending. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
