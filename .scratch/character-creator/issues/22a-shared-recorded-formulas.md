# 22A: Shared recorded formula framework

**Parent:** 22/04/06/09/10/11/12. **Status:** done.
**Base:** 96a6a9dc34ba03f3c5519068db3be38220e406a1.

User steering: prioritize reusable mechanics and review declarative class/race imports; do not implement a bespoke engine for each option.

First framework increment: consolidate ordinary recorded bonus formulas for classes, Physical skills and super abilities behind one implementation. Reject malformed or unknown formula operations before saving. Preserve legacy pack bytes, receipt shapes, retained dice, manual values and attribute-generation house rules. Document the framework audit, class/race import contract and dependency-ordered next increments. This does not claim magic, psionics, or a complete importer are implemented.

Acceptance through the previously agreed CharacterApplication and portable-character seams: independently worked examples across games and effect families; atomic rejection of invalid formula data/dice; remove/reselect/import retain rolls; existing progression and PDF flows remain unchanged. Run affected checks, required type/syntax checks, full suite and packaged Windows checks; independent Standards/Spec review; scoped commit, PR and merge.

PR89 merged as118d15d7a105f385eae6fcf97c5f75ec02c9da45. Both exact-head Windows37226460205/37226434948 passed, including frozen executable checks. Final378 local tests, mypy120, compilation/JS/whitespace pass; both independent reviews approve.
