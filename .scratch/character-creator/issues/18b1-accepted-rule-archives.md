# 18B1: Resolve accepted rules by immutable version

**Status:** in-progress

**Blocked by:** 18A

Independent foundation of 18B. Preserve accepted definitions by `(pack ID, version)` with canonical-content hashes and separate active versions. Reopen, reroll, select skills, duplicate, and portable import/export using exact saved pins; changing the active version must not move a saved character onto it. Reject missing accepted versions, altered files, duplicate identities, and manifest paths outside the pack directory. Return independent definition copies so callers cannot mutate the archive.

Application tests exercise archived fixtures alongside the active definitions and verify prior projections, source explanations, and portable definitions. Production includes only the two reviewed version-1.0.0 packs. Fixture versions demonstrate resolution without publishing fictional rules or a correction. This does not activate arbitrary books, implement rule upgrades, or close the both-game parent 18B.
