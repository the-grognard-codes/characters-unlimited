# 02b11-hu2-mega-hero: Implement rule from Heroes Unlimited - RPG - 2E: Mega-Hero

**Status:** ready-for-agent.

**Book:** `heroes-unlimited-rpg-2e`. Scope is restricted to the exact identities below. Source fingerprints: Markdown `02927f54f7ebfc544629092464cb7c3430daa84683ced4ebf8a3e0607af77282`, original PDF `5041e03b8132aa73161c3845af1248de07e853b63a31eab97b9210442d49a706`.

**Blocked by:** `02`, `03`, `07`, `09`, `19`, `21`. These are actual workflow, source-dependency, or verified source-recovery edges; unresolved rule prerequisites remain findings until reviewed.

## Exact identities and source evidence

| Canonical ID | Exact name / kind | Aliases | Printed pages / PDF pages | Candidate IDs | Findings to retain |
|---|---|---|---|---|---|
| `hu2-mega-hero` | Mega-Hero / `rule` | — | 20 / 21 | `b9958da629c9e6641335` | Identity confirmed against the original PDF; complete mechanics, restrictions, advancement, equipment and dependency audit remain pending.; Optional personality and power modifier with category-specific applicability; it is not a separate roll on the ten-category table. |

## Acceptance

- Verify every listed identity and alias against its exact fingerprinted corrected Markdown candidates and original PDF pages; record heading, offset, precedence, variant and source-gap evidence without copying book prose.
- Review each identity’s mechanics, selection inputs, mandatory prerequisites, conditional/optional/NPC guidance and actual shared rules. Distinguish source cross-references from required character choices; do not add GM-only access gates.
- Independently calculate representative expected values and edge cases for every listed identity, including relevant attributes, resources, skills, power/spell/psionic effects, combat and costs. Any unresolved source/mechanical dependency stays explicit; implement no inferred fallback.
- Add public workflow tests for every named path covering selection/revisioned save/reopen and portable import/export with exact pins. Exercise advancement and applicable combat/resource projections.
- Verify source explanations and applicable editable Rifts/Heroes PDF fields with rendered evidence. Preserve game separation and saved compatibility; exercise the public workflow, not a helper-only unit path.
- Keep ticket ownership stable. Advance identity/mechanical/dependency review or automation state only when its own evidence and acceptance checks are complete; ticket assignment does not certify review or automation.

**Dependency contract:** the manifest mirrors canonical `dependencies` to owning tickets, plus actual parent workflow and verified source-recovery prerequisites. Other dependencies remain pending and must not be silently treated as resolved.
