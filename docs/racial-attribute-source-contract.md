# Racial attribute source contract

Attribute generation resolves evidence independently for each of the eight attributes. A race may declare `source` as its default book citation and `attribute_sources` as a map keyed by canonical attribute names. An attribute override replaces the entire citation; otherwise the race default applies, falling back to the pinned core pack source for legacy definitions.

Every declared citation requires nonempty string `book` and `section` values. Additional citation metadata, such as page references, is retained exactly. Unknown attribute keys, malformed maps and malformed default or override citations reject before any initial dice. This validates citation identity, not the accuracy of book evidence or the full import schema.

Initial generation and rerolls use the same resolver. Each attribute receives its own copied citation. Current records, every roll-history frame and starting-resource attribute snapshots must match the exact source resolved from the saved core version during portable import. Editing a source record cannot silently replace its evidence. Existing definitions with no racial citations keep their existing core source records.

Core generation definitions remain pinned to their original versions; the existing correction preview does not migrate core attributes or racial sources. This increment does not add core migrations, R.C.C. replacement precedence, new accepted races, full importer certification or callbacks specific to a race.
