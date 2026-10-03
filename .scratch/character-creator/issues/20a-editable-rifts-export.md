# 20A: Editable Rifts export for supported values

**Status:** done

**Dependencies:** Current Rifts application/portable-rule contracts. Parent 20 remains open for equipment, resources, magic, additional attack projection and full release acceptance.

Export a currently supported Human/Vagabond through the local UI after a nonblocking unfinished-parts checklist. Preserve the supplied Rifts sheet artwork and blank missing values; do not stamp it as a draft. Populate identity, attributes, level, reviewed skills, representative combat and notes. Overflow skill checks and long notes onto editable continuation pages that use the reference's monochrome lines and serif headings.

The supplied reference shares unrelated fields and appearance streams. Normalize each widget into its own canonical editable field without altering the artwork. Validate canonical values, widget values, unique appearance streams, actual edit/save/reopen behavior and short/long rendering. Download must preserve the saved character and use one consistent character snapshot. Keep original reference files unchanged.

Validate through CharacterApplication, the PDF artifact seam, the HTTP adapter and browser download; complete both reviews and Windows CI before merge. Tailored Heroes Unlimited export and all parent-20 dependent mechanics remain separate work.

Merged in PR #19. The remaining browser-delivery check passed during 23A: the frozen app created a character in Edge, downloaded a real PDF to Downloads, and its name, pages and canonical fields reopened correctly. Parent 20 stays open for its remaining mechanics.
