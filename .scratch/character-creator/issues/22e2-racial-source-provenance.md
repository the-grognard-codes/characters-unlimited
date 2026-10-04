# 22E2: Racial generation source composition

**Status:** done. **Base:**dfa6706f6c2b8150d8f340547ad96ea3b1e91251 (merged22E1/PR96; review basefc68c770 has the identical tree).

Resolve generation citations from a race default source, optional per-attribute source overrides, and legacy core fallback. Validate all declared source identities before dice. Generation/reroll/current/history/resource snapshot/portable reopening must retain exact pinned source evidence; source tampering must reject. Legacy source records remain unchanged. Core generation stays on its immutable saved version; this does not implement core correction migration, R.C.C. precedence, full importer or accept new book content.

Merged PR97: c074870950295374f7831e12ebaf3dd8d4538e66. Both exact-head Windows and frozen checks passed.
