# 22B2B: Shared option selectors

**Status:** in-progress. **Base:**04df5b68ce951d6fce3e2fa76142cf8d7d69b01a (merged22B2A/PR91).

Implement a strict non-executable selector over a pinned game-specific catalog. Include clauses combine referenced identities, categories and semantic tags; exclusions apply after inclusion. Reference matching is exact. Unknown/malformed selector fields reject as rule data, never silently expand to all options. Preserve unresolved dependency reporting rather than pretending absent abilities exist.

First integrations: Heroes program choice groups may compile a reviewed selector into existing explicit option identities; Minor power-category accounting uses the same selector; existing effect tag targeting may reuse this engine where its source contracts remain compatible. Preserve legacy explicit-ID group definitions and pins unchanged. Class/race names never control selector execution.

Verify selectable/granted identities, weighted credit, excluded/tagged choices, malformed syntax/reference atomic rejection, backtracking and portable reopening through agreed CharacterApplication/portable seams. Synthetic selector fixtures are mechanics-contract tests, not new accepted book rules. Full fixed-grant composition follows22B2C; typed effects/resources/importer remain dependency-ordered.
